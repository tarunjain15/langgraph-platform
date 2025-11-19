#!/usr/bin/env python3
"""
R5 Integration Verification Script

Verifies all R5 components are correctly integrated:
- R5.1: MCP Session Manager
- R5.2: Claude Code Node Factory
- R5.3: Repository Isolation (patterns)
- R5.4: Cost Tracking Metadata

Usage:
    python scripts/verify_r5_integration.py
"""

import sys


def test_r5_1_session_manager():
    """Test R5.1: MCP Session Manager"""
    print("=" * 80)
    print("R5.1: MCP Session Manager")
    print("=" * 80)

    try:
        from lgp.claude_code import MCPSessionManager, get_default_manager

        # Test class instantiation
        manager = MCPSessionManager(container_name="claude-mcp")
        assert manager.container_name == "claude-mcp"
        assert manager.server_params.command == "docker"
        assert "claude-mcp" in manager.server_params.args

        # Test default manager
        default_manager = get_default_manager()
        assert isinstance(default_manager, MCPSessionManager)

        print("✅ MCPSessionManager class: OK")
        print("✅ get_default_manager(): OK")
        print("✅ Server params configuration: OK")
        print()
        return True

    except Exception as e:
        print(f"❌ R5.1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_r5_2_node_factory():
    """Test R5.2: Claude Code Node Factory"""
    print("=" * 80)
    print("R5.2: Claude Code Node Factory")
    print("=" * 80)

    try:
        from lgp.claude_code import create_claude_code_node, AgentRoleConfig

        # Test config type
        config: AgentRoleConfig = {
            'role_name': 'test_agent',
            'repository': 'test-repo',
            'timeout': 30000
        }

        # Create mock session
        class MockSession:
            async def call_tool(self, tool_name, arguments):
                # Mock response
                class MockContent:
                    text = "Session ID: 12345678-1234-1234-1234-123456789abc\n\nTest output"

                class MockResult:
                    content = [MockContent()]

                return MockResult()

        mock_session = MockSession()

        # Create node
        node = create_claude_code_node(config, mock_session)

        # Verify node attributes
        assert node.__name__ == "test_agent_node"
        assert node.role_name == "test_agent"
        assert node.repository == "test-repo"

        print("✅ create_claude_code_node(): OK")
        print("✅ Node metadata: OK")
        print("✅ AgentRoleConfig type: OK")
        print()
        return True

    except Exception as e:
        print(f"❌ R5.2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_r5_3_repository_isolation():
    """Test R5.3: Repository Isolation Patterns"""
    print("=" * 80)
    print("R5.3: Repository Isolation (Pattern Verification)")
    print("=" * 80)

    try:
        from lgp.claude_code import create_claude_code_node, AgentRoleConfig

        # Create 3 nodes with different repositories
        configs = [
            {'role_name': 'researcher', 'repository': 'sample-app', 'timeout': 60000},
            {'role_name': 'writer', 'repository': 'sample-api', 'timeout': 60000},
            {'role_name': 'reviewer', 'repository': 'sample-infra', 'timeout': 60000}
        ]

        class MockSession:
            async def call_tool(self, tool_name, arguments):
                class MockContent:
                    text = f"Session ID: {arguments['repository']}-session-id\n\nOutput"
                class MockResult:
                    content = [MockContent()]
                return MockResult()

        session = MockSession()

        nodes = []
        for config in configs:
            node = create_claude_code_node(config, session)
            nodes.append(node)

        # Verify all nodes have different repositories
        repositories = [node.repository for node in nodes]
        assert len(set(repositories)) == 3, "Repositories should be unique"
        assert repositories == ['sample-app', 'sample-api', 'sample-infra']

        print("✅ 3 nodes created with different repositories: OK")
        print(f"   • researcher → sample-app")
        print(f"   • writer → sample-api")
        print(f"   • reviewer → sample-infra")
        print("✅ Repository isolation pattern: VERIFIED")
        print()
        return True

    except Exception as e:
        print(f"❌ R5.3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_r5_4_cost_tracking():
    """Test R5.4: Cost Tracking Metadata"""
    print("=" * 80)
    print("R5.4: Cost Tracking Metadata")
    print("=" * 80)

    try:
        from lgp.observability.tracers import LangfuseTracer

        # Test metadata without Claude Code
        metadata_basic = LangfuseTracer.get_metadata(
            'test_workflow',
            'experiment',
            uses_claude_code=False
        )

        assert 'cost_model' not in metadata_basic
        assert 'session_continuity' not in metadata_basic

        # Test metadata with Claude Code
        metadata_cc = LangfuseTracer.get_metadata(
            'test_workflow',
            'experiment',
            uses_claude_code=True
        )

        assert metadata_cc['cost_model'] == 'fixed_subscription'
        assert metadata_cc['session_continuity'] == 'enabled'
        assert metadata_cc['monthly_cost'] == 20.00
        assert metadata_cc['cost_type'] == 'predictable'

        # Test tags
        tags_basic = LangfuseTracer.get_tags('test_workflow', 'experiment', uses_claude_code=False)
        assert 'claude-code' not in tags_basic

        tags_cc = LangfuseTracer.get_tags('test_workflow', 'experiment', uses_claude_code=True)
        assert 'claude-code' in tags_cc
        assert 'stateful-sessions' in tags_cc

        print("✅ Metadata without Claude Code: OK (no cost fields)")
        print("✅ Metadata with Claude Code: OK")
        print(f"   • cost_model: {metadata_cc['cost_model']}")
        print(f"   • monthly_cost: ${metadata_cc['monthly_cost']}")
        print(f"   • session_continuity: {metadata_cc['session_continuity']}")
        print("✅ Tags with Claude Code: OK")
        print(f"   • claude-code: included")
        print(f"   • stateful-sessions: included")
        print()
        return True

    except Exception as e:
        print(f"❌ R5.4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """Run all verification tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "R5 INTEGRATION VERIFICATION" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    results = []

    # Run all tests
    results.append(("R5.1: MCP Session Manager", test_r5_1_session_manager()))
    results.append(("R5.2: Node Factory", test_r5_2_node_factory()))
    results.append(("R5.3: Repository Isolation", test_r5_3_repository_isolation()))
    results.append(("R5.4: Cost Tracking", test_r5_4_cost_tracking()))

    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 25 + "✅ R5 COMPLETE ✅" + " " * 33 + "║")
        print("╚" + "=" * 78 + "╝")
        print()
        print("All R5 components verified successfully!")
        print()
        print("Next Steps:")
        print("  • Update flow-pressure/04-current-state.md")
        print("  • Commit R5 implementation")
        print("  • Move to R6 (Workflow Templates)")
        print()
        return 0
    else:
        print("❌ VERIFICATION FAILED")
        print("Some R5 components have issues. Please review the errors above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
