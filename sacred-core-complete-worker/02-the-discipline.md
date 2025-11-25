```yaml
name: Complete Worker - The Discipline
description: Sacred constraints protecting worker marketplace integrity. Isolation boundaries, constraint non-negotiability, witness automation.
created: 2025-11-25
version: 1.0.0
phase: R13
```

# Complete Worker: The Discipline

## What This Protects (ETERNAL)

**Threat to Primitive:**
```
Worker Marketplace Corruption = Workers bypass constraints, user journeys bleed context, trust escalation becomes meaningless
```

**Symptoms of Corruption:**
- Workers share state across user journeys (context bleed)
- Constraints checked manually instead of automatically
- Worker definitions contain executable code (security risk)
- Trust levels ignored during execution
- Witnesses return approval without actual verification
- Worker instances escape isolation boundaries

**Result:** Platform becomes unsafe, constraints become performative, marketplace loses integrity

---

## The Five Sacred Constraints (ETERNAL)

### 1. JOURNEY_ISOLATION

**Definition:**
```
Each user journey MUST execute in isolated environment. NO context bleed between journeys.
```

**Witness (Observable, Automatic, Continuous, Actionable):**
```python
# Test runs on every worker spawn
def test_journey_isolation(worker_instance_1, worker_instance_2):
    """
    Verify user journeys are isolated

    Test:
    1. Spawn two worker instances from same definition
    2. Set state in instance_1
    3. Verify state NOT visible in instance_2
    """
    worker_1 = WorkerFactory.spawn(definition, "journey_1")
    worker_2 = WorkerFactory.spawn(definition, "journey_2")

    await worker_1.execute({"type": "write", "target": "test.txt", "content": "secret"})

    # Verification: worker_2 should NOT see worker_1's files
    worker_2_files = await worker_2.execute({"type": "list_files"})
    assert "test.txt" not in worker_2_files["result"]["files"], \
        "JOURNEY_ISOLATION violation: Journey context leaked between instances"

    # Verification: worker instances have different workspace paths
    assert worker_1.workspace_path != worker_2.workspace_path, \
        "JOURNEY_ISOLATION violation: Shared workspace detected"
```

**Violation Example:**
```python
# ❌ VIOLATION: Shared workspace across instances
class WorkerFactory:
    SHARED_WORKSPACE = "/tmp/shared"  # ❌ All instances share same workspace

    @staticmethod
    def spawn(definition, user_journey_id):
        return Worker(workspace=SHARED_WORKSPACE)  # ❌ Context bleed
```

**Correct Pattern:**
```python
# ✅ CORRECT: Isolated workspace per journey
class WorkerFactory:
    @staticmethod
    def spawn(definition, user_journey_id):
        workspace = f"/home/claude/workspace/{user_journey_id}"  # ✅ Unique per journey
        return Worker(
            workspace=workspace,
            session_id=user_journey_id,
            container_id=f"worker_{user_journey_id}"  # ✅ Isolated container
        )
```

**Enforcement:** 100% (workspace isolation verified on spawn, filesystem access sandboxed)

---

### 2. CONSTRAINT_NON_NEGOTIABILITY

**Definition:**
```
Worker constraints CANNOT be bypassed, disabled, or overridden by user, worker, or platform code.
```

**Witness:**
```python
def test_constraint_enforcement(worker_definition):
    """
    Verify constraints enforced regardless of execution path

    Test:
    1. Worker definition has constraint: max_file_size = 1MB
    2. Attempt to execute action violating constraint
    3. Verify action rejected BEFORE execution
    """
    definition = WorkerDefinition(
        worker_id="test_worker",
        constraints=[
            WorkerConstraint(
                constraint_id="max_file_size",
                value=1_000_000,  # 1MB
                witness="verify_file_size_within_limit"
            )
        ]
    )

    worker = WorkerFactory.spawn(definition, "test_journey")

    # Attempt to write 2MB file (violates constraint)
    result = await worker.execute({
        "type": "write",
        "target": "large.txt",
        "content": "x" * 2_000_000  # 2MB
    })

    assert result.status == "rejected", \
        "CONSTRAINT_NON_NEGOTIABILITY violation: Large file write not rejected"
    assert "max_file_size" in result.reason, \
        "CONSTRAINT_NON_NEGOTIABILITY violation: Constraint violation not logged"
```

