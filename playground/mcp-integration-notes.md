# MCP Integration Notes

## Brave Search ✅ Working

Successfully integrated with:
- `brave_web_search`: General web search
- `brave_local_search`: Local business/place search

Configuration:
- Requires `BRAVE_API_KEY` environment variable
- MCP server: `@modelcontextprotocol/server-brave-search`

## Filesystem ✅ Working

Full filesystem access via MCP:
- read_file, write_file, edit_file
- create_directory, list_directory, directory_tree
- move_file, search_files, get_file_info

Configuration:
- Allowed directories configured in tool_registry.py
- MCP server: `@modelcontextprotocol/server-filesystem`

## Playwright ⚠️ Not Recommended

### Issue
Browser opens but cannot interact with page elements. The MCP client sends commands but Playwright doesn't respond to element interactions.

### Root Cause Analysis
Playwright MCP requires **stateful session management**:
1. Must call `browser_navigate` first to establish a page context
2. Page snapshots required before element interactions
3. Element references (`ref`) from snapshots must be used for clicks/typing

Our current MCP client implementation treats each tool call independently, losing the session context between calls.

### Workaround
Use Brave Search for web research instead of Playwright browser automation.

### Future Fix
To properly support Playwright:
1. Implement session state management in tool_registry.py
2. Cache page context between tool calls
3. Implement proper `browser_snapshot` → `browser_click` workflow
4. Consider using the official MCP SDK's session handling

## MCP Client Implementation

### Current Gaps (vs MCP Spec)

1. **No progress notifications**: We don't handle `notifications/progress`
2. **No cancellation**: We don't support `$/cancelRequest`
3. **Basic error handling**: Could be more robust

### What We Do Right

1. ✅ Proper JSON-RPC 2.0 protocol
2. ✅ Initialize handshake (initialize → initialized notification)
3. ✅ Environment variable injection for server processes
4. ✅ Tool listing and execution
5. ✅ Proper stdin/stdout transport
