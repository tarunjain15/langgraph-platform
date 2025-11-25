```yaml
name: Complete Worker - Implementation Plan
description: Execution map for R13 (Worker Marketplace). Four phases building configuration layer on top of R11 execution layer.
created: 2025-11-25
version: 1.0.0
phase: R13
status: Roadmap (0% complete)
```

# Complete Worker: Implementation Plan

## Execution Status

**🔮 R13 Roadmap** - Worker Marketplace (75% complete, 4 phases)
**✅ R13.0 Complete** - Parallel agent execution blocker resolved
**✅ R13.1 Complete** - Worker Definition Schema
**✅ R13.2 Complete** - Worker Factory
**✅ R13.3 Complete** - Journey Isolation (Runtime)
**✅ R11 Complete** - Worker execution layer (foundation)
**📍 Next** - R13.4 (Constraint Enforcement Platform)

---

## Immediate Blocker: Fix Parallel Agent Execution

**Status:** 🚨 BLOCKING R13

**Error:**
```
InvalidUpdateError: At key 'current_step': Can receive only one value per step.
```

**Root Cause:**
- Parallel preparation nodes (prepare_research, prepare_write, prepare_review) all update `current_step`
- `current_step` is LastValue channel (can only receive one update per step)
- Parallel updates violate LastValue semantics

**Fix:**
```python
# workflows/claude_code_test.py - Line 21
# CHANGE FROM:
current_step: str  # LastValue channel

# CHANGE TO:
current_step: Annotated[List[str], operator.add]  # Topic channel (accumulates)
```

**Why This Unblocks R13:**
- Proves platform can orchestrate multiple Claude Code workers in parallel
- Demonstrates R10 4-channel coordination scales to multi-worker scenarios
- Validates claude-mesh MCP pattern for worker isolation
- Creates foundation for worker marketplace (each worker = parallel agent)

**Task:** R13.0 (Fix Parallel Execution) - **MUST complete before R13.1**

---

## R13: Worker Marketplace (4 Phases)

### Phase Overview

```
R13.1: Worker Definition Schema (Configuration)
  ↓
R13.2: Worker Factory (Instantiation)
  ↓
R13.3: Journey Isolation (Runtime)
  ↓
R13.4: Constraint Enforcement Platform (Safety)
```

---

## R13.0: Fix Parallel Agent Execution ✅

**Task ID:** R13.0
**Type:** Bugfix
**Status:** Complete
**Blocks:** All R13 phases
**Actual Duration:** 45 minutes

### Witness
**Observable Truth:** 3 parallel agents execute successfully, all update current_step, no InvalidUpdateError ✅

### Acceptance Criteria
- [x] Change `current_step` from `str` to `Annotated[List[str], operator.add]`
- [x] All 3 preparation nodes execute in parallel
- [x] claude-mesh MCP calls succeed for all 3 agents
- [x] Workflow compiles without InvalidUpdateError
- [x] Validation test confirms parallel execution works

### Execution Steps
1. Read workflows/claude_code_test.py
2. Locate State definition (line ~21)
3. Change `current_step: str` to `current_step: Annotated[List[str], operator.add]`
4. Update nodes to append to list instead of setting string
5. Run: `echo '{"topic": "test"}' | python3 -m cli.main run workflows/claude_code_test.py`
6. Verify: No InvalidUpdateError, 3 agents executed

### Code Changes
```python
# Before
class State(TypedDict):
    topic: str
    current_step: str  # ❌ LastValue channel

# After
class State(TypedDict):
    topic: str
    current_step: Annotated[List[str], operator.add]  # ✅ Topic channel

# Nodes update pattern
# Before
return {"current_step": "prepare_research"}

# After
return {"current_step": ["prepare_research"]}  # Append to list
```

### Files Modified
- `lgp/claude_code/node_factory.py` (line 115: changed string to list)
- `scripts/test_claude_code_integration.py` (State schema: current_step as Topic channel)
- `workflows/claude_code_test.py` (Added current_step field to ClaudeCodeTestState)
- `test_r13_validation.py` (Created - standalone validation test)

### Completion Evidence

**Commits:**
- `591f860` - R13.0: Fix parallel agent execution blocker (InvalidUpdateError)
- `f748473` - R13.0 Complete: State schema fix and validation test

**Validation Result:**
```
======================================================================
✅ R13.0 VALIDATION SUCCESSFUL
======================================================================

VERIFIED:
  ✅ Workflow compiled with 3 parallel agents
  ✅ All agents updated current_step (Topic channel)
  ✅ No InvalidUpdateError on current_step
  ✅ Parallel execution works correctly
```

**Root Cause:** `node_factory.py` returned `current_step` as string, creating LastValue channel. Multiple parallel agents violated LastValue semantics.

**Fix:** Changed to Topic channel pattern:
- `node_factory.py`: Return `['current_step']` as list
- State schemas: Declare `current_step: Annotated[list[str], operator.add]`