**Violation Example:**
```python
# ❌ VIOLATION: Constraint bypass via flag
async def execute(action, skip_constraints=False):  # ❌ Bypass flag
    if not skip_constraints:
        verify_constraints(action)
    return do_execution(action)

# ❌ User can bypass constraints
await worker.execute(action, skip_constraints=True)  # ❌ Constraints skipped
```

**Correct Pattern:**
```python
# ✅ CORRECT: Constraints always enforced
async def execute(action):
    # Constraints verified BEFORE execution, no bypass possible
    warnings = await WitnessEnforcement.verify(
        worker_id=self.worker_id,
        action=action,
        constraints=self.definition.constraints
    )

    if warnings:
        return VoidResult(
            success=False,
            warnings=warnings,
            reason="Constraint verification failed"
        )

    # Only reaches here if constraints pass
    return do_execution(action)
```

**Enforcement:** 100% (witness verification hardcoded in worker protocol, no bypass paths)

---

### 3. DEFINITION_DECLARATIVE_PURITY

**Definition:**
```
Worker definitions MUST be pure YAML data. NO executable code in definitions.
```

**Witness:**
```python
def test_definition_purity(worker_definition_file):
    """
    Verify worker definition contains only data, no code

    Test:
    1. Load worker definition YAML
    2. Verify all fields are primitive types or lists/dicts
    3. Verify no Python code, shell commands, or eval() usage
    """
    import yaml

    with open(worker_definition_file) as f:
        definition = yaml.safe_load(f)  # ✅ safe_load (no code execution)

    # Verification: All values are data types
    forbidden_patterns = [
        "import ",
        "eval(",
        "exec(",
        "__",
        "subprocess",
        "os.system",
        "lambda",
    ]

    definition_str = yaml.dump(definition)
    for pattern in forbidden_patterns:
        assert pattern not in definition_str, \
            f"DEFINITION_DECLARATIVE_PURITY violation: Code pattern '{pattern}' found in definition"
```

**Violation Example:**
```yaml
# ❌ VIOLATION: Executable code in definition
worker_definition:
  worker_id: "malicious_worker"
  identity:
    system_prompt: "You are helpful"
    # ❌ SECURITY RISK: Code injection
    onboarding:
      - "__import__('os').system('rm -rf /')"  # ❌ Code in data
```

**Correct Pattern:**
```yaml
# ✅ CORRECT: Pure data definition
worker_definition:
  worker_id: "safe_worker"
  identity:
    name: "Research Assistant"
    system_prompt: "You help with research tasks..."
    onboarding:  # ✅ Data only
      - "Load research database"
      - "Review citation style"

  constraints:  # ✅ Constraint IDs reference witness functions
    - constraint_id: "max_web_searches"
      value: 50
      witness: "verify_search_count"  # ✅ Function name (string), not code
```

**Enforcement:** 100% (YAML safe_load only, witness functions registered separately in code)

---

### 4. WITNESS_AUTOMATION

**Definition:**
```
Constraint witnesses MUST run automatically. NO manual verification calls in worker code.
```

**Witness:**
```python
def test_witness_automation():
    """
    Verify witnesses called automatically before execution

    Test:
    1. Define worker with constraint
    2. Execute action WITHOUT manually calling witness
    3. Verify witness ran automatically
    """
    witness_called = []

    # Mock witness function
    async def verify_test_constraint(action):
        witness_called.append(True)
        return []  # No warnings

    # Register witness
    WitnessRegistry.register("verify_test_constraint", verify_test_constraint)

    definition = WorkerDefinition(
        worker_id="test",
        constraints=[
            WorkerConstraint(
                constraint_id="test_constraint",
                witness="verify_test_constraint"
            )
        ]
    )

    worker = WorkerFactory.spawn(definition, "test_journey")

    # Execute WITHOUT manually calling witness
    await worker.execute({"type": "test_action"})

    assert len(witness_called) == 1, \
        "WITNESS_AUTOMATION violation: Witness not called automatically"
```

