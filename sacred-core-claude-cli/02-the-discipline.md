```yaml
name: Claude Code CLI Discipline
description: Constraints and patterns for Claude Code CLI integration as LLMProvider.
created: 2025-11-26
```

# The Discipline: Claude Code CLI Integration Constraints

## Sacred Constraints

### 1. INTERFACE_PARITY
```yaml
constraint: Claude Code CLI provider MUST implement the same LLMProvider interface as Ollama/OpenAI
rationale: Single integration pattern for all providers
enforcement: Type checking against LLMProvider ABC
violation: Custom methods that break provider interchangeability
```

### 2. STATELESS_BY_DEFAULT
```yaml
constraint: Every execute_task() call MUST be independent unless session_id explicitly passed
rationale: LangGraph manages state, not providers
enforcement: session_id is optional parameter, not required
violation: Provider that requires session setup before use
```

### 3. JSON_OUTPUT_ONLY
```yaml
constraint: MUST use --output-format json for all CLI invocations
rationale: Structured parsing, no regex, native metadata
enforcement: _build_command() always includes --output-format json
violation: Text parsing or regex extraction from CLI output
```

### 4. LANGFUSE_NATIVE
```yaml
constraint: MUST use @observe decorator for automatic tracing
rationale: Same observability pattern as other providers
enforcement: execute_task() decorated with @observe
violation: Manual Langfuse span creation or custom tracing
```

### 5. TRANSPORT_SIMPLICITY
```yaml
constraint: MUST use subprocess.run() directly, NOT MCP bridge
rationale: CLI provides JSON output natively, MCP adds unnecessary complexity
enforcement: No MCPSessionManager, no docker exec via MCP
violation: Any intermediate protocol layer between Python and CLI
```

### 6. COST_FROM_RESPONSE
```yaml
constraint: MUST extract cost from CLI response, NOT calculate externally
rationale: CLI provides total_cost_usd natively, more accurate than estimation
enforcement: Return response["total_cost_usd"] directly
violation: Token-based cost calculation for Claude Code
```

---

## Patterns

### Pattern 1: Command Building
```python
def _build_command(self, prompt: str, session_id: Optional[str] = None) -> list:
    """Build claude CLI command with all required flags."""
    cmd = []

    # Optional container prefix
    if self.container:
        cmd = ["docker", "exec", self.container]

    # Core command
    cmd.extend([
        "claude",
        "-p", prompt,
        "--output-format", "json",  # ALWAYS JSON
        "--model", self.model,
        "--max-turns", str(self.max_turns),
        "--allowedTools", ",".join(self.allowed_tools)
    ])

    # Optional session resume
    if session_id:
        cmd.extend(["--resume", session_id])

    return cmd
```

### Pattern 2: Response Parsing
```python
def _parse_response(self, stdout: str) -> Dict[str, Any]:
    """Parse CLI JSON response into state updates."""
    response = json.loads(stdout)

    return {
        f"{self.role_name}_output": response["result"],
        f"{self.role_name}_session_id": response["session_id"],
        f"{self.role_name}_tokens": {
            "cost": response["total_cost_usd"],
            "turns": response["num_turns"],
            "duration_ms": response["duration_ms"]
        }
    }
```

### Pattern 3: Error Handling
```python
def _handle_error(self, result: subprocess.CompletedProcess) -> None:
    """Handle CLI errors with actionable messages."""
    if result.returncode != 0:
        # Parse error from stderr or stdout
        try:
            error_data = json.loads(result.stdout)
            if error_data.get("is_error"):
                raise RuntimeError(f"Claude Code error: {error_data.get('result')}")
        except json.JSONDecodeError:
            pass

        raise RuntimeError(f"Claude Code CLI failed (exit {result.returncode}): {result.stderr}")
```

### Pattern 4: Langfuse Integration
```python
from langfuse import observe, get_client

@observe(name="claude_code_execute")
async def execute_task(self, task: str, state: Dict, config: Dict) -> Dict:
    """Execute with automatic Langfuse tracing."""
    response = self._run_cli(task, state.get(f"{self.role_name}_session_id"))

    # Update Langfuse with native cost (BONUS: more accurate than estimation)
    langfuse = get_client()
    langfuse.update_current_observation(
        usage={"total_cost": response["total_cost_usd"]}
    )

    return self._parse_response(response)
```

---

## Anti-Patterns

