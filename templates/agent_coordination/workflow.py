"""
Agent Coordination Template (⭐⭐⭐⭐ Expert)

MENTAL MODEL:
  4 Channels = Observe external truth → Agents plan intents → Coordinator resolves → Executor acts
  4 Nodes = ObserverNode, AgentNode(s), CoordinatorNode, ExecutorNode
  Flow = Observe → Plan → Coordinate → Execute → Loop
  Coordination = Topic (observation, intent, execution) + LastValue (coordination)

  External State (source of truth) ← Observer (read-only mirror)
                                       ↓
                        Observation Channel (Topic: accumulates events)
                                       ↓
                        Agent Nodes (read observations, write plans)
                                       ↓
                           Intent Channel (Topic: accumulates plans)
                                       ↓
                    Coordinator Node (detects conflicts, resolves)
                                       ↓
                   Coordination Channel (LastValue: latest decision)
                                       ↓
                     Executor Node (executes approved action)
                                       ↓
                    Execution Channel (Topic: immutable audit trail)

ANTI-PATTERNS TO AVOID:
  ❌ Agents execute directly → concurrent write errors
  ❌ Coordinator not reading all intents → conflicts missed
  ❌ Using LastValue for observation → events lost
  ❌ Using Topic for coordination → stale decisions
  ❌ Agent nodes with side effects → bypasses coordination
  ❌ Silent failures → audit trail incomplete
  ❌ Observer modifies external state → breaks read-only contract

CORRECT PATTERNS:
  ✅ Observer mirrors external truth only (read-only, automatic)
  ✅ Agent plans without executing (pure decision logic)
  ✅ Coordinator resolves all conflicts (deterministic policy)
  ✅ Executor logs to audit channel (no silent failures)
  ✅ Topic channels for history (observation, intent, execution)
  ✅ LastValue channel for decisions (coordination)
  ✅ Field ownership respected (each node owns its output)

4-CHANNEL PATTERN:
  1. OBSERVATION (Topic): External truth mirror
     - Observer writes observations
     - Agents read to form intents
     - Example: file changes, API events, user inputs

  2. INTENT (Topic): Agent action plans
     - Agents write plans (NO execution)
     - Coordinator reads to detect conflicts
     - Example: "agent_1 wants to modify file.txt"

  3. COORDINATION (LastValue): Conflict resolution
     - Coordinator writes approved decision
     - Executor reads to know what to execute
     - Example: "agent_1 approved, agent_2 deferred"

  4. EXECUTION (Topic): Immutable audit trail
     - Executor writes execution results
     - Includes: status, timestamp, duration
     - Example: "file.txt modified at 2025-11-24 14:30:00"

CUSTOMIZE THIS TEMPLATE:
  1. Zone 1: State Schema
     - Define your external observation fields
     - Add custom metadata to intent/execution logs

  2. Zone 2: Node Functions
     - ObserverNode: How to detect external changes
     - AgentNode: What actions to plan
     - CoordinatorNode: Conflict resolution policy
     - ExecutorNode: How to execute actions

  3. Zone 3: Graph Structure
     - Sequential vs parallel agents
     - Execution order (serial vs pipeline)

USAGE:
  lgp run workflows/my_coordination_workflow.py      # Experiment mode
  lgp serve workflows/my_coordination_workflow.py    # Hosted mode

WHEN TO USE THIS PATTERN:
  ✅ Multiple agents need to coordinate around external state
  ✅ Conflicts possible (same file, same resource, etc.)
  ✅ Audit trail required (compliance, debugging)
  ✅ Rollback needed (undo execution)
  ✅ What-if analysis (intent without execution)

WHEN NOT TO USE:
  ❌ Single agent, no conflicts → use basic template
  ❌ No external state → use multi_agent template
  ❌ Direct execution okay → use with_claude_code template

SEE ALSO:
  - Mental models: sacred-core/01-the-project.md#agent-coordination
  - 4-channel pattern: research/checkpoint-mastery/crystallised-understanding/ubiquitous-language/external-code-state-coordination.md
  - Discipline: sacred-core/02-the-discipline.md#channel-coordination-purity
  - Reference implementations: workflows/observation_test.py, workflows/intent_test.py, workflows/coordination_test.py, workflows/execution_test.py
"""

import time
import asyncio
from typing import TypedDict, Annotated, Optional
from pathlib import Path
from langgraph.graph import StateGraph, START, END
import operator


# ========================================
# ZONE 1: State Schema (4 Channels)
# ← CUSTOMIZE: Add domain-specific observation fields
# ========================================

