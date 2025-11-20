"""
Workflow Executor - Environment-aware execution engine

Executes workflows with environment-specific configuration (experiment vs hosted).
"""

import importlib.util
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from langfuse import observe, propagate_attributes
from lgp.observability import (
    configure_langfuse,
    flush_traces,
    sanitize_for_dashboard
)
from lgp.observability.tracers import LangfuseTracer
from lgp.checkpointing import create_checkpointer
from lgp.config import load_config
from lgp.claude_code.node_factory import create_claude_code_node
from lgp.claude_code.session_manager import get_default_manager
from lgp.agents.factory import create_agent_node


class WorkflowExecutor:
    """Executes workflows with environment-specific configuration"""

    def __init__(self, environment: str = "experiment", verbose: bool = False):
        self.environment = environment
        self.verbose = verbose
        self.config = self._load_config(environment)

        # Configure Langfuse if enabled
        if self.config.get("observability", {}).get("langfuse", False):
            configure_langfuse(enabled=True)
        else:
            configure_langfuse(enabled=False)

    def _load_config(self, environment: str) -> Dict[str, Any]:
        """
        Load environment-specific configuration from YAML files.

        Loads from config/experiment.yaml or config/hosted.yaml with:
        - Environment variable substitution
        - Validation
        - Merge with .env secrets

        Args:
            environment: Environment name (experiment/hosted)

        Returns:
            Dictionary with configuration

        Raises:
            ValueError: If environment is invalid or config is malformed
            FileNotFoundError: If config file doesn't exist
        """
        try:
            config = load_config(environment)
            return config
        except FileNotFoundError as e:
            # Fallback to hardcoded config if YAML files don't exist
            # This maintains backward compatibility
            print(f"[lgp] Warning: {e}")
            print(f"[lgp] Using hardcoded configuration (legacy mode)")
            return self._legacy_config(environment)
        except Exception as e:
            raise ValueError(f"Failed to load config for {environment}: {e}")

    def _legacy_config(self, environment: str) -> Dict[str, Any]:
        """Legacy hardcoded configuration (backward compatibility)"""
        if environment == "experiment":
            return {
                "checkpointer": {
                    "type": "sqlite",
                    "path": "./checkpoints.db",
                    "async": True
                },
                "observability": {
                    "console": True,
                    "langfuse": False
                },
                "runtime": {
                    "hot_reload": True
                }
            }
        elif environment == "hosted":
            return {
                "checkpointer": {
                    "type": "postgresql",
                    "url": None,
                    "pool_size": 10
                },
                "observability": {
                    "console": False,
                    "langfuse": True
                },
                "server": {
                    "workers": 4
                },
                "auth": {
                    "api_key": None
                }
            }
        else:
            raise ValueError(f"Unknown environment: {environment}")

    def _load_workflow_module(self, workflow_path: str):
        """Load workflow Python module"""
        path = Path(workflow_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")

        # Load module from file
        spec = importlib.util.spec_from_file_location("workflow", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load workflow from: {workflow_path}")

        module = importlib.util.module_from_spec(spec)

        # Add workflow directory to path for relative imports
        sys.path.insert(0, str(path.parent))

        try:
            spec.loader.exec_module(module)
        finally:
            # Remove from path
            sys.path.remove(str(path.parent))

        return module

    def _extract_workflow(self, module):
        """Extract compiled workflow from module"""
        # Look for 'workflow' or 'app' attribute
        if hasattr(module, 'workflow'):
            return module.workflow
        elif hasattr(module, 'app'):
            return module.app
        elif hasattr(module, 'create_workflow'):
            # Call factory function
            return module.create_workflow()
        else:
            raise AttributeError(
                "Workflow module must export 'workflow', 'app', or 'create_workflow()'"
            )

    async def _inject_claude_code_nodes(self, workflow, module):
        """
        Inject LLM agent nodes into workflow (multi-provider support).

        Reads claude_code_config from the workflow module and dynamically creates
        agent nodes for the specified provider (Ollama, Claude Code, etc.).

        R8 Multi-Provider Support:
        - Dispatches to correct provider based on agent config
        - Supports: "ollama" (self-hosted, $0), "claude_code" (cloud, $$)
        - Future: GPT, Claude API, LM Studio, etc.

        Args:
            workflow: StateGraph builder (uncompiled)
            module: Workflow module (may contain claude_code_config)

        Returns:
            Workflow with agent nodes injected (still uncompiled)
        """
        # Check if module has claude_code_config
        if not hasattr(module, 'claude_code_config'):
            if self.verbose:
                print("[lgp] No claude_code_config found, skipping agent injection")
            return workflow

        config = module.claude_code_config

        # Check if enabled
        if not config.get("enabled", False):
            if self.verbose:
                print("[lgp] Agent injection disabled in config")
            return workflow

        agents = config.get("agents", [])
        if not agents:
            if self.verbose:
                print("[lgp] No agents configured in claude_code_config")
            return workflow

        if self.verbose:
            print(f"[lgp] Injecting {len(agents)} agent nodes...")

        # Get LLM provider configurations from environment config
        llm_providers = self.config.get("llm_providers", {})

        # Inject each agent
        for agent_config in agents:
            role_name = agent_config.get("role_name")
            inject_after = agent_config.get("inject_after")
            inject_before = agent_config.get("inject_before")
            provider = agent_config.get("provider", "claude_code")  # Default to Claude Code for backward compat

            if not all([role_name, inject_after]):
                print(f"[lgp] Warning: Incomplete agent config, skipping: {agent_config}")
                continue

            # Get provider-specific configuration
            provider_config = llm_providers.get(provider, {})
            if not provider_config:
                print(f"[lgp] Warning: No config for provider '{provider}', using defaults")
                provider_config = {"enabled": True}

            # Create agent node using factory (dispatches to correct provider)
            node_name = f"{role_name}_agent"
            try:
                agent_node = create_agent_node(
                    provider_type=provider,
                    config=agent_config,
                    provider_config=provider_config
                )

                # Add node to graph
                workflow.add_node(node_name, agent_node)

                # Add edges: inject_after → agent → inject_before
                workflow.add_edge(inject_after, node_name)

                if inject_before:
                    workflow.add_edge(node_name, inject_before)

                if self.verbose:
                    provider_label = f"{provider}"
                    if provider == "ollama":
                        model = agent_config.get("model", provider_config.get("default_model", "llama3.2"))
                        provider_label = f"ollama:{model}"
                    print(f"[lgp]   ✅ Injected {node_name} ({provider_label}) ({inject_after} → {node_name} → {inject_before or 'END'})")

            except ValueError as e:
                print(f"[lgp] ❌ Failed to create {node_name}: {e}")
                continue

        return workflow

    def execute(self, workflow_path: str, input_data: Optional[Dict[str, Any]] = None):
        """Execute workflow (synchronous entry point)"""
        if input_data is None:
            input_data = {"input": "test"}

        # Check if workflow is async
        try:
            return asyncio.run(self.aexecute(workflow_path, input_data))
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                # Already in async context
                return asyncio.create_task(self.aexecute(workflow_path, input_data))
            raise

    async def aexecute(self, workflow_path: str, input_data: Optional[Dict[str, Any]] = None):
        """Execute workflow (async)"""
        if input_data is None:
            input_data = {"input": "test"}

        if self.verbose:
            print(f"[lgp] Executing workflow...")

        start_time = time.time()
        workflow_name = Path(workflow_path).stem
        checkpointer_cm = None

        try:
            # Load workflow module
            module = self._load_workflow_module(workflow_path)

            if self.verbose:
                print(f"[lgp] Module loaded: {module.__name__}")

            # Extract workflow (builder or compiled graph)
            workflow = self._extract_workflow(module)

            if self.verbose:
                print(f"[lgp] Workflow extracted")

            # Inject Claude Code nodes if configured
            workflow = await self._inject_claude_code_nodes(workflow, module)

            # Inject checkpointer based on config
            if self.config.get("checkpointer"):
                checkpointer_cm = create_checkpointer(self.config["checkpointer"])

                # Enter async context manager to get actual checkpointer
                checkpointer = await checkpointer_cm.__aenter__()

                # If workflow is a builder (has compile method), compile with checkpointer
                if hasattr(workflow, 'compile'):
                    if self.verbose:
                        print(f"[lgp] Compiling workflow with checkpointer")
                    workflow = workflow.compile(checkpointer=checkpointer)
                elif self.verbose:
                    print(f"[lgp] Workflow already compiled, checkpointer will be passed in config")
            else:
                checkpointer = None

            # Build execution config with thread_id for state persistence
            thread_id = input_data.get("thread_id", "default")
            execution_config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }

            if self.verbose:
                print(f"[lgp] Using thread_id: {thread_id}")

            # Prepare metadata and tags for Langfuse
            metadata = LangfuseTracer.get_metadata(
                workflow_name=workflow_name,
                environment=self.environment,
                workflow_path=workflow_path
            )
            tags = LangfuseTracer.get_tags(
                workflow_name=workflow_name,
                environment=self.environment
            )

            # Execute workflow with Langfuse tracing
            if self.verbose:
                print(f"[lgp] Invoking workflow...")

            if LangfuseTracer.is_enabled():
                # Wrap execution in Langfuse trace
                with propagate_attributes(metadata=metadata, tags=tags):
                    result = await self._execute_with_trace(
                        workflow,
                        input_data,
                        workflow_name,
                        execution_config
                    )
            else:
                # Execute without tracing
                result = await workflow.ainvoke(input_data, config=execution_config)

            elapsed = time.time() - start_time

            # Sanitize result for dashboard
            if LangfuseTracer.is_enabled():
                sanitized_result, sanitization_metadata = sanitize_for_dashboard(result)
                if sanitization_metadata:
                    if self.verbose:
                        print(f"[lgp] Output sanitized: {sanitization_metadata}")
            else:
                sanitized_result = result

            if self.verbose:
                print(f"[lgp] Execution complete")
                print(f"[lgp] Result: {sanitized_result}")

            print(f"[lgp] ✅ Complete ({elapsed:.1f}s)")

            # Flush traces to Langfuse
            if LangfuseTracer.is_enabled():
                flush_traces()

            print()

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[lgp] ❌ Error ({elapsed:.1f}s)")
            print(f"[lgp] {type(e).__name__}: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()

            # Flush traces even on error
            if LangfuseTracer.is_enabled():
                flush_traces()

            raise

        finally:
            # Clean up checkpointer context manager
            if checkpointer_cm is not None:
                try:
                    await checkpointer_cm.__aexit__(None, None, None)
                except Exception:
                    pass  # Ignore cleanup errors

    @observe(name="workflow_execution")
    async def _execute_with_trace(
        self,
        workflow,
        input_data: Dict[str, Any],
        workflow_name: str,
        config: Dict[str, Any]
    ):
        """
        Execute workflow with Langfuse trace decoration.

        Current limitation: Creates a single trace for the entire workflow execution.
        Individual node executions are not yet broken out into separate spans.

        To get node-level observability, decorate your workflow nodes with @observe:
            @observe(name="my_node")
            async def my_node(state):
                ...
        """
        return await workflow.ainvoke(input_data, config=config)