### Anti-Pattern 1: MCP Bridge
```python
# WRONG: Unnecessary complexity
async with mcp_manager.create_session() as session:
    result = await session.call_tool('mesh_execute', {...})
    # Parse text output with regex
    session_id = re.search(r'Session ID: ([a-f0-9-]+)', text).group(1)

# CORRECT: Direct subprocess
result = subprocess.run(['claude', '-p', prompt, '--output-format', 'json'], ...)
response = json.loads(result.stdout)
session_id = response["session_id"]  # Native JSON field
```

### Anti-Pattern 2: External Cost Calculation
```python
# WRONG: Calculate cost from tokens
cost = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000)

# CORRECT: Use native cost from CLI
cost = response["total_cost_usd"]  # Already calculated by CLI
```

### Anti-Pattern 3: Custom Session Management
```python
# WRONG: Complex session state machine
class SessionManager:
    def __init__(self):
        self.sessions = {}
    def get_or_create(self, user_id):
        ...

# CORRECT: Pass session_id in state (LangGraph handles persistence)
session_id = state.get(f"{role_name}_session_id")
if session_id:
    cmd.extend(["--resume", session_id])
```

### Anti-Pattern 4: Text Output Parsing
```python
# WRONG: Parse text output
result = subprocess.run(['claude', '-p', prompt], ...)
# Try to extract structured data from free text...

# CORRECT: Always use JSON output
result = subprocess.run(['claude', '-p', prompt, '--output-format', 'json'], ...)
response = json.loads(result.stdout)
```

---

## Decision Framework

### When to Use Which Provider

| Scenario | Provider | Rationale |
|----------|----------|-----------|
| Simple LLM completion | `claude_api` | No tools needed, thin-client |
| Code analysis/generation | `claude_code` | Needs Read, Grep, Glob tools |
| File modifications | `claude_code` | Needs Write, Edit tools |
| Git operations | `claude_code` | Needs Bash, Git tools |
| Multi-tenant workloads | `claude_code_container` | Needs isolation |
| Cost-sensitive dev | `ollama` | $0 cost |

### Tool Selection Guide

```yaml
read_only_analysis:
  allowed_tools: ["Read", "Grep", "Glob"]
  permission_mode: null  # Default read-only

code_modification:
  allowed_tools: ["Read", "Write", "Edit", "Grep", "Glob"]
  permission_mode: "acceptEdits"

full_agent:
  allowed_tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
  permission_mode: "acceptEdits"
  # Use container for isolation in production
```

---

## Enforcement

### Type Checking
```python
def create_provider(config: Dict) -> LLMProvider:
    """Factory ensures all providers implement LLMProvider."""
    provider_type = config.get("provider", "claude_code")

    if provider_type == "ollama":
        return OllamaProvider(config)
    elif provider_type == "claude_api":
        return ClaudeAPIProvider(config)
    elif provider_type == "claude_code":
        return ClaudeCodeProvider(config)
    elif provider_type == "claude_code_container":
        return ClaudeCodeProvider({**config, "container": config["container"]})

    raise ValueError(f"Unknown provider: {provider_type}")
```

### Validation
```python
def validate_provider(provider: LLMProvider) -> None:
    """Validate provider implements required interface."""
    assert hasattr(provider, 'execute_task'), "Missing execute_task"
    assert hasattr(provider, 'get_provider_name'), "Missing get_provider_name"
    assert hasattr(provider, 'get_cost_estimate'), "Missing get_cost_estimate"

    # Verify async
    import inspect
    assert inspect.iscoroutinefunction(provider.execute_task), "execute_task must be async"
```

---

## Witness Protocol

### Success Criteria
```yaml
interface_parity:
  - ClaudeCodeProvider implements LLMProvider ABC
  - execute_task() returns same structure as OllamaProvider
  - get_provider_name() returns "claude_code"

langfuse_integration:
  - @observe decorator on execute_task()
  - Traces visible in Langfuse dashboard
  - Cost tracking from native CLI response

simplicity:
  - No MCP bridge code
  - No regex parsing
  - subprocess.run() + json.loads() only
```

### Verification Commands
```bash
# Test CLI directly
claude -p "What is 2+2?" --output-format json | jq '.'

# Test in container
docker exec claude-mcp claude -p "test" --output-format json | jq '.'

# Verify JSON fields
claude -p "test" --output-format json | jq '{session_id, result, total_cost_usd, duration_ms, num_turns}'
```
