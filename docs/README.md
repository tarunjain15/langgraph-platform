# LangGraph Platform Documentation

Welcome to the LangGraph Platform documentation. This platform provides a complete runtime for rapid experimentation and hosting of LangGraph workflows.

## Quick Links

### Getting Started
- [Configuration Guide](configuration.md) - **NEW** Environment configuration, settings, and best practices
- [Workflow Templates](../templates/README.md) - Quick-start templates for common patterns

### Core Features
- **R1: CLI Runtime** - `lgp run` and `lgp serve` commands with hot reload
- **R2: API Server** - RESTful API for workflow execution (hosted mode)
- **R3: Observability** - Langfuse integration for trace analysis
- **R4: State Persistence** - Async checkpointer with SQLite/PostgreSQL
- **R5: Claude Code Nodes** - Stateful agents with repository isolation
- **R6: Workflow Templates** - Rapid workflow creation (`lgp create`)
- **R6.5: Configuration System** - YAML-based environment configs ([Guide](configuration.md))

## Platform Architecture

```
langgraph-platform/
├── cli/              # CLI commands (run, serve, create, templates)
├── runtime/          # Workflow execution engine
├── api/              # REST API server (hosted mode)
├── lgp/              # Core platform modules
│   ├── claude_code/  # Claude Code integration (R5)
│   ├── checkpointing/# State persistence (R4)
│   ├── observability/# Langfuse tracing (R3)
│   └── config/       # Configuration loader (R6.5)
├── config/           # Environment configuration files
│   ├── experiment.yaml  # Local development settings
│   └── hosted.yaml      # Production settings
├── workflows/        # Your workflow definitions
├── templates/        # Workflow templates
└── docs/             # Documentation (you are here)
```

## Usage Examples

### Run a Workflow (Experiment Mode)

```bash
# Execute workflow once
lgp run workflows/my_workflow.py

# With hot reload
lgp run workflows/my_workflow.py --watch

# With verbose logging
lgp run workflows/my_workflow.py --verbose
```

### Serve as API (Hosted Mode)

```bash
# Start API server
lgp serve workflows/my_workflow.py

# Custom port
lgp serve workflows/my_workflow.py --port 8001
```

### Create from Template

```bash
# List available templates
lgp templates

# Create basic workflow
lgp create my_workflow --template basic

# Create multi-agent workflow
lgp create research_pipeline --template multi_agent

# Create Claude Code workflow
lgp create agent_workflow --template with_claude_code
```

## Configuration

The platform uses YAML configuration files for environment-specific settings:

- **`config/experiment.yaml`** - Local development (sqlite, console logs)
- **`config/hosted.yaml`** - Production (postgresql, Langfuse, auth)

See the [Configuration Guide](configuration.md) for complete details.

### Quick Config Changes

**Enable Langfuse Tracing:**
```yaml
# config/experiment.yaml
observability:
  langfuse: true  # Change from false
```

**Use PostgreSQL:**
```yaml
# config/experiment.yaml
checkpointer:
  type: postgresql  # Change from sqlite
  url: ${DATABASE_URL}
```

**Enable Verbose Logs:**
```yaml
# config/experiment.yaml
runtime:
  verbose: true  # Change from false
```

## Environment Variables

Create a `.env` file for secrets:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

# API Authentication
API_KEY=your-secret-api-key

# Langfuse Observability
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

## Workflow Development

### 1. Create from Template

```bash
lgp create my_workflow --template basic
```

### 2. Edit Workflow

Look for `← CUSTOMIZE` comments in `workflows/my_workflow.py`:

```python
class WorkflowState(TypedDict):
    input: str      # ← CUSTOMIZE: Add your fields
    output: str
```

### 3. Test Locally

```bash
lgp run workflows/my_workflow.py --watch
```

### 4. Deploy to Production

```bash
lgp serve workflows/my_workflow.py
# API available at http://localhost:8000
```

## Feature Highlights

### Claude Code Integration (R5)

Stateful Claude Code agents with repository isolation:

```python
# workflows/claude_code_workflow.py
claude_code_config = {
    "enabled": True,
    "agents": [
        {
            "role_name": "researcher",
            "repository": "sample-app",
            "timeout": 60000
        }
    ]
}
```

Session IDs persist via R4 checkpointer for conversation continuity.

### State Persistence (R4)

Async checkpointer with SQLite (dev) or PostgreSQL (prod):

```yaml
# config/experiment.yaml
checkpointer:
  type: sqlite
  path: ./checkpoints.db
  async: true
```

Enables resumable workflows and session continuity.

### Observability (R3)

Langfuse integration for trace analysis:

```yaml
# config/hosted.yaml
observability:
  langfuse: true
```

All workflow executions automatically traced with metadata and tags.

## Troubleshooting

### Config File Not Found

```bash
# Check config files exist
ls config/
# Should show: experiment.yaml, hosted.yaml
```

See [Configuration Guide](configuration.md#troubleshooting) for details.

### Hot Reload Not Working

Ensure `hot_reload: true` in `config/experiment.yaml`:

```yaml
runtime:
  hot_reload: true
```

### Langfuse Not Tracing

1. Enable in config: `observability.langfuse: true`
2. Add credentials to `.env`:
```bash
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
```

## Documentation Status

| Document | Status | Description |
|----------|--------|-------------|
| [Configuration Guide](configuration.md) | ✅ Complete | Environment configuration and settings |
| [Workflow Templates](../templates/README.md) | ✅ Complete | Quick-start templates |
| Observability Guide | 🚧 Coming Soon | Langfuse integration details |
| API Reference | 🚧 Coming Soon | REST API endpoints |
| Deployment Guide | 🚧 Coming Soon | Production deployment (R7) |
| Development Guide | 🚧 Coming Soon | Contributing and extending |

## Getting Help

- **Issues:** Report bugs or request features on GitHub
- **Examples:** See `workflows/` directory for reference implementations
- **Templates:** Use `lgp templates` to see available starting points

## Next Steps

1. Read the [Configuration Guide](configuration.md) to understand settings
2. Create your first workflow: `lgp create my_workflow --template basic`
3. Enable observability for production: See [Configuration Guide](configuration.md#enable-langfuse-tracing-in-development)

---

**Version:** 0.1.0 (R6.5 Complete)
**Last Updated:** 2025-11-19