---

## R13.1: Worker Definition Schema

**Task ID:** R13.1
**Type:** Foundation
**Status:** Complete ✅
**Dependencies:** R13.0 complete
**Estimated Duration:** 2 hours
**Actual Duration:** ~1.5 hours

### Witness
**Observable Truth:** Worker definition YAML validates successfully, loads into Python dataclass, rejects invalid definitions

**Validation Result:**
```
20 tests passed in 0.05s
✅ research_assistant_v1.yaml validates successfully
✅ Defense layers 1-4 all functional
✅ DEFINITION_DECLARATIVE_PURITY constraint enforced
```

### What This Unlocks
- First-class worker definitions (configuration as data)
- YAML-based worker specification (no code in definitions)
- Validation layer (catch errors at load time)

### Acceptance Criteria
- [x] `workers/definitions/schema.py` defines all dataclasses
- [x] `workers/definitions/loader.py` loads YAML → Python objects
- [x] `workers/definitions/validator.py` validates definitions
- [x] Example definition: `workers/definitions/examples/research_assistant_v1.yaml`
- [x] Tests: `workers/definitions/test_definitions.py` (validation coverage)

### Execution Steps

**Step 1: Define Schema (30 min)**
```python
# workers/definitions/schema.py
from dataclasses import dataclass
from typing import List, Dict, Any, Literal

@dataclass
class WorkerIdentity:
    name: str
    system_prompt: str
    onboarding_steps: List[str]

@dataclass
class WorkerConstraint:
    constraint_id: str
    witness: str  # Function name
    feedback: Literal["alert_dashboard", "log", "email"]
    value: Any = None

@dataclass
class WorkerRuntime:
    container: str = "claude-code:latest"
    workspace_template: str = "/home/claude/workspace/{user_journey_id}"
    tools: List[str] = None
    session_persistence: bool = True

@dataclass
class WorkerAudit:
    log_all_actions: bool = True
    execution_channel: str = "worker_executions"
    retention_days: int = 90

@dataclass
class WorkerDefinition:
    worker_id: str
    identity: WorkerIdentity
    constraints: List[WorkerConstraint]
    runtime: WorkerRuntime
    trust_level: Literal["supervised", "monitored", "autonomous"]
    audit: WorkerAudit
    tools: List[str]
```

**Step 2: Implement Loader (30 min)**
```python
# workers/definitions/loader.py
import yaml
from pathlib import Path
from workers.definitions.schema import WorkerDefinition, WorkerIdentity, ...

def load_worker_definition(definition_file: str) -> WorkerDefinition:
    """
    Load worker definition from YAML file

    Args:
        definition_file: Path to YAML file or worker_id

    Returns:
        WorkerDefinition instance

    Raises:
        ValidationError: If definition invalid
    """
    # Resolve path (support both full path and worker_id)
    if not definition_file.endswith('.yaml'):
        definition_file = f"workers/definitions/{definition_file}.yaml"

    with open(definition_file) as f:
        data = yaml.safe_load(f)  # ✅ safe_load (no code execution)

    # Parse into dataclasses
    return WorkerDefinition(
        worker_id=data['worker_id'],
        identity=WorkerIdentity(**data['identity']),
        constraints=[WorkerConstraint(**c) for c in data['constraints']],
        runtime=WorkerRuntime(**data['runtime']),
        trust_level=data['trust_level'],
        audit=WorkerAudit(**data['audit']),
        tools=data['tools']
    )
```

**Step 3: Implement Validator (30 min)**
```python
# workers/definitions/validator.py
from workers.definitions.schema import WorkerDefinition

class ValidationError(Exception):
    pass

def validate_definition(definition: WorkerDefinition):
    """
    Validate worker definition for constraint compliance

    Checks:
    - DEFINITION_DECLARATIVE_PURITY: No code in definition
    - Worker ID valid
    - Witness functions exist
    - Trust level valid
    """
    # Check worker_id format
    if not definition.worker_id.replace('_', '').isalnum():
        raise ValidationError(f"Invalid worker_id: {definition.worker_id}")

    # Check trust level
    valid_levels = ["supervised", "monitored", "autonomous"]
    if definition.trust_level not in valid_levels:
        raise ValidationError(f"Invalid trust_level: {definition.trust_level}")

    # Check witness functions registered
    from workers.enforcement.witness import WitnessRegistry
    for constraint in definition.constraints:
        if not WitnessRegistry.is_registered(constraint.witness):
            raise ValidationError(f"Witness function not registered: {constraint.witness}")

    # Check no code patterns in system_prompt
    forbidden = ["import ", "eval(", "exec(", "__", "lambda"]
    for pattern in forbidden:
        if pattern in definition.identity.system_prompt:
            raise ValidationError(f"Code pattern in system_prompt: {pattern}")
```