class AgentCoordinationState(TypedDict):
    """
    State schema with 4 coordination channels.

    PATTERN: Topic channels accumulate history, LastValue channels hold latest state
    """
    # CHANNEL 1: Observation (Topic - accumulates all external events)
    # ← CUSTOMIZE: Define what external changes you observe
    external_changes: Annotated[list[dict], operator.add]  # Observer writes, Agents read
    """
    Example observation event:
    {
        "type": "file_modified" | "api_event" | "user_input",
        "path": "/path/to/resource",
        "timestamp": 1763981577.2562408,
        "observer_id": "fs_observer_1"
    }
    """

    # CHANNEL 2: Intent (Topic - accumulates all agent plans)
    # ← CUSTOMIZE: What actions can agents plan
    intents: Annotated[list[dict], operator.add]  # Agents write, Coordinator reads
    """
    Example intent:
    {
        "agent_id": "agent_alpha",
        "action": {"type": "modify_file", "target": "/path/to/file"},
        "reason": "Responding to file_modified event",
        "timestamp": 1763981583.969653
    }
    """

    # CHANNEL 3: Coordination (LastValue - latest decision only)
    # ← CUSTOMIZE: Resolution policy metadata
    coordination_decision: Optional[dict]  # Coordinator writes, Executor reads
    """
    Example decision:
    {
        "approved_agent_id": "agent_alpha",
        "action": {"type": "modify_file", "target": "/path/to/file"},
        "execution_order": ["agent_alpha", "agent_beta"],
        "deferred": ["agent_beta"],
        "resolution_policy": "timestamp_first",
        "conflict_type": "same_target"
    }
    """

    # CHANNEL 4: Execution (Topic - immutable audit trail)
    # ← CUSTOMIZE: What metadata to log
    executions: Annotated[list[dict], operator.add]  # Executor writes (audit log)
    """
    Example execution log:
    {
        "executor_id": "executor_main",
        "agent_id": "agent_alpha",
        "action": {"type": "modify_file", "target": "/path/to/file"},
        "result": "File modified successfully",
        "status": "success" | "failure",
        "timestamp": 1763981583.969859,
        "duration_ms": 1.20
    }
    """


# ========================================
# ZONE 2: Node Functions
# ← CUSTOMIZE: Replace with your domain logic
# ========================================

# ------------------------------------------------------------
# ObserverNode (R10.1) - Mirrors External State
# ------------------------------------------------------------

class ObserverNode:
    """
    Observes external state changes (read-only mirror).

    SACRED PROPERTIES:
      - Read-only (never modifies external state)
      - Automatic (detects changes <100ms)
      - External source of truth (state exists outside)

    ← CUSTOMIZE: How to detect changes (polling, webhooks, file watcher)
    """

    def __init__(self, observer_id: str = "observer_1"):
        self.observer_id = observer_id
        # ← CUSTOMIZE: Initialize your observation mechanism
        # Examples: watchdog.Observer, API polling, webhook listener

    async def observe(self, state: AgentCoordinationState) -> dict:
        """
        Observe external changes, emit to observation channel.

        Returns only external_changes field (field ownership).

        ← CUSTOMIZE: How to detect and structure observations
        """
        # ← CUSTOMIZE: Implement your observation logic
        # Example: Check file system, poll API, read message queue

        # Placeholder: Simulate observation
        observations = []
        # If changes detected:
        # observations.append({
        #     "type": "your_event_type",
        #     "path": "resource_identifier",
        #     "timestamp": time.time(),
        #     "observer_id": self.observer_id
        # })

        if not observations:
            return {}  # No changes detected

        # Return only owned field (external_changes)
        return {"external_changes": observations}


# ------------------------------------------------------------
# AgentNode (R10.2) - Plans Actions (No Execution)
# ------------------------------------------------------------

class AgentNode:
    """
    Reads observations, generates action plans (ZERO side effects).

    SACRED PROPERTIES:
      - Pure decision logic (no I/O)
      - Reads observation channel
      - Writes intent channel
      - Intent ≠ Execution (separation)

    ← CUSTOMIZE: Agent decision logic
    """

    def __init__(self, agent_id: str, strategy: str = "default"):
        self.agent_id = agent_id
        self.strategy = strategy

    async def plan(self, state: AgentCoordinationState) -> dict:
        """
        Read observations, generate action plan (NO execution).

        Returns only intents field (field ownership).

        ← CUSTOMIZE: Decision logic for your domain
        """
        observations = state.get("external_changes", [])

        if not observations:
            return {}  # Nothing to react to

        latest_obs = observations[-1]

        # ← CUSTOMIZE: Decide what action to plan
        # Example decision logic:
        action_plan = {
            "type": "process_event",  # ← CUSTOMIZE: Your action type
            "target": latest_obs.get("path", "unknown"),
            "strategy": self.strategy
        }

        intent = {
            "agent_id": self.agent_id,
            "action": action_plan,
            "reason": f"Responding to {latest_obs['type']}",
            "timestamp": time.time()
        }

        print(f"[Agent {self.agent_id}] Intent: {action_plan['type']} (NOT executing)")

        # Return only owned field (intents)
        return {"intents": [intent]}


