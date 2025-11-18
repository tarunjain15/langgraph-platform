# LangGraph Platform

A workflow runtime for rapid experimentation and hosting of LangGraph workflows.

## Status

🚧 **Initial Setup Complete** - Following knowledge-layer discipline

See `flow-pressure/` for project structure, discipline, and implementation plan.

## Project Structure

```
langgraph-platform/
├── flow-pressure/              # Knowledge layers (eternal + structural)
│   ├── 01-the-project.md      # Sacred primitive + phases
│   ├── 02-the-discipline.md   # Constraints + witnesses
│   ├── 03-implementation-plan.md  # 26 tasks across 7 phases
│   └── 04-current-state.md    # Volatile execution state
│
├── runtime/                    # Workflow execution engine
├── platform/                   # Infrastructure (checkpointing, observability)
├── cli/                        # Command-line interface
├── api/                        # HTTP API (hosted mode)
├── workflows/                  # User workflows (gitignored)
└── templates/                  # Workflow templates
```

## Sacred Primitive

```
Workflow Runtime = Environment-isolated execution engine for LangGraph graphs
```

**What This Means:**
- Workflows are **data** (Python files loaded by runtime)
- Environments are **boundaries** (experiment vs hosted)
- Execution is **isolated** (hot reload, observability, checkpointing injected)

## Current Phase

**Phase:** R1 (CLI Runtime - Experiment Mode)
**Status:** 🟡 NOT STARTED
**Next:** Implement `lgp run <workflow>` with hot reload

See `flow-pressure/04-current-state.md` for real-time progress.

## The 7 Phases

1. **R1: CLI Runtime** - `lgp run` with hot reload (experiment mode)
2. **R2: API Runtime** - `lgp serve` with REST API (hosted mode)
3. **R3: Observability** - Langfuse integration, trace sanitization
4. **R4: PostgreSQL** - Multi-server checkpointing, connection pooling
5. **R5: Claude Code Nodes** - Stateful agent factory, MCP integration
6. **R6: Templates** - `lgp create` with 5+ workflow templates
7. **R7: Production** - `lgp deploy` with auto-scaling, self-healing

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