**Step 4: Create Example Definition (15 min)**
```yaml
# workers/definitions/examples/research_assistant_v1.yaml
worker_id: "research_assistant_v1"

identity:
  name: "Research Assistant"
  system_prompt: |
    You are a research assistant specializing in deep research and source verification.
    You help users find accurate information using web search and document analysis.
    Always cite sources and verify claims before presenting them.
  onboarding_steps:
    - "Connect to research database"
    - "Load user preferences and citation style"
    - "Review research ethics guidelines"

constraints:
  - constraint_id: "no_hallucinated_citations"
    witness: "verify_source_exists"
    feedback: "alert_dashboard"

  - constraint_id: "max_web_searches_per_hour"
    value: 50
    witness: "verify_search_count"
    feedback: "log"

  - constraint_id: "require_approval_for_paid_sources"
    witness: "verify_purchase_approval"
    feedback: "alert_dashboard"

runtime:
  container: "claude-code:latest"
  workspace_template: "/home/claude/workspace/{user_journey_id}"
  tools:
    - "web_search"
    - "browser"
    - "filesystem"
    - "document_parser"
  session_persistence: true

trust_level: "supervised"

audit:
  log_all_actions: true
  execution_channel: "research_executions"
  retention_days: 90

tools:
  - "web_search"
  - "browser"
  - "filesystem"
  - "document_parser"
```

**Step 5: Write Tests (15 min)**
```python
# workflows/test_worker_definitions.py
import pytest
from workers.definitions.loader import load_worker_definition
from workers.definitions.validator import validate_definition, ValidationError

def test_load_valid_definition():
    """Test loading valid worker definition"""
    definition = load_worker_definition("examples/research_assistant_v1.yaml")

    assert definition.worker_id == "research_assistant_v1"
    assert definition.identity.name == "Research Assistant"
    assert len(definition.constraints) == 3
    assert definition.trust_level == "supervised"

def test_reject_invalid_worker_id():
    """Test validation rejects invalid worker_id"""
    with pytest.raises(ValidationError, match="Invalid worker_id"):
        definition = load_worker_definition("invalid-worker-id.yaml")
        validate_definition(definition)

def test_reject_code_in_definition():
    """Test validation rejects code in system_prompt"""
    definition = WorkerDefinition(
        worker_id="malicious",
        identity=WorkerIdentity(
            name="Malicious",
            system_prompt="import os; os.system('rm -rf /')",  # ❌ Code
            onboarding_steps=[]
        ),
        # ... rest of definition
    )

    with pytest.raises(ValidationError, match="Code pattern"):
        validate_definition(definition)
```

### Files Created
- `workers/definitions/__init__.py`
- `workers/definitions/schema.py` (~100 lines)
- `workers/definitions/loader.py` (~80 lines)
- `workers/definitions/validator.py` (~60 lines)
- `workers/definitions/examples/research_assistant_v1.yaml` (~40 lines)
- `workflows/test_worker_definitions.py` (~100 lines)

### Completion Signal
```bash
# Load example definition
python3 -c "
from workers.definitions.loader import load_worker_definition
from workers.definitions.validator import validate_definition

definition = load_worker_definition('research_assistant_v1')
validate_definition(definition)
print(f'✅ {definition.worker_id} loaded and validated')
"
```

**Output:** `✅ research_assistant_v1 loaded and validated`

---

## R13.2: Worker Factory

**Task ID:** R13.2
**Type:** Integration
**Status:** Complete ✅
**Dependencies:** R13.1 complete
**Estimated Duration:** 3 hours
**Actual Duration:** ~2 hours

### Witness
**Observable Truth:** WorkerFactory.spawn() creates worker instance from definition, instance has isolated workspace, constraints loaded ✅

**Validation Result:**
```
14 tests passed in 0.05s
✅ R13.2 WITNESS SATISFIED
✅ WorkerFactory.spawn() creates worker instance from definition
✅ Worker instance has isolated workspace per journey
✅ Worker carries constraints loaded from definition
✅ JOURNEY_ISOLATION constraint enforced
```

### What This Unlocks
- Worker instantiation from definitions
- User journey → worker instance mapping
- Worker lifecycle management (spawn, kill, resume)

### Acceptance Criteria
- [x] `workers/factory.py` implements WorkerFactory
- [x] `workers/factory.py` implements spawn(), kill(), resume()
- [x] Worker instance carries definition + user_journey_id
- [x] Test: `workers/test_worker_factory.py` (spawn/kill/resume tests)

### Execution Steps

