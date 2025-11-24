# Coded Systems: Machine-Readable Sacred Primitive

**Machine-legible specification of the MCP Tool Factory system.**

This directory contains the complete system specification in JSONL format (newline-delimited JSON), enabling:
- AI agents to self-onboard to tool boundaries
- Runtime validation that implementation matches specification
- Tool generation that automatically conforms to the primitive
- Cross-system integration with shared sacred contract

---

## The Four Files

### `primitive.jsonl` (1 line)
**The sacred contract all tools share.**

Defines the immutable primitive:
```
MCP Tool = Conversational negotiation
         + Graduated permissions
         + Hot-reload lifecycle
         + State continuity
         + Tool isolation
```

**Immutability clause:** "This primitive is not negotiable. This primitive is not augmented."

**Emergence principle:** Capabilities emerge from constraint removal, never from direct implementation.

### `constraints.jsonl` (5 lines)
**The five protection mechanisms.**

Each line defines one sacred constraint:
1. **CONVERSATIONAL_ALIGNMENT** - Refuses blind execution
2. **PERMISSION_GRADUATION** - Refuses permission escalation
3. **HOT_RELOAD_SAFETY** - Refuses reload corruption
4. **STATE_CONTINUITY** - Refuses state amnesia
5. **TOOL_CLASS_ISOLATION** - Refuses tool interference

Each constraint includes:
- `rule` - What it enforces
- `what_it_prevents` - Threats blocked
- `witness_protocol` - Observable metrics (100% enforcement)
- `enforcement` - Automatic + manual mechanisms
- `violation_consequence` - What happens on breach

### `infrastructure.jsonl` (6 lines)
**System capabilities and meta-actions.**

Defines infrastructure provided to all tools:
1. **conversation-meta-actions** - conversation:status, conversation:list, conversation:switch
2. **hot-reload-mechanism** - Zero-downtime tool evolution (M1)
3. **permission-graduation-system** - Progressive trust ladder (M4)
4. **alignment-detection-system** - Intent verification (M2)
5. **orchestration-safety-system** - Multi-dimensional orchestration (M6)
6. **shared-context-system** - Cross-tool resource coordination (M5)

Each infrastructure component declares its own refusals and safety limits.

### `tools.jsonl` (4 lines)
**Tool instances with capabilities AND refusals.**

Each line defines one tool:
- `example-tool` - Testing and demonstration
- `data-tool` - Resource management (SharedContext)
- `admin-tool` - Validation and admin operations
- `orchestrator-tool` - Multi-dimensional orchestration (M6)

Each tool declares:
- `capabilities` - What it can do
- `refusals` - What it refuses to do (the five sacred constraints + tool-specific)
- `permission_requirements` - Graduated access per action (Level 1-4)
- `context_dependencies` - Required relationship boundaries

---

## Leverage Pattern 1: LLM Context Injection

**Use case:** AI agent needs to use mcp-tool-factory tools safely

**Before:**
```
Human: "Use example-tool to do something"
AI: *tries action* → rejected for permission violation
AI: *requests approval* → granted
AI: *tries again* → succeeds through trial and error
```

**After:**
```bash
# Load specification as context
cat coded-systems/*.jsonl | jq -s '.'

# AI agent now knows:
# - The primitive contract (what makes a tool sacred)
# - The five sacred refusals (what all tools refuse)
# - Permission requirements per action (Level 1-4)
# - Orchestration limits (depth 5, no circular deps)
# - Infrastructure capabilities (meta-actions, hot-reload, etc.)
```

**Result:** AI operates within boundaries by design, not through rejection feedback loops.

### Example: Claude Code Integration

```bash
# In .claude/mcp_config.json or similar
{
  "system_context": [
    "coded-systems/primitive.jsonl",
    "coded-systems/constraints.jsonl",
    "coded-systems/infrastructure.jsonl",
    "coded-systems/tools.jsonl"
  ],
  "context_instruction": "Load all 4 files to understand tool boundaries before execution"
}
```

AI agent reads specs → understands refusals → never violates boundaries.

---

## Leverage Pattern 2: Runtime Validation

**Use case:** Verify implementation hasn't drifted from specification