# ------------------------------------------------------------
# CoordinatorNode (R10.3) - Resolves Conflicts
# ------------------------------------------------------------

class CoordinatorNode:
    """
    Detects conflicts between intents, applies resolution policy.

    SACRED PROPERTIES:
      - Pure coordination logic (no execution)
      - Reads ALL intents
      - Deterministic conflict resolution
      - LastValue channel (only latest decision)

    ← CUSTOMIZE: Conflict detection rules and resolution policy
    """

    def __init__(self, policy: str = "timestamp_first"):
        self.policy = policy
        # ← CUSTOMIZE: Configure resolution policy
        # Options: timestamp_first, priority_based, resource_aware, custom

    async def coordinate(self, state: AgentCoordinationState) -> dict:
        """
        Read intents, detect conflicts, resolve, emit decision.

        Returns only coordination_decision field (field ownership).

        ← CUSTOMIZE: Conflict detection algorithm and policy
        """
        intents = state.get("intents", [])

        if not intents:
            return {}  # Nothing to coordinate

        print(f"[Coordinator] Analyzing {len(intents)} intent(s)...")

        # ← CUSTOMIZE: Detect conflicts (same target, resource contention, etc.)
        conflict = self.detect_conflicts(intents)

        if conflict:
            print(f"[Coordinator] CONFLICT DETECTED: {conflict['conflict_type']}")
            decision = self.resolve_policy(conflict)
            print(f"[Coordinator] RESOLVED via {decision['resolution_policy']}")
            return {"coordination_decision": decision}
        else:
            # No conflict - approve first intent
            print(f"[Coordinator] No conflicts, approving first intent")
            decision = {
                "approved_agent_id": intents[0]["agent_id"],
                "action": intents[0]["action"],
                "execution_order": [intents[0]["agent_id"]],
                "deferred": [],
                "resolution_policy": "no_conflict"
            }
            return {"coordination_decision": decision}

    def detect_conflicts(self, intents: list[dict]) -> Optional[dict]:
        """
        Detect conflicts between intents.

        ← CUSTOMIZE: Define what constitutes a conflict
        """
        if len(intents) < 2:
            return None  # No conflict with single intent

        # ← CUSTOMIZE: Implement conflict detection
        # Example: Check if multiple intents target same resource
        targets = {}
        for intent in intents:
            target = intent["action"].get("target", "unknown")
            if target not in targets:
                targets[target] = []
            targets[target].append(intent)

        # Find conflicts
        for target, intent_list in targets.items():
            if len(intent_list) > 1:
                return {
                    "conflict_type": "same_target",
                    "target": target,
                    "intents": intent_list
                }

        return None  # No conflicts

    def resolve_policy(self, conflict: dict) -> dict:
        """
        Resolve conflict via policy.

        ← CUSTOMIZE: Define resolution strategy
        """
        intents = conflict["intents"]

        # ← CUSTOMIZE: Implement your resolution policy
        if self.policy == "timestamp_first":
            winner = min(intents, key=lambda x: x["timestamp"])
        elif self.policy == "priority_based":
            # ← CUSTOMIZE: Implement priority logic
            winner = intents[0]
        else:
            winner = intents[0]

        deferred = [i["agent_id"] for i in intents if i != winner]

        return {
            "approved_agent_id": winner["agent_id"],
            "action": winner["action"],
            "execution_order": [winner["agent_id"]] + deferred,
            "deferred": deferred,
            "resolution_policy": self.policy,
            "conflict_type": conflict["conflict_type"],
            "target": conflict.get("target")
        }


# ------------------------------------------------------------
# ExecutorNode (R10.4) - Executes Actions + Logs
# ------------------------------------------------------------