**Step 1: Implement WorkerFactory (90 min)**
```python
# workers/factory.py
from typing import Dict, Literal
from workers.definitions.schema import WorkerDefinition
from workers.definitions.loader import load_worker_definition
from workers.base import Worker
import uuid

class WorkerFactory:
    """Spawn worker instances from definitions"""

    _instances: Dict[str, Worker] = {}  # user_journey_id → worker instance

    @staticmethod
    async def spawn(
        definition: WorkerDefinition | str,
        user_journey_id: str,
        isolation_level: Literal["container", "process", "thread"] = "container"
    ) -> Worker:
        """
        Spawn worker instance for user journey

        Args:
            definition: WorkerDefinition or worker_id to load
            user_journey_id: Unique journey identifier (thread_id from checkpointer)
            isolation_level: Isolation boundary (container | process | thread)

        Returns:
            Worker instance with isolated workspace

        Flow:
            1. Load definition if worker_id provided
            2. Create isolated workspace
            3. Initialize worker instance
            4. Register constraints
            5. Return worker
        """
        # Load definition if worker_id string provided
        if isinstance(definition, str):
            definition = load_worker_definition(definition)

        # Create isolated workspace
        workspace_path = definition.runtime.workspace_template.format(
            user_journey_id=user_journey_id
        )

        # Instantiate worker (uses R11 Worker protocol)
        from workers.claude_code_worker import ClaudeCodeWorker  # R13.3

        worker = ClaudeCodeWorker(
            worker_id=f"{definition.worker_id}_{user_journey_id}",
            definition=definition,
            workspace_path=workspace_path,
            user_journey_id=user_journey_id,
            isolation_level=isolation_level
        )

        # Register in factory
        WorkerFactory._instances[user_journey_id] = worker

        return worker

    @staticmethod
    def get(user_journey_id: str) -> Worker | None:
        """Get existing worker instance for journey"""
        return WorkerFactory._instances.get(user_journey_id)

    @staticmethod
    async def kill(user_journey_id: str):
        """Terminate worker instance and cleanup workspace"""
        worker = WorkerFactory._instances.pop(user_journey_id, None)
        if worker:
            await worker.cleanup()

    @staticmethod
    async def resume(user_journey_id: str) -> Worker:
        """Resume existing worker instance or spawn new one"""
        existing = WorkerFactory.get(user_journey_id)
        if existing:
            return existing

        # No existing instance - need definition to spawn
        # In practice, would load from session metadata
        raise ValueError(f"Cannot resume: no worker instance for {user_journey_id}")
```

**Step 2: Implement ClaudeCodeWorker (60 min)**
```python
# workers/claude_code_worker.py
from workers.base import Worker, VoidResult, ExecutionResult
from workers.definitions.schema import WorkerDefinition
import asyncio

class ClaudeCodeWorker(Worker):
    """
    Worker instance wrapping Claude Code via MCP

    Implements R11 Worker protocol with R13 definition + isolation
    """

    def __init__(
        self,
        worker_id: str,
        definition: WorkerDefinition,
        workspace_path: str,
        user_journey_id: str,
        isolation_level: str = "container"
    ):
        self.worker_id = worker_id
        self.definition = definition
        self.workspace_path = workspace_path
        self.user_journey_id = user_journey_id
        self.isolation_level = isolation_level

        # TODO R13.3: Initialize container/process isolation
        self.container_id = None

    async def void(self, action) -> VoidResult:
        """
        Simulate action WITHOUT side effects

        Flow:
        1. Run constraint witnesses (R13.4)
        2. If witnesses pass, simulate via MCP
        3. Return predicted outcome
        """
        # R13.4: Automatic witness verification
        from workers.enforcement.witness import WitnessEnforcement

        warnings = await WitnessEnforcement.verify(
            worker_id=self.worker_id,
            action=action,
            constraints=self.definition.constraints
        )

        if warnings:
            return VoidResult(
                action_id=action.get("action_id", f"void_{uuid.uuid4().hex[:8]}"),
                success=False,
                predicted_outcome={},
                side_effect_occurred=False,
                simulation_timestamp=time.time(),
                warnings=warnings
            )

        # Simulate via MCP (dry-run mode)
        # TODO R13.3: Call claude-mesh MCP with simulate=True
        return VoidResult(
            action_id=action.get("action_id", f"void_{uuid.uuid4().hex[:8]}"),
            success=True,
            predicted_outcome={"simulated": True},
            side_effect_occurred=False,
            simulation_timestamp=time.time(),
            warnings=[]
        )

    async def execute(self, action) -> ExecutionResult:
        """
        Execute action WITH side effects

        Flow:
        1. Witnesses already ran in void() (R13.4)
        2. Execute via MCP in isolated workspace
        3. Return actual outcome
        """
        start_time = time.time()

        # TODO R13.3: Call claude-mesh MCP for actual execution
        # await mcp_execute(
        #     worker_id=self.worker_id,
        #     workspace=self.workspace_path,
        #     action=action
        # )

        return ExecutionResult(
            action_id=action.get("action_id", f"exec_{uuid.uuid4().hex[:8]}"),
            success=True,
            actual_outcome={"executed": True},
            side_effect_occurred=True,
            execution_timestamp=time.time(),
            duration_ms=(time.time() - start_time) * 1000,
            audit_log_id=f"audit_{self.worker_id}_{int(time.time())}"
        )

    async def cleanup(self):
        """Cleanup worker instance (kill container, delete workspace)"""
        # TODO R13.3: Kill docker container
        pass
```