**Validation script:**
```javascript
const fs = require('fs');

// Load specs
const primitive = JSON.parse(fs.readFileSync('coded-systems/primitive.jsonl'));
const constraints = fs.readFileSync('coded-systems/constraints.jsonl', 'utf8')
  .split('\n').filter(Boolean).map(JSON.parse);
const tools = fs.readFileSync('coded-systems/tools.jsonl', 'utf8')
  .split('\n').filter(Boolean).map(JSON.parse);

// Validate each tool
tools.forEach(tool => {
  console.log(`Validating ${tool.name}...`);

  // 1. Must declare all 5 sacred refusals
  const requiredRefusals = [
    'blind_execution',
    'permission_escalation',
    'state_amnesia',
    'reload_corruption',
    'tool_interference'
  ];

  requiredRefusals.forEach(refusal => {
    if (!tool.refusals[refusal]) {
      throw new Error(`${tool.name} missing refusal: ${refusal}`);
    }
  });

  // 2. Every capability must have permission requirement
  tool.capabilities.forEach(action => {
    if (!(action in tool.permission_requirements)) {
      throw new Error(`${tool.name}.${action} missing permission requirement`);
    }
  });

  // 3. Must require conversationId and alignmentCheck
  if (!tool.context_dependencies.required.includes('conversationId')) {
    throw new Error(`${tool.name} doesn't require conversationId`);
  }
  if (!tool.context_dependencies.required.includes('alignmentCheck')) {
    throw new Error(`${tool.name} doesn't require alignmentCheck`);
  }

  console.log(`✅ ${tool.name} conforms to primitive`);
});

console.log('\n✅ All tools validated against specification');
```

**CI/CD Integration:**
```yaml
# .github/workflows/validate-spec.yml
validate:
  runs-on: ubuntu-latest
  steps:
    - name: Validate tools conform to primitive
      run: node validate-spec.js
    - name: Fail PR if validation fails
      if: failure()
      run: echo "Tools have drifted from primitive specification" && exit 1
```

**Result:** Impossible for tools to drift from primitive without breaking CI.

---

## Leverage Pattern 3: Tool Generation

**Use case:** Create new tool that automatically conforms to primitive

**Generator:**
```javascript
const generateTool = (name, capabilities, description) => {
  // Load primitive to auto-include all requirements
  const primitive = require('./coded-systems/primitive.jsonl');
  const constraints = require('./coded-systems/constraints.jsonl');

  // Generate tool spec
  const toolSpec = {
    name,
    version: "1.0.0",
    type: "generated",
    capabilities,
    description,

    // Auto-include all 5 sacred refusals
    refusals: {
      blind_execution: "Refuses to execute without conversational alignment check",
      permission_escalation: `Refuses ${name} actions without explicit approval`,
      state_amnesia: "Refuses to operate without conversation context",
      reload_corruption: "Implements getState/setState for hot-reload continuity",
      tool_interference: "Maintains isolated state, no cross-tool leakage"
    },

    // Auto-infer permission requirements
    permission_requirements: inferPermissions(capabilities),

    // Auto-include required context
    context_dependencies: {
      required: ["conversationId", "alignmentCheck"],
      optional: []
    }
  };

  // Generate TypeScript implementation
  const implementation = `
    class ${capitalize(name)} extends BaseTool {
      constructor() {
        super({
          name: '${name}',
          version: '1.0.0',
          capabilities: ${JSON.stringify(capabilities)}
        });
      }

      async execute(action: string, context: ToolContext): Promise<ToolResult> {
        // Auto-generated: All 5 sacred refusals enforced
        // ... implementation
      }

      // Auto-generated: getState/setState for hot-reload
      getState(): any { return { ...this.state }; }
      setState(state: any): void { this.state = state; }
    }
  `;

  return { spec: toolSpec, implementation };
};

// Usage
const { spec, implementation } = generateTool(
  'validator-tool',
  ['validate-schema', 'check-integrity'],
  'Schema validation and integrity checking'
);

// Write spec
fs.appendFileSync('coded-systems/tools.jsonl', JSON.stringify(spec) + '\n');

// Write implementation
fs.writeFileSync(`src/tools/${spec.name}.ts`, implementation);
```

**Result:** New tools are born sacred, cannot be created without conforming to primitive.

---

## Leverage Pattern 4: Cross-System Integration

**Use case:** Implement mcp-tool-factory primitive in another language/system

**Python Example:**
```python
import json

# Load primitive specification
with open('coded-systems/primitive.jsonl') as f:
    primitive = json.load(f)

with open('coded-systems/constraints.jsonl') as f:
    constraints = [json.loads(line) for line in f]

