# LangGraph Platform

A workflow runtime for rapid experimentation and hosting of LangGraph workflows.

## Status

✅ **Parked at R9** (90% Complete) - Production-ready with PostgreSQL + graceful degradation

**Completed**: R1-R6, R6.5, R8, R9 (9/10 phases)
**Pending**: R7 (Production Mastery - optional deployment automation)

See `flow-pressure/04-current-state.md` for real-time status.

## Project Structure

```
langgraph-platform/
├── flow-pressure/              # Platform runtime knowledge layer
│   ├── 01-the-project.md      # Runtime primitive (ETERNAL)
│   ├── 02-the-discipline.md   # Runtime constraints (ETERNAL)
│   ├── 03-implementation-plan.md  # R1-R9 phases (STRUCTURAL)
│   └── 04-current-state.md    # Runtime execution state (VOLATILE)
│
├── research/                   # Foundational research verticals
│   └── checkpoint-mastery/    # Checkpoint database optimization research
│       ├── flow-pressure/     # Checkpoint research knowledge layer (M1-M7)
│       ├── crystallised-understanding/  # Deep technical insights
│       └── README.md          # Bridge: research → platform relationship
│
├── lgp/                        # Platform implementation
│   ├── agents/                # Multi-provider agents (Claude Code, Ollama)
│   ├── checkpointing/         # Multi-backend checkpointer (SQLite, PostgreSQL)
│   ├── claude_code/           # Claude Code MCP integration
│   ├── config/                # Configuration loader
│   └── observability/         # Langfuse tracing, sanitization
│
├── runtime/                    # Workflow execution engine
├── cli/                        # Command-line interface
├── api/                        # HTTP API (hosted mode)
├── workflows/                  # Example workflows
├── config/                     # Environment configs (experiment.yaml, hosted.yaml)
└── templates/                  # Workflow templates (basic, multi_agent, with_claude_code)
```

## Sacred Primitive

```
Workflow Runtime = Environment-isolated execution engine for LangGraph graphs
```

**What This Means:**
- Workflows are **data** (Python files loaded by runtime)
- Environments are **boundaries** (experiment vs hosted)
- Execution is **isolated** (hot reload, observability, checkpointing injected)

## Research Verticals

This platform builds upon **foundational research** that explores complete optimization paths:

### Checkpoint Mastery (`research/checkpoint-mastery/`)
- **What**: Complete checkpoint database evolution (SQLite → PostgreSQL → Redis → auto-scaling)
- **Status**: Paused at M2 (10/28 tasks complete)
- **Platform Adoption**:
  - R4 implements M1 patterns (SQLite foundation)
  - R9 implements M4 patterns (PostgreSQL at 90%)
  - M5-M7 available when needed (connection pooling, cross-thread memory, tiered storage)
- **See**: `research/checkpoint-mastery/README.md` for complete research status

## Platform Phases (R1-R9)

| Phase | Status | Description |
|-------|--------|-------------|
| **R1** | ✅ Complete | CLI Runtime - `lgp run` with hot reload (experiment mode) |
| **R2** | ✅ Complete | API Runtime - `lgp serve` with REST API (hosted mode) |
| **R3** | ✅ Complete | Observability - Langfuse integration, output sanitization |
| **R4** | ✅ Complete | Checkpointer Management - SQLite for single-server |
| **R5** | ✅ Complete | Claude Code Nodes - Stateful agents via MCP |
| **R6** | ✅ Complete | Workflow Templates - `lgp create` with 3 templates |
| **R6.5** | ✅ Complete | Configuration Infrastructure - Externalized YAML configs |
| **R8** | ✅ Complete | Multi-Provider Agency - Ollama integration ($0 cost workflows) |
| **R9** | ✅ 90% | PostgreSQL Checkpointer - Multi-server with retry + fallback |
| **R7** | 🟡 Optional | Production Mastery - Auto-deployment, self-healing (deferred) |

## Installation

```bash
# Clone repository
cd /Users/tarun/claude-workspace/workspace/langgraph-platform

# Install dependencies (once R1 is complete)
poetry install

# Run CLI
lgp --help
```

## Documentation

- **01-the-project.md** - System identity, phases, entities (ETERNAL + STRUCTURAL)
- **02-the-discipline.md** - 5 sacred constraints, witness protocol (ETERNAL + LEARNED)
- **03-implementation-plan.md** - 26 tasks with witnesses (STRUCTURAL)
- **04-current-state.md** - Real-time progress (VOLATILE)

## License

MIT

## Related Projects

- [langgraph-checkpoint-mastery](https://github.com/tarunjain15/langgraph-checkpoint-mastery) - Checkpoint patterns (M1-M2)
- [langfuse-langgraph-demo](https://github.com/tarunjain15/langfuse-langgraph-demo) - Observability + Claude Code integration
- [my-langgraph](https://github.com/tarunjain15/my-langgraph) - Knowledge layer framework

---

**Generated with knowledge-layer discipline** - See `flow-pressure/templates/00-knowledge-layers.md`