**Step 3: Write Tests (30 min)**
```python
# workflows/test_worker_factory.py
import pytest
from workers.factory import WorkerFactory

@pytest.mark.asyncio
async def test_spawn_worker_from_definition():
    """Test spawning worker from definition"""
    worker = await WorkerFactory.spawn(
        definition="research_assistant_v1",
        user_journey_id="test_journey_1"
    )

    assert worker.worker_id.startswith("research_assistant_v1_")
    assert worker.user_journey_id == "test_journey_1"
    assert worker.definition.worker_id == "research_assistant_v1"
    assert "test_journey_1" in worker.workspace_path

@pytest.mark.asyncio
async def test_worker_isolation():
    """Test that different journeys get isolated workers"""
    worker_1 = await WorkerFactory.spawn("research_assistant_v1", "journey_1")
    worker_2 = await WorkerFactory.spawn("research_assistant_v1", "journey_2")

    assert worker_1.user_journey_id != worker_2.user_journey_id
    assert worker_1.workspace_path != worker_2.workspace_path
    assert worker_1.worker_id != worker_2.worker_id

@pytest.mark.asyncio
async def test_kill_worker():
    """Test killing worker instance"""
    worker = await WorkerFactory.spawn("research_assistant_v1", "test_journey_kill")

    assert WorkerFactory.get("test_journey_kill") is not None

    await WorkerFactory.kill("test_journey_kill")

    assert WorkerFactory.get("test_journey_kill") is None
```

### Files Created
- `workers/factory.py` (~150 lines)
- `workers/claude_code_worker.py` (~120 lines)
- `workflows/test_worker_factory.py` (~80 lines)

### Completion Signal
```bash
pytest workflows/test_worker_factory.py -v
```

**Output:** `3 passed`

---

## R13.3: Journey Isolation

**Task ID:** R13.3
**Type:** Infrastructure
**Status:** Complete ✅
**Dependencies:** R13.2 complete
**Estimated Duration:** 4 hours
**Actual Duration:** ~2 hours

### Witness
**Observable Truth:** Worker instances execute in isolated containers, workspace filesystems separate, no context bleed ✅

**Validation Result:**
```
6 tests passed in 0.09s
✅ R13.3 WITNESS SATISFIED
✅ Worker instances can execute in isolated containers
✅ Workspace filesystems are separate per journey
✅ No context bleed between journeys
✅ Session state persists across worker restarts
```

### What This Unlocks
- True user journey isolation (JOURNEY_ISOLATION constraint)
- Protected filesystem per journey
- Session persistence across invocations

### Acceptance Criteria
- [x] `workers/isolation/container.py` implements docker isolation
- [x] Each worker instance runs in dedicated container
- [x] Workspace filesystem isolated per journey
- [x] Test: Verify no context bleed between journeys
- [x] Test: Session state persists across worker restarts

### Execution Steps

**Step 1: Implement Container Isolation (2 hours)**
```python
# workers/isolation/container.py
import docker
from pathlib import Path

class ContainerIsolation:
    """Docker-based journey isolation"""

    client = docker.from_env()

    @staticmethod
    async def spawn_container(
        user_journey_id: str,
        workspace_path: str,
        container_image: str = "claude-code:latest"
    ) -> str:
        """
        Spawn isolated docker container for user journey

        Args:
            user_journey_id: Journey identifier
            workspace_path: Host workspace path
            container_image: Docker image to use

        Returns:
            Container ID

        Creates:
            - Isolated network namespace
            - Bind-mounted workspace volume
            - Read-only root filesystem
        """
        # Create workspace directory on host
        Path(workspace_path).mkdir(parents=True, exist_ok=True)

        # Spawn container
        container = ContainerIsolation.client.containers.run(
            image=container_image,
            name=f"worker_{user_journey_id}",
            detach=True,
            network_mode="bridge",  # Isolated network
            volumes={
                workspace_path: {
                    "bind": "/home/claude/workspace",
                    "mode": "rw"
                }
            },
            read_only=True,  # Root filesystem read-only
            tmpfs={"/tmp": "rw,size=100m"},  # Writable tmp
            environment={
                "USER_JOURNEY_ID": user_journey_id
            },
            labels={
                "langgraph.user_journey_id": user_journey_id,
                "langgraph.isolation": "container"
            }
        )

        return container.id

    @staticmethod
    async def kill_container(container_id: str):
        """Kill and remove container"""
        try:
            container = ContainerIsolation.client.containers.get(container_id)
            container.kill()
            container.remove()
        except docker.errors.NotFound:
            pass  # Already removed

    @staticmethod
    async def exec_in_container(
        container_id: str,
        command: str,
        timeout: int = 30
    ) -> dict:
        """
        Execute command in container

        Args:
            container_id: Container ID
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            {"exit_code": int, "output": str}
        """
        container = ContainerIsolation.client.containers.get(container_id)

        exec_result = container.exec_run(
            cmd=command,
            demux=True,
            timeout=timeout
        )

        return {
            "exit_code": exec_result.exit_code,
            "output": exec_result.output.decode() if exec_result.output else ""
        }
```