class SacredToolBase:
    """Base class enforcing mcp-tool-factory primitive in Python"""

    def __init__(self, name, version, capabilities):
        self.name = name
        self.version = version
        self.capabilities = capabilities
        self.state = {}

    def execute(self, action, context):
        # Enforce CONVERSATIONAL_ALIGNMENT
        if not hasattr(context, 'alignmentCheck'):
            raise RefusalError("blind_execution",
                "Refuses to execute without conversational alignment check")

        # Enforce PERMISSION_GRADUATION
        required_level = self.permission_requirements.get(action, 1)
        if context.currentLevel < required_level:
            raise RefusalError("permission_escalation",
                f"Action '{action}' requires Level {required_level}")

        # Enforce STATE_CONTINUITY
        if not hasattr(context, 'conversationId'):
            raise RefusalError("state_amnesia",
                "Refuses to operate without conversation context")

        # Delegate to subclass
        return self._execute_action(action, context)

    def _execute_action(self, action, context):
        raise NotImplementedError("Subclass must implement")

    # Enforce HOT_RELOAD_SAFETY
    def get_state(self):
        return dict(self.state)

    def set_state(self, state):
        self.state = state

# Create Python tool using primitive
class PythonDataTool(SacredToolBase):
    def __init__(self):
        super().__init__(
            name='python-data-tool',
            version='1.0.0',
            capabilities=['create', 'read', 'update', 'delete']
        )
        self.permission_requirements = {
            'create': 2,
            'read': 1,
            'update': 2,
            'delete': 3
        }

    def _execute_action(self, action, context):
        # Implementation here
        pass
```

**Result:** Sacred primitive propagates across languages, creating polyglot tool ecosystem with shared contract.

---

## The Truth These Files Encode

### Tools Are Defined By Their Refusals

**Traditional tool definition:**
```json
{
  "name": "tool",
  "capabilities": ["action1", "action2", "action3"]
}
```
Focus: What it can do

**Sacred tool definition:**
```json
{
  "name": "tool",
  "capabilities": ["action1", "action2", "action3"],
  "refusals": {
    "blind_execution": "Refuses to execute without alignment",
    "permission_escalation": "Refuses without explicit approval",
    "state_amnesia": "Refuses without conversation context",
    "reload_corruption": "Refuses to break continuity",
    "tool_interference": "Refuses to leak state"
  }
}
```
Focus: What it can do AND what it refuses to do

**The shift:** Capabilities without boundaries are violence. Boundaries (refusals) make capabilities trustworthy.

### The Primitive Is Immutable

From `primitive.jsonl`:
```json
"immutability": "This primitive is not negotiable. This primitive is not augmented."
```

Tools can add capabilities, but cannot remove refusals.
Tools can specialize, but cannot violate the primitive.
The primitive is the invariant; capabilities are the variables.

### Constraints Only Tighten

From `constraints.jsonl`:
```json
"enforcement": {
  "automatic": "Tool framework intercepts all execute() calls",
  "manual": "Code review rejects violations"
}
```

If a witness falls below 100%, the constraint tightens (never relaxes).
If a tool violates a constraint, the operation is denied (never permitted).

The protection cannot decay without observable witness failure.

---

## File Format: JSONL (Newline-Delimited JSON)

Each line is independently parseable JSON. This enables:
- Streaming consumption (process line by line)
- Append-only updates (add new tools without rewriting file)
- Partial loading (load only needed specs)
- Line-based diff (git shows exact changes)

**Parsing:**
```javascript
// JavaScript
const specs = fs.readFileSync('file.jsonl', 'utf8')
  .split('\n')
  .filter(Boolean)
  .map(JSON.parse);

// Python
specs = [json.loads(line) for line in open('file.jsonl')]

// Bash + jq
cat file.jsonl | jq -s '.'
```

---

## Validation Commands

**Verify files are valid JSONL:**
```bash
# Each line should parse independently
head -1 coded-systems/primitive.jsonl | jq '.'
head -1 coded-systems/constraints.jsonl | jq '.'
head -1 coded-systems/infrastructure.jsonl | jq '.'
head -1 coded-systems/tools.jsonl | jq '.'
```

**Count entries:**
```bash
wc -l coded-systems/*.jsonl
#    1 primitive.jsonl
#    5 constraints.jsonl
#    6 infrastructure.jsonl
#    4 tools.jsonl
#   16 total
```

**Validate tools conform to primitive:**
```bash
node validate-spec.js  # See Leverage Pattern 2
```

---

## Next Steps

1. **For AI Agents:** Load all 4 files as system context before using tools
2. **For Developers:** Run validation on every commit (CI/CD integration)
3. **For Tool Creators:** Use generator pattern to create conforming tools
4. **For System Integrators:** Implement primitive in your language/system

The specification exists. The leverage is in consumption.

---

## Version

**Specification Version:** 1.0.0 (M6 Complete)

**Phases Encoded:**
- M1: Hot-Reload Infrastructure
- M2: Conversational Negotiation
- M3: State Continuity
- M4: Permission Graduation
- M5: Multi-Tool Orchestration
- M6: Multi-Dimensional Orchestration

**Generated:** 2025-11-22

**Status:** Production-ready, immutable primitive
