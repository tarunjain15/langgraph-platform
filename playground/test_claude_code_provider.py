#!/usr/bin/env python3
"""
Test Script: ClaudeCodeProvider (subprocess + JSON)

Tests the simplified Claude Code CLI integration at Langfuse level.
Validates stateless execution, session continuity, and LangGraph integration.

Usage:
    # Test provider directly
    PYTHONPATH="." python playground/test_claude_code_provider.py

    # Test with custom prompt
    PYTHONPATH="." python playground/test_claude_code_provider.py "Summarize README.md"
"""

import sys
import asyncio
from typing import TypedDict
from unittest.mock import patch, MagicMock
import json

# Import the new provider
from lgp.agents.claude_code_provider import ClaudeCodeProvider
from lgp.agents.factory import create_agent_node


class TestState(TypedDict):
    """Simple test state for LangGraph workflow"""
    task: str
    analyzer_task: str
    analyzer_output: str
    analyzer_session_id: str
    analyzer_tokens: dict


def test_provider_initialization():
    """Test provider initialization with various configs"""
    print("=" * 60)
    print("TEST 1: Provider Initialization")
    print("=" * 60)

    # Default config
    provider = ClaudeCodeProvider({"role_name": "test"})
    assert provider.role_name == "test"
    assert provider.model == "sonnet"
    assert provider.allowed_tools == ["Read", "Grep", "Glob"]
    assert provider.max_turns == 10
    assert provider.container is None
    print("✅ Default config works")

    # Full config
    provider = ClaudeCodeProvider({
        "role_name": "researcher",
        "model": "opus",
        "allowed_tools": ["Read", "Write", "Bash"],
        "max_turns": 20,
        "cwd": "/tmp",
        "container": "claude-mcp"
    })
    assert provider.model == "opus"
    assert provider.container == "claude-mcp"
    assert provider.max_turns == 20
    print("✅ Full config works")

    print()


def test_command_building():
    """Test CLI command construction"""
    print("=" * 60)
    print("TEST 2: Command Building")
    print("=" * 60)

    # Local CLI
    provider = ClaudeCodeProvider({
        "role_name": "test",
        "model": "sonnet",
        "allowed_tools": ["Read", "Grep"],
        "max_turns": 5
    })

    cmd = provider._build_command("Test prompt")
    assert "claude" in cmd
    assert "-p" in cmd
    assert "Test prompt" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd
    assert "--model" in cmd
    assert "sonnet" in cmd
    assert "--allowedTools" in cmd
    assert "Read,Grep" in cmd
    print(f"✅ Local command: {' '.join(cmd[:6])}...")

    # With session resume
    cmd_resume = provider._build_command("Continue", session_id="abc123")
    assert "--resume" in cmd_resume
    assert "abc123" in cmd_resume
    print("✅ Session resume flag added")

    # Container isolation
    container_provider = ClaudeCodeProvider({
        "role_name": "sandboxed",
        "container": "claude-mcp"
    })

    cmd_container = container_provider._build_command("Test")
    assert cmd_container[0] == "docker"
    assert cmd_container[1] == "exec"
    assert cmd_container[2] == "claude-mcp"
    print(f"✅ Container command: {' '.join(cmd_container[:4])}...")

    print()


def test_response_parsing():
    """Test JSON response parsing"""
    print("=" * 60)
    print("TEST 3: Response Parsing")
    print("=" * 60)

    provider = ClaudeCodeProvider({"role_name": "analyzer"})

    # Simulate CLI JSON response
    mock_response = {
        "result": "Analysis complete: found 3 files",
        "session_id": "abc-123-def-456",
        "total_cost_usd": 0.0023,
        "num_turns": 3,
        "duration_ms": 1500,
        "duration_api_ms": 1200
    }

    state_updates = provider._parse_response(mock_response)

    assert state_updates["analyzer_output"] == "Analysis complete: found 3 files"
    assert state_updates["analyzer_session_id"] == "abc-123-def-456"
    assert state_updates["analyzer_tokens"]["cost"] == 0.0023
    assert state_updates["analyzer_tokens"]["turns"] == 3
    assert state_updates["analyzer_tokens"]["duration_ms"] == 1500
    print("✅ State updates correctly extracted")

    # Verify keys follow {role_name}_ pattern
    for key in state_updates:
        assert key.startswith("analyzer_"), f"Key {key} should start with analyzer_"
    print("✅ All keys follow {role_name}_ pattern")

    print()


