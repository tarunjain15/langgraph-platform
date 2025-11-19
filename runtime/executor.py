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


class WorkflowExecutor:
    """Executes workflows with environment-specific configuration"""

    def __init__(self, environment: str = "experiment", verbose: bool = False):
        self.environment = environment
        self.verbose = verbose
        self.config = self._load_config(environment)

    def _load_config(self, environment: str) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        # TODO: Load from config/experiment.yaml or config/hosted.yaml
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
                "hot_reload": True
            }
        elif environment == "hosted":
            return {
                "checkpointer": {
                    "type": "postgresql",
                    "url": None,  # Will be from env var
                    "pool_size": 10
                },
                "observability": {
                    "console": False,
                    "langfuse": True
                },
                "workers": 4,
                "auth": {
                    "api_key": None  # Will be from env var
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

        try:
            # Load workflow module
            module = self._load_workflow_module(workflow_path)

            if self.verbose:
                print(f"[lgp] Module loaded: {module.__name__}")

            # Extract workflow
            workflow = self._extract_workflow(module)

            if self.verbose:
                print(f"[lgp] Workflow extracted")

            # TODO: Inject checkpointer based on config
            # TODO: Inject tracer based on config

            # Execute workflow
            if self.verbose:
                print(f"[lgp] Invoking workflow...")

            result = await workflow.ainvoke(input_data)

            elapsed = time.time() - start_time

            if self.verbose:
                print(f"[lgp] Execution complete")
                print(f"[lgp] Result: {result}")

            print(f"[lgp] ✅ Complete ({elapsed:.1f}s)")
            print()

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[lgp] ❌ Error ({elapsed:.1f}s)")
            print(f"[lgp] {type(e).__name__}: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            raise