**Step 2: Integrate with ClaudeCodeWorker (1 hour)**
```python
# workers/claude_code_worker.py (update)
class ClaudeCodeWorker(Worker):
    async def __init__(self, ...):
        # ... existing init code ...

        # Spawn container on worker creation
        if self.isolation_level == "container":
            from workers.isolation.container import ContainerIsolation
            self.container_id = await ContainerIsolation.spawn_container(
                user_journey_id=self.user_journey_id,
                workspace_path=self.workspace_path,
                container_image=self.definition.runtime.container
            )

    async def execute(self, action) -> ExecutionResult:
        """Execute action in isolated container"""
        from workers.isolation.container import ContainerIsolation

        # Execute via MCP inside container
        result = await ContainerIsolation.exec_in_container(
            container_id=self.container_id,
            command=self._build_mcp_command(action),
            timeout=action.get("timeout", 30)
        )

        return ExecutionResult(
            success=result["exit_code"] == 0,
            actual_outcome={"output": result["output"]},
            side_effect_occurred=True,
            # ... rest of result
        )

    async def cleanup(self):
        """Kill container and cleanup workspace"""
        from workers.isolation.container import ContainerIsolation
        if self.container_id:
            await ContainerIsolation.kill_container(self.container_id)
```

**Step 3: Write Isolation Tests (1 hour)**
```python
# workflows/test_journey_isolation.py
import pytest
from workers.factory import WorkerFactory

@pytest.mark.asyncio
async def test_journey_isolation_no_context_bleed():
    """
    Test JOURNEY_ISOLATION constraint

    Verify:
    1. Two worker instances from same definition
    2. Instance 1 writes file
    3. Instance 2 cannot see file (no context bleed)
    """
    worker_1 = await WorkerFactory.spawn("research_assistant_v1", "journey_1")
    worker_2 = await WorkerFactory.spawn("research_assistant_v1", "journey_2")

    # Worker 1 writes file
    await worker_1.execute({
        "type": "write",
        "target": "secret.txt",
        "content": "classified information"
    })

    # Worker 2 lists files
    result = await worker_2.execute({"type": "list_files"})

    # Verify: Worker 2 should NOT see secret.txt
    assert "secret.txt" not in result.actual_outcome["files"], \
        "JOURNEY_ISOLATION violated: Context bleed detected"

    # Cleanup
    await WorkerFactory.kill("journey_1")
    await WorkerFactory.kill("journey_2")

@pytest.mark.asyncio
async def test_session_persistence():
    """
    Test session state persists across worker restarts

    Verify:
    1. Worker writes file
    2. Worker killed
    3. Worker resumed (new container, same workspace)
    4. File still exists
    """
    # Initial worker
    worker = await WorkerFactory.spawn("research_assistant_v1", "persistent_journey")

    await worker.execute({
        "type": "write",
        "target": "persistent.txt",
        "content": "persisted data"
    })

    # Kill worker
    await WorkerFactory.kill("persistent_journey")

    # Resume worker (new container, same workspace)
    worker_resumed = await WorkerFactory.spawn("research_assistant_v1", "persistent_journey")

    result = await worker_resumed.execute({"type": "read", "target": "persistent.txt"})

    assert result.actual_outcome["content"] == "persisted data", \
        "Session persistence failed"

    await WorkerFactory.kill("persistent_journey")
```

### Files Created
- `workers/isolation/__init__.py`
- `workers/isolation/container.py` (~120 lines)
- `workflows/test_journey_isolation.py` (~100 lines)

### Completion Signal
```bash
pytest workflows/test_journey_isolation.py -v
```

**Output:** `2 passed` (no context bleed, session persistence works)

---

## R13.4: Constraint Enforcement Platform

**Task ID:** R13.4
**Type:** Safety
**Status:** Roadmap
**Dependencies:** R13.3 complete
**Estimated Duration:** 3 hours

### Witness
**Observable Truth:** Constraints verified automatically before every execution, violations logged to alert dashboard, execution aborted on failure

### What This Unlocks
- Automatic constraint enforcement (WITNESS_AUTOMATION)
- Alert dashboard for violations
- Platform-level safety (not manual checking)

### Acceptance Criteria
- [ ] `workers/enforcement/witness.py` implements WitnessEnforcement
- [ ] `workers/enforcement/registry.py` registers witness functions
- [ ] Witnesses called automatically in ClaudeCodeWorker.void()
- [ ] Test: Constraint violation aborts execution
- [ ] Test: Alert dashboard receives violation events