def test_metadata():
    """Test Langfuse metadata generation"""
    print("=" * 60)
    print("TEST 4: Langfuse Metadata")
    print("=" * 60)

    provider = ClaudeCodeProvider({
        "role_name": "researcher",
        "model": "opus",
        "allowed_tools": ["Read", "Grep", "Glob", "Bash"],
        "container": "claude-mcp"
    })

    metadata = provider.get_metadata()

    assert metadata["provider"] == "claude_code"
    assert metadata["model"] == "opus"
    assert metadata["role"] == "researcher"
    assert metadata["container"] == "claude-mcp"
    assert "Read" in metadata["allowed_tools"]
    print(f"✅ Metadata: {metadata}")

    print()


def test_factory_integration():
    """Test factory creates correct node"""
    print("=" * 60)
    print("TEST 5: Factory Integration")
    print("=" * 60)

    # Test claude_code provider
    node = create_agent_node(
        provider_type="claude_code",
        config={"role_name": "test_agent", "model": "haiku"},
        provider_config={"enabled": True}
    )
    assert callable(node)
    print("✅ Factory creates claude_code node")

    # Test claude_code_container provider
    node_container = create_agent_node(
        provider_type="claude_code_container",
        config={"role_name": "sandboxed_agent"},
        provider_config={"enabled": True, "container": "my-container"}
    )
    assert callable(node_container)
    print("✅ Factory creates claude_code_container node")

    # Test disabled provider raises error
    try:
        create_agent_node(
            provider_type="claude_code",
            config={"role_name": "test"},
            provider_config={"enabled": False}
        )
        assert False, "Should raise ValueError for disabled provider"
    except ValueError as e:
        assert "not enabled" in str(e)
        print("✅ Disabled provider raises ValueError")

    print()


async def test_execute_mock():
    """Test execute_task with mocked subprocess"""
    print("=" * 60)
    print("TEST 6: Execute Task (Mocked)")
    print("=" * 60)

    provider = ClaudeCodeProvider({
        "role_name": "analyzer",
        "model": "sonnet",
        "allowed_tools": ["Read"]
    })

    # Mock subprocess response
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({
        "result": "Found 5 Python files",
        "session_id": "mock-session-123",
        "total_cost_usd": 0.001,
        "num_turns": 2,
        "duration_ms": 800,
        "duration_api_ms": 600
    })
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        result = await provider.execute_task(
            task="Count Python files",
            state={},
            config={}
        )

    assert result["analyzer_output"] == "Found 5 Python files"
    assert result["analyzer_session_id"] == "mock-session-123"
    assert result["analyzer_tokens"]["cost"] == 0.001
    print("✅ Mocked execution works")

    # Test session continuity
    with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
        await provider.execute_task(
            task="Continue analysis",
            state={"analyzer_session_id": "existing-session"},
            config={}
        )

        # Verify --resume flag was passed
        call_args = mock_subprocess.call_args[1]["args"] if "args" in mock_subprocess.call_args[1] else mock_subprocess.call_args[0][0]
        assert "--resume" in call_args
        assert "existing-session" in call_args
        print("✅ Session continuity passes --resume flag")

    print()


async def test_live_execution(prompt: str = None):
    """
    Test live execution with actual Claude Code CLI.

    Only runs if CLI is available.
    """
    print("=" * 60)
    print("TEST 7: Live Execution (Optional)")
    print("=" * 60)

    provider = ClaudeCodeProvider({
        "role_name": "live_test",
        "model": "haiku",  # Use cheapest model for testing
        "allowed_tools": ["Read"],
        "max_turns": 1  # Single turn for quick test
    })

    # Check availability
    if not provider.is_available():
        print("⏭️  Skipped: Claude Code CLI not available")
        return

    test_prompt = prompt or "What is 2 + 2? Reply with just the number."

    try:
        result = await provider.execute_task(
            task=test_prompt,
            state={},
            config={}
        )

        print(f"✅ Live execution successful")
        print(f"   Output: {result['live_test_output'][:100]}...")
        print(f"   Session: {result['live_test_session_id']}")
        print(f"   Cost: ${result['live_test_tokens']['cost']:.4f}")
        print(f"   Turns: {result['live_test_tokens']['turns']}")

    except Exception as e:
        print(f"⚠️  Live execution failed: {e}")

    print()


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CLAUDE CODE PROVIDER TEST SUITE")
    print("(subprocess + JSON implementation)")
    print("=" * 60 + "\n")

    # Synchronous tests
    test_provider_initialization()
    test_command_building()
    test_response_parsing()
    test_metadata()
    test_factory_integration()

    # Async tests
    asyncio.run(test_execute_mock())

    # Optional live test
    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(test_live_execution(prompt))

    print("=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
