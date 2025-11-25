#!/usr/bin/env python3
"""
Test Script: Claude Code Integration (R5.3)

Tests repository isolation with 3 Claude Code nodes in different workspaces.
Verifies session continuity and state flow.

Usage:
    python scripts/test_claude_code_integration.py "Your topic here"
"""

import sys
import asyncio
from typing import TypedDict, Annotated
import operator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import lgp modules
from lgp.claude_code import MCPSessionManager, create_claude_code_node, AgentRoleConfig
from lgp.observability import configure_langfuse, flush_traces
from langfuse import observe, propagate_attributes

# LangGraph imports
from langgraph.graph import StateGraph, END


class TestState(TypedDict):
    """Simple test state"""
    topic: str
    researcher_output: str
    researcher_session_id: str
    writer_output: str
    writer_session_id: str
    reviewer_output: str
    reviewer_session_id: str
    current_step: Annotated[list[str], operator.add]  # Topic channel (accumulates in parallel)


@observe(name="researcher_node_wrapper")
async def researcher_wrapper(state: TestState, node_func) -> TestState:
    """Wrapper for researcher node with Langfuse tracing"""
    print(f"🔍 RESEARCHER NODE")
    print(f"   Topic: {state['topic']}")

    task_state = {
        **state,
        'researcher_task': f"Research briefly (2 sentences): {state['topic']}"
    }

    result = await node_func(task_state)

    if result.get('researcher_session_id'):
        print(f"   ✅ Complete (session: {result['researcher_session_id'][:20]}...)")
    else:
        print(f"   ⚠️ Complete (no session_id)")

    print()
    return {**state, **result}


@observe(name="writer_node_wrapper")
async def writer_wrapper(state: TestState, node_func) -> TestState:
    """Wrapper for writer node with Langfuse tracing"""
    print(f"✍️  WRITER NODE")

    task_state = {
        **state,
        'writer_task': f"Based on: '{state['researcher_output']}', write 1 paragraph."
    }

    result = await node_func(task_state)

    if result.get('writer_session_id'):
        print(f"   ✅ Complete (session: {result['writer_session_id'][:20]}...)")
    else:
        print(f"   ⚠️ Complete (no session_id)")

    print()
    return {**state, **result}


@observe(name="reviewer_node_wrapper")
async def reviewer_wrapper(state: TestState, node_func) -> TestState:
    """Wrapper for reviewer node with Langfuse tracing"""
    print(f"🔎 REVIEWER NODE")

    task_state = {
        **state,
        'reviewer_task': f"Review (1-2 sentences): '{state['writer_output']}'"
    }

    result = await node_func(task_state)

    if result.get('reviewer_session_id'):
        print(f"   ✅ Complete (session: {result['reviewer_session_id'][:20]}...)")
    else:
        print(f"   ⚠️ Complete (no session_id)")

    print()
    return {**state, **result}


@observe(name="claude_code_workflow_test")
async def run_test(topic: str):
    """Execute test workflow with 3 Claude Code nodes"""

    print("=" * 80)
    print("CLAUDE CODE INTEGRATION TEST (R5.3)")
    print("=" * 80)
    print(f"\nTopic: {topic}")
    print()

    # Configure Langfuse
    configure_langfuse(enabled=True)

    # Initialize MCP session manager
    mcp_manager = MCPSessionManager()

    async with mcp_manager.create_session() as session:
        print("✅ MCP session initialized")
        print()

        # Define agent configurations
        researcher_config: AgentRoleConfig = {
            'role_name': 'researcher',
            'repository': 'sample-app',
            'timeout': 60000
        }

        writer_config: AgentRoleConfig = {
            'role_name': 'writer',
            'repository': 'sample-api',
            'timeout': 60000
        }

        reviewer_config: AgentRoleConfig = {
            'role_name': 'reviewer',
            'repository': 'sample-infra',
            'timeout': 60000
        }

        # Create Claude Code nodes
        researcher_node = create_claude_code_node(researcher_config, session)
        writer_node = create_claude_code_node(writer_config, session)
        reviewer_node = create_claude_code_node(reviewer_config, session)

        # Build workflow
        workflow = StateGraph(TestState)

        # Add nodes - directly use async wrapper functions
        async def research_node_wrapped(state):
            return await researcher_wrapper(state, researcher_node)

        async def write_node_wrapped(state):
            return await writer_wrapper(state, writer_node)

        async def review_node_wrapped(state):
            return await reviewer_wrapper(state, reviewer_node)

        workflow.add_node("research", research_node_wrapped)
        workflow.add_node("write", write_node_wrapped)
        workflow.add_node("review", review_node_wrapped)

        # Define flow
        workflow.set_entry_point("research")
        workflow.add_edge("research", "write")
        workflow.add_edge("write", "review")
        workflow.add_edge("review", END)

        # Compile
        app = workflow.compile()
        print("✅ Workflow compiled")
        print()

        # Initial state
        initial_state: TestState = {
            'topic': topic,
            'researcher_output': '',
            'researcher_session_id': '',
            'writer_output': '',
            'writer_session_id': '',
            'reviewer_output': '',
            'reviewer_session_id': '',
            'current_step': []  # Topic channel starts empty
        }

        # Execute with metadata
        print("🚀 Executing workflow...")
        print("-" * 80)
        print()

        with propagate_attributes(
            metadata={
                "workflow_type": "claude-code-test",
                "cost_model": "fixed_subscription",
                "session_continuity": "enabled",
                "test_phase": "R5.3"
            },
            tags=["claude-code", "langgraph-platform", "R5-test"]
        ):
            final_state = await app.ainvoke(initial_state)

        # Display results
        print()
        print("=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        print()
        print("📊 OUTPUTS:")
        print(f"  Research: {final_state['researcher_output'][:100]}..." if final_state.get('researcher_output') else "  Research: No output")
        print(f"  Article: {final_state['writer_output'][:100]}..." if final_state.get('writer_output') else "  Article: No output")
        print(f"  Review: {final_state['reviewer_output'][:100]}..." if final_state.get('reviewer_output') else "  Review: No output")
        print()
        print("🔗 SESSION IDs (Repository Isolation Proof):")
        print(f"  • Researcher (sample-app): {final_state['researcher_session_id']}")
        print(f"  • Writer (sample-api): {final_state['writer_session_id']}")
        print(f"  • Reviewer (sample-infra): {final_state['reviewer_session_id']}")
        print()

        # Verify isolation
        session_ids = [
            final_state['researcher_session_id'],
            final_state['writer_session_id'],
            final_state['reviewer_session_id']
        ]

        if len(set(session_ids)) == 3:
            print("✅ REPOSITORY ISOLATION VERIFIED: All 3 nodes have different session IDs")
        else:
            print("⚠️  WARNING: Session IDs not unique (possible isolation failure)")

        print()

        return final_state


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage: python scripts/test_claude_code_integration.py \"Your topic\"")
        print("\nExample:")
        print('  python scripts/test_claude_code_integration.py "Benefits of async Python"')
        sys.exit(1)

    topic = sys.argv[1]

    try:
        asyncio.run(run_test(topic))

        # Flush traces
        print("📤 Flushing traces to Langfuse...")
        flush_traces()
        print("✅ Traces sent")
        print()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