### Execution Steps

**Step 1: Implement Witness Registry (1 hour)**
```python
# workers/enforcement/registry.py
from typing import Callable, Dict, Any, List

class WitnessRegistry:
    """Registry of witness verification functions"""

    _witnesses: Dict[str, Callable] = {}

    @staticmethod
    def register(witness_id: str, witness_fn: Callable):
        """
        Register witness function

        Args:
            witness_id: Constraint witness identifier (from worker definition)
            witness_fn: async function(action) -> List[str] (warnings)
        """
        WitnessRegistry._witnesses[witness_id] = witness_fn

    @staticmethod
    def is_registered(witness_id: str) -> bool:
        """Check if witness function registered"""
        return witness_id in WitnessRegistry._witnesses

    @staticmethod
    async def run(witness_id: str, action: Dict[str, Any]) -> List[str]:
        """
        Run witness verification

        Args:
            witness_id: Witness to run
            action: Action to verify

        Returns:
            List of warning messages (empty if constraint passes)

        Raises:
            KeyError: If witness not registered
        """
        if witness_id not in WitnessRegistry._witnesses:
            raise KeyError(f"Witness not registered: {witness_id}")

        witness_fn = WitnessRegistry._witnesses[witness_id]
        return await witness_fn(action)


# Example witness functions
async def verify_file_size_within_limit(action: Dict[str, Any]) -> List[str]:
    """Witness: Verify file size doesn't exceed limit"""
    warnings = []

    if action.get("type") == "write":
        content = action.get("content", "")
        size_bytes = len(content.encode())
        max_size = 1_000_000  # 1MB

        if size_bytes > max_size:
            warnings.append(
                f"File size {size_bytes} bytes exceeds limit {max_size} bytes"
            )

    return warnings


async def verify_search_count(action: Dict[str, Any]) -> List[str]:
    """Witness: Verify web search count within hourly limit"""
    # TODO: Track search count per user_journey_id
    # For now, placeholder
    return []


# Register witnesses
WitnessRegistry.register("verify_file_size_within_limit", verify_file_size_within_limit)
WitnessRegistry.register("verify_search_count", verify_search_count)
```

**Step 2: Implement Witness Enforcement (1 hour)**
```python
# workers/enforcement/witness.py
from typing import List, Dict, Any
from workers.definitions.schema import WorkerConstraint
from workers.enforcement.registry import WitnessRegistry

class WitnessEnforcement:
    """Platformized constraint verification"""

    @staticmethod
    async def verify(
        worker_id: str,
        action: Dict[str, Any],
        constraints: List[WorkerConstraint]
    ) -> List[str]:
        """
        Run all constraint witnesses for action

        Args:
            worker_id: Worker identifier
            action: Action to verify
            constraints: Worker constraints to enforce

        Returns:
            List of warning messages (empty if all constraints pass)

        Called automatically before every worker.execute()
        """
        all_warnings = []

        for constraint in constraints:
            # Run witness verification
            warnings = await WitnessRegistry.run(constraint.witness, action)

            if warnings:
                # Log violation
                await WitnessEnforcement._log_violation(
                    worker_id=worker_id,
                    constraint=constraint,
                    action=action,
                    warnings=warnings
                )

                all_warnings.extend(warnings)

        return all_warnings

    @staticmethod
    async def _log_violation(
        worker_id: str,
        constraint: WorkerConstraint,
        action: Dict[str, Any],
        warnings: List[str]
    ):
        """
        Log constraint violation

        Routes to appropriate feedback channel:
        - alert_dashboard: Send to alert dashboard
        - log: Write to execution log
        - email: Send email notification
        """
        violation_event = {
            "timestamp": time.time(),
            "worker_id": worker_id,
            "constraint_id": constraint.constraint_id,
            "action": action,
            "warnings": warnings
        }

        if constraint.feedback == "alert_dashboard":
            # TODO: Send to alert dashboard API
            print(f"🚨 CONSTRAINT VIOLATION: {violation_event}")

        elif constraint.feedback == "log":
            # Write to execution log
            import logging
            logging.warning(f"Constraint violation: {violation_event}")

        elif constraint.feedback == "email":
            # TODO: Send email notification
            pass
```