**Violation Example:**
```python
# ❌ VIOLATION: Manual witness calls
async def execute(action):
    # ❌ Developer must remember to call witness
    warnings = await verify_constraints(action)

    if warnings:
        return {"status": "rejected"}

    return do_execution(action)
```

**Correct Pattern:**
```python
# ✅ CORRECT: Witnesses called automatically by base class
class Worker(BaseWorker):
    async def execute(self, action):
        # ✅ BaseWorker.execute() automatically calls witnesses
        # Developer CANNOT forget - it's in the protocol
        return await super().execute(action)

class BaseWorker:
    async def execute(self, action):
        # ✅ Witness verification ALWAYS runs (automatic)
        warnings = await WitnessEnforcement.verify(
            worker_id=self.worker_id,
            action=action,
            constraints=self.definition.constraints
        )

        if warnings:
            return self._reject(warnings)

        return await self._do_execute(action)
```

**Enforcement:** 100% (Worker protocol enforces witness calls, subclasses cannot skip)

---

### 5. TRUST_LEVEL_MONOTONICITY

**Definition:**
```
Trust levels can only INCREASE (supervised → monitored → autonomous), never DECREASE, without explicit reset.
```

**Witness:**
```python
def test_trust_monotonicity(worker_instance):
    """
    Verify trust level progression is monotonic

    Test:
    1. Worker starts at "supervised"
    2. Earn trust → upgrade to "monitored"
    3. Verify cannot downgrade without explicit reset
    """
    worker = WorkerFactory.spawn(definition, "test_journey")

    assert worker.trust_level == "supervised", "Initial trust level incorrect"

    # Simulate trust earned (100 successful actions, 0 violations)
    worker.trust_manager.record_actions(successful=100, violations=0)
    worker.trust_manager.evaluate()

    assert worker.trust_level == "monitored", "Trust level not upgraded"

    # Attempt to manually downgrade
    try:
        worker.trust_level = "supervised"  # ❌ Should fail
        assert False, "TRUST_LEVEL_MONOTONICITY violation: Manual downgrade allowed"
    except ImmutableTrustLevelError:
        pass  # ✅ Correct: downgrade prevented

    # Reset requires explicit action
    worker.trust_manager.reset(reason="security_audit")
    assert worker.trust_level == "supervised", "Reset failed"
```

**Violation Example:**
```python
# ❌ VIOLATION: Trust level can be arbitrarily changed
worker.trust_level = "supervised"  # ❌ No protection
time.sleep(1)
worker.trust_level = "autonomous"  # ❌ Instant escalation
time.sleep(1)
worker.trust_level = "supervised"  # ❌ Arbitrary downgrade
```

**Correct Pattern:**
```python
# ✅ CORRECT: Trust level managed by TrustManager
class TrustManager:
    def __init__(self, initial_level="supervised"):
        self._level = initial_level
        self._action_history = []
        self._last_evaluation = time.time()

    @property
    def level(self):
        return self._level

    def evaluate(self):
        """
        Evaluate trust level based on action history
        Trust can only increase (monotonic)
        """
        if self._level == "supervised" and self._meets_monitored_criteria():
            self._level = "monitored"  # ✅ Upgrade only
        elif self._level == "monitored" and self._meets_autonomous_criteria():
            self._level = "autonomous"  # ✅ Upgrade only

    def reset(self, reason: str):
        """Explicit reset to supervised (requires justification)"""
        self._log_reset(reason)
        self._level = "supervised"
        self._action_history = []
```

**Enforcement:** 100% (TrustManager property is read-only, upgrades automatic, downgrades require reset())

---

## Constraint Compliance Checklist

Before implementing R13 features, verify:

- [ ] **JOURNEY_ISOLATION:** Workspace paths unique per user_journey_id
- [ ] **JOURNEY_ISOLATION:** Container/process isolation enforced
- [ ] **JOURNEY_ISOLATION:** Session state NOT shared across instances
- [ ] **CONSTRAINT_NON_NEGOTIABILITY:** No bypass flags in execute()
- [ ] **CONSTRAINT_NON_NEGOTIABILITY:** Witnesses always called before execution
- [ ] **DEFINITION_DECLARATIVE_PURITY:** YAML definitions use safe_load()
- [ ] **DEFINITION_DECLARATIVE_PURITY:** No eval(), exec(), or code in definitions
- [ ] **WITNESS_AUTOMATION:** BaseWorker protocol enforces witness calls
- [ ] **WITNESS_AUTOMATION:** Subclasses cannot skip verification
- [ ] **TRUST_LEVEL_MONOTONICITY:** TrustManager level property read-only
- [ ] **TRUST_LEVEL_MONOTONICITY:** Upgrades automatic, downgrades require reset()

---

## Violation Detection

### Automated Checks

**On Worker Definition Load:**
```python
def validate_definition(definition_file):
    """Run all constraint checks on definition load"""
    checks = [
        check_definition_purity,
        check_constraint_witnesses_registered,
        check_trust_level_valid,
    ]
    for check in checks:
        check(definition_file)
```

**On Worker Spawn:**
```python
def validate_spawn(worker_instance, user_journey_id):
    """Run all isolation checks on worker spawn"""
    checks = [
        check_journey_isolation,
        check_workspace_unique,
        check_container_isolated,
    ]
    for check in checks:
        check(worker_instance, user_journey_id)
```

**On Worker Execute:**
```python
def validate_execute(worker, action):
    """Run all enforcement checks on execution"""
    checks = [
        check_witnesses_ran,
        check_constraints_enforced,
        check_trust_level_respected,
    ]
    for check in checks:
        check(worker, action)
```

---

## Enforcement Mechanisms

### 1. Type System (Compile-Time)
```python
# Immutable trust level via property
@property
def trust_level(self) -> Literal["supervised", "monitored", "autonomous"]:
    return self._trust_level  # Read-only, no setter
```

### 2. Protocol Enforcement (Runtime)
```python
class Worker(Protocol):
    async def execute(self, action) -> ExecutionResult:
        """
        PROTOCOL REQUIREMENT: Must call WitnessEnforcement.verify()
        before executing action. Enforced by BaseWorker.
        """
        ...
```

### 3. Isolation Enforcement (Container/OS)
```python
# Docker container isolation
container = docker.run(
    image="claude-code:latest",
    name=f"worker_{user_journey_id}",
    network_mode="bridge",  # ✅ Isolated network
    volumes={
        f"/workspaces/{user_journey_id}": {
            "bind": "/home/claude/workspace",
            "mode": "rw"
        }
    },
    read_only=True,  # ✅ Root filesystem read-only
)
```

---

## Recovery from Violations

### Detected Constraint Bypass
```python
if constraint_bypass_detected:
    # 1. Terminate worker instance
    worker.kill()

    # 2. Alert dashboard
    alert_dashboard(
        severity="critical",
        message=f"Constraint bypass detected in {worker.worker_id}",
        journey_id=worker.user_journey_id
    )

    # 3. Reset trust level
    worker.trust_manager.reset(reason="constraint_bypass")

    # 4. Log to audit trail
    audit_log(event="constraint_violation", worker=worker)
```

### Detected Context Bleed
```python
if context_bleed_detected:
    # 1. Destroy both worker instances
    worker_1.kill()
    worker_2.kill()

    # 2. Investigation mode
    enable_investigation_mode(user_journey_1, user_journey_2)

    # 3. Alert security team
    alert_security(
        severity="high",
        message="Journey isolation breach detected"
    )
```

---

## Notes

**Key Insight:** Constraints are ETERNAL because they protect the primitive. Worker definitions, trust criteria, and witness implementations may evolve, but the constraint NAMES and witness PROTOCOL are sacred.

**Production Safety:** Automatic witness verification prevents "forgot to check constraint" errors. Platform enforces safety, developers cannot bypass.

**Testability:** Each constraint has observable witness that can ONLY pass if constraint holds. No performative compliance.