class ExecutorNode:
    """
    Reads approved actions, executes them, logs to audit trail.

    SACRED PROPERTIES:
      - Reads coordination_decision
      - Applies approved action (side effect!)
      - Logs result to execution channel
      - Logs failures (no silent failures)

    ← CUSTOMIZE: How to execute actions
    """

    def __init__(self, executor_id: str = "executor_1"):
        self.executor_id = executor_id

    async def execute(self, state: AgentCoordinationState) -> dict:
        """
        Read coordination decision, execute approved action, log result.

        Returns only executions field (field ownership).

        ← CUSTOMIZE: Execution logic for your actions
        """
        decision = state.get("coordination_decision")

        if not decision:
            print(f"[Executor] No coordination decision to execute")
            return {}

        approved_agent = decision["approved_agent_id"]
        action = decision["action"]

        print(f"[Executor] Executing approved action from {approved_agent}...")

        start_time = time.time()
        status = "success"
        result_message = ""

        try:
            # ← CUSTOMIZE: Apply the action (side effect!)
            result_message = await self.apply_action(action)
            status = "success"
            print(f"[Executor] ✅ SUCCESS: {result_message}")

        except Exception as e:
            result_message = f"Error: {str(e)}"
            status = "failure"
            print(f"[Executor] ❌ FAILED: {result_message}")

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # Log execution to audit trail
        execution_log = {
            "executor_id": self.executor_id,
            "agent_id": approved_agent,
            "action": action,
            "result": result_message,
            "status": status,
            "timestamp": end_time,
            "duration_ms": duration_ms
        }

        print(f"[Executor] Logged to execution channel (audit trail)")

        # Return only owned field (executions)
        return {"executions": [execution_log]}

    async def apply_action(self, action: dict) -> str:
        """
        Actually perform the action (produces side effect).

        ← CUSTOMIZE: Implement your execution logic
        """
        action_type = action["type"]
        target = action.get("target", "unknown")

        # ← CUSTOMIZE: Implement action execution
        # Examples: modify file, call API, update database, send message

        # Placeholder implementation
        if action_type == "process_event":
            # Simulate work
            await asyncio.sleep(0.001)
            return f"Processed event for {target}"
        else:
            raise ValueError(f"Unknown action type: {action_type}")


# ========================================
# ZONE 3: Graph Structure
# ← CUSTOMIZE: Adjust flow (sequential vs parallel agents)
# ========================================

def create_workflow():
    """
    Create agent coordination workflow with 4 channels.

    Flow:
      START → observer → [agent_1, agent_2, ...] → coordinator → executor → END

    ← CUSTOMIZE: Add/remove agents, adjust flow pattern
    """
    # Create node instances
    # ← CUSTOMIZE: Configure your nodes
    observer = ObserverNode(observer_id="observer_1")
    agent_1 = AgentNode(agent_id="agent_alpha", strategy="strategy_1")
    agent_2 = AgentNode(agent_id="agent_beta", strategy="strategy_2")
    coordinator = CoordinatorNode(policy="timestamp_first")
    executor = ExecutorNode(executor_id="executor_main")

    # Build graph
    workflow = StateGraph(AgentCoordinationState)

    # Add nodes
    workflow.add_node("observer", observer.observe)
    workflow.add_node("agent_1", agent_1.plan)
    workflow.add_node("agent_2", agent_2.plan)  # ← CUSTOMIZE: Add more agents
    workflow.add_node("coordinator", coordinator.coordinate)
    workflow.add_node("executor", executor.execute)

    # Define flow
    # ← CUSTOMIZE: Sequential vs parallel agents
    workflow.add_edge(START, "observer")
    workflow.add_edge("observer", "agent_1")  # Agents run in parallel
    workflow.add_edge("observer", "agent_2")
    workflow.add_edge("agent_1", "coordinator")
    workflow.add_edge("agent_2", "coordinator")
    workflow.add_edge("coordinator", "executor")
    workflow.add_edge("executor", END)

    # Compile workflow
    app = workflow.compile()

    return app


# ========================================
# Main Entry Point (for testing)
# ========================================

async def main():
    """
    Example usage of agent coordination workflow.

    ← CUSTOMIZE: Add your input configuration
    """
    print("\n" + "="*60)
    print("AGENT COORDINATION WORKFLOW TEST")
    print("="*60 + "\n")

    app = create_workflow()

    # Run workflow
    # ← CUSTOMIZE: Provide your initial state
    result = await app.ainvoke(
        {
            "external_changes": [],
            "intents": [],
            "coordination_decision": None,
            "executions": []
        },
        {"configurable": {"thread_id": "test_1"}}
    )

    # Display results
    print("\nRESULTS:")
    print(f"  Observations: {len(result.get('external_changes', []))}")
    print(f"  Intents: {len(result.get('intents', []))}")
    print(f"  Decision: {result.get('coordination_decision') is not None}")
    print(f"  Executions: {len(result.get('executions', []))}")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