**Step 3: Write Enforcement Tests (1 hour)**
```python
# workflows/test_constraint_enforcement.py
import pytest
from workers.factory import WorkerFactory
from workers.enforcement.registry import WitnessRegistry

@pytest.mark.asyncio
async def test_constraint_violation_aborts_execution():
    """
    Test CONSTRAINT_NON_NEGOTIABILITY

    Verify:
    1. Worker has max_file_size constraint
    2. Attempt to write file exceeding limit
    3. void() returns warnings
    4. execute() NOT called
    """
    worker = await WorkerFactory.spawn("research_assistant_v1", "test_constraint")

    # Attempt to write large file (exceeds 1MB limit)
    large_content = "x" * 2_000_000  # 2MB

    void_result = await worker.void({
        "type": "write",
        "target": "large.txt",
        "content": large_content
    })

    # Verify: void() detected violation
    assert not void_result.success or void_result.warnings, \
        "Constraint violation not detected"
    assert "File size" in str(void_result.warnings), \
        "File size constraint not triggered"

    await WorkerFactory.kill("test_constraint")

@pytest.mark.asyncio
async def test_witness_automation():
    """
    Test WITNESS_AUTOMATION constraint

    Verify witnesses called automatically (not manually)
    """
    witness_called = []

    async def mock_witness(action):
        witness_called.append(True)
        return []

    WitnessRegistry.register("mock_witness_auto", mock_witness)

    # Create worker with mock witness
    from workers.definitions.schema import WorkerDefinition, WorkerConstraint, ...

    definition = WorkerDefinition(
        worker_id="test_auto",
        constraints=[
            WorkerConstraint(
                constraint_id="test_auto_constraint",
                witness="mock_witness_auto",
                feedback="log"
            )
        ],
        # ... rest of definition
    )

    worker = await WorkerFactory.spawn(definition, "test_auto_journey")

    # Execute action WITHOUT manually calling witness
    await worker.execute({"type": "test_action"})

    # Verify: Witness was called automatically
    assert len(witness_called) == 1, \
        "WITNESS_AUTOMATION violated: Witness not called automatically"

    await WorkerFactory.kill("test_auto_journey")
```

### Files Created
- `workers/enforcement/__init__.py`
- `workers/enforcement/registry.py` (~80 lines)
- `workers/enforcement/witness.py` (~100 lines)
- `workflows/test_constraint_enforcement.py` (~120 lines)

### Completion Signal
```bash
pytest workflows/test_constraint_enforcement.py -v
```

**Output:** `2 passed` (constraint violation aborts, witnesses run automatically)

---

## R13 Completion Criteria

### All Tests Pass
```bash
pytest workflows/test_worker_definitions.py -v      # R13.1
pytest workflows/test_worker_factory.py -v          # R13.2
pytest workflows/test_journey_isolation.py -v       # R13.3
pytest workflows/test_constraint_enforcement.py -v  # R13.4
```

### Witness Verification
```python
# End-to-end test
from workers.factory import WorkerFactory

# 1. Load worker definition (R13.1)
worker = await WorkerFactory.spawn("research_assistant_v1", "demo_journey")

# 2. Worker instance isolated (R13.2, R13.3)
assert "demo_journey" in worker.workspace_path

# 3. Constraints enforced automatically (R13.4)
result = await worker.execute({"type": "write", "target": "test.txt", "content": "x" * 2_000_000})
assert result.status == "rejected"  # Constraint violation

# 4. Valid actions execute
result = await worker.execute({"type": "write", "target": "small.txt", "content": "hello"})
assert result.success

await WorkerFactory.kill("demo_journey")
```

### Documentation Updated
- [ ] `README.md` updated with worker marketplace section
- [ ] `workers/definitions/examples/` contains 3+ example definitions
- [ ] `docs/worker-marketplace.md` created with architecture overview

---

## Post-R13: What This Enables

### Worker Marketplace Catalog
```yaml
workers/definitions/
├── research_assistant_v1.yaml
├── code_reviewer_v1.yaml
├── options_trader_v1.yaml
├── data_analyst_v1.yaml
└── documentation_writer_v1.yaml
```

### User Journey Workflow
```python
# User selects worker type from catalog
worker = await WorkerFactory.spawn("options_trader_v1", thread_id)

# Platform enforces constraints automatically
# Trust level determines autonomy
# Session persists across invocations
```

### Trust Escalation (R14+)
```python
# Worker earns trust through safe actions
worker.trust_manager.record_action(success=True, violations=0)

# Automatic promotion: supervised → monitored → autonomous
if worker.trust_level == "autonomous":
    # Can execute without approval
    await worker.execute(action)
else:
    # Requires human approval
    await request_approval(action)
```

---

## Timeline Estimate

**R13.0:** 30 minutes (fix parallel execution blocker)
**R13.1:** 2 hours (worker definition schema)
**R13.2:** 3 hours (worker factory)
**R13.3:** 4 hours (journey isolation)
**R13.4:** 3 hours (constraint enforcement platform)

**Total:** 12.5 hours (1.5 development days)

---

## Notes

**Key Insight:** R13 is CONFIGURATION LAYER on top of R11 EXECUTION LAYER. Worker definitions enable rapid creation of specialized agents with enforced safety.

**Production Safety:** Automatic witness verification prevents "forgot to check constraint" errors. Platform enforces, developers cannot bypass.

**Integration Point:** R13 workers integrate with R10 coordination via ExecutorNode. Each user journey gets isolated worker instance.
