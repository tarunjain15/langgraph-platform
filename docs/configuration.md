# Configuration Guide

LangGraph Platform uses YAML-based configuration files for environment-specific settings.

## Quick Start

### 1. Configuration Files

Two configuration files control platform behavior:

- **`config/experiment.yaml`** - Local development and experimentation
- **`config/hosted.yaml`** - Production API server

### 2. Basic Usage

Configuration is automatically loaded based on the command you use:

```bash
# Uses config/experiment.yaml
lgp run workflows/my_workflow.py

# Uses config/hosted.yaml
lgp serve workflows/my_workflow.py
```

No code changes needed - the platform automatically loads the right config.

---

## Configuration Structure

### Experiment Configuration (`config/experiment.yaml`)

```yaml
# State Persistence (R4)
checkpointer:
  type: sqlite                    # sqlite or postgresql
  path: ./checkpoints.db          # SQLite database path
  async: true                     # Use async checkpointer

# Observability (R3)
observability:
  console: true                   # Print logs to console
  langfuse: false                 # Disable Langfuse tracing in dev
  # To enable Langfuse:
  # 1. Set langfuse: true
  # 2. Add LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY to .env

# Runtime Settings (R1)
runtime:
  hot_reload: true                # Enable file watching and auto-reload
  verbose: false                  # Show detailed execution logs

# Feature Flags
features:
  claude_code: true               # Enable Claude Code node support (R5)
  templates: true                 # Enable workflow templates (R6)
```

### Hosted Configuration (`config/hosted.yaml`)

```yaml
# State Persistence (R4)
checkpointer:
  type: postgresql                # postgresql for production
  url: ${DATABASE_URL}            # Read from .env
  pool_size: 10                   # Connection pool size
  pool_timeout: 30                # Connection timeout (seconds)

# Observability (R3)
observability:
  console: false                  # Disable console logs in production
  langfuse: true                  # Enable Langfuse tracing
  # Required .env variables:
  # - LANGFUSE_SECRET_KEY
  # - LANGFUSE_PUBLIC_KEY
  # - LANGFUSE_BASE_URL (optional)

# Server Settings (R2)
server:
  workers: 4                      # Number of worker processes
  timeout: 300                    # Request timeout (seconds)
  max_requests: 1000              # Max requests per worker before restart

# Authentication (R2)
auth:
  enabled: true                   # Require API key authentication
  api_key: ${API_KEY}             # Read from .env

# Feature Flags
features:
  claude_code: true               # Enable Claude Code node support
  templates: true                 # Enable workflow templates
  rate_limiting: true             # Enable rate limiting
  auto_scaling: false             # Auto-scaling (not implemented)
```

---

## Environment Variables

### Using Environment Variables in Config

Reference environment variables using `${VAR_NAME}` syntax:

```yaml
checkpointer:
  url: ${DATABASE_URL}            # Required, no default

auth:
  api_key: ${API_KEY:default}     # Optional, with default value
```

### Setting Environment Variables

Create a `.env` file in the project root:

```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
API_KEY=your-secret-api-key
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
```

The platform automatically loads `.env` variables.

---

## Common Configurations

### Enable Langfuse Tracing in Development

Edit `config/experiment.yaml`:

```yaml
observability:
  console: true
  langfuse: true              # Change from false to true
```

Add credentials to `.env`:

```bash
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com  # optional
```

### Use PostgreSQL for Local Development

Edit `config/experiment.yaml`:

```yaml
checkpointer:
  type: postgresql            # Change from sqlite
  url: ${DATABASE_URL}        # Reference .env variable
  pool_size: 5
```

Add to `.env`:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dev_db
```

### Enable Verbose Logging

Edit `config/experiment.yaml`:

```yaml
runtime:
  verbose: true               # Change from false
```

### Disable Claude Code Support

Edit `config/experiment.yaml`:

```yaml
features:
  claude_code: false          # Change from true
```

---

## Advanced Usage

### Programmatic Config Access

Access configuration in your code:

```python
from lgp.config import load_config

# Load experiment config
config = load_config("experiment")

# Access settings
db_type = config["checkpointer"]["type"]
langfuse_enabled = config["observability"]["langfuse"]

# Check feature flags
if config.get("features", {}).get("claude_code", False):
    print("Claude Code enabled")
```

### Config Validation

The platform validates configuration on load:

```python
from lgp.config import load_config

try:
    config = load_config("experiment")
except ValueError as e:
    print(f"Invalid config: {e}")
except FileNotFoundError as e:
    print(f"Config file missing: {e}")
```

**Required Fields:**
- `checkpointer` (with `type` field)
- `observability` (with `console` and `langfuse` fields)

**Valid Checkpointer Types:**
- `sqlite`
- `postgresql`

### Custom Configuration

Add custom sections to config files:

```yaml
# config/experiment.yaml

# Your custom settings
custom:
  api_rate_limit: 100
  batch_size: 32
  cache_ttl: 3600
```

Access in code:

```python
config = load_config("experiment")
rate_limit = config.get("custom", {}).get("api_rate_limit", 50)
```

---

## Configuration Reference

### Checkpointer

Controls state persistence (R4):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Database type: `sqlite` or `postgresql` |
| `path` | string | If sqlite | Path to SQLite database file |
| `url` | string | If postgresql | PostgreSQL connection URL |
| `async` | boolean | No | Use async checkpointer (default: true) |
| `pool_size` | integer | No | Connection pool size (postgresql) |
| `pool_timeout` | integer | No | Connection timeout in seconds |

### Observability

Controls logging and tracing (R3):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `console` | boolean | Yes | Print logs to console |
| `langfuse` | boolean | Yes | Enable Langfuse tracing |

**Environment Variables for Langfuse:**
- `LANGFUSE_SECRET_KEY` - Required
- `LANGFUSE_PUBLIC_KEY` - Required
- `LANGFUSE_BASE_URL` - Optional (defaults to cloud.langfuse.com)

### Runtime

Controls execution behavior (R1):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hot_reload` | boolean | No | Enable file watching (experiment mode) |
| `verbose` | boolean | No | Show detailed execution logs |

### Server

Controls API server (R2):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workers` | integer | No | Number of worker processes |
| `timeout` | integer | No | Request timeout in seconds |
| `max_requests` | integer | No | Max requests per worker |

### Authentication

Controls API authentication (R2):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | No | Require API key authentication |
| `api_key` | string | If enabled | API key (use ${API_KEY}) |

### Features

Feature flags for optional capabilities:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `claude_code` | boolean | true | Enable Claude Code nodes (R5) |
| `templates` | boolean | true | Enable workflow templates (R6) |
| `rate_limiting` | boolean | false | Enable API rate limiting |
| `auto_scaling` | boolean | false | Enable auto-scaling (R7) |

---

## Troubleshooting

### Config File Not Found

**Error:**
```
FileNotFoundError: Config file not found: /path/to/config/experiment.yaml
```

**Solution:**
Check that config files exist:
```bash
ls -la config/
# Should show: experiment.yaml, hosted.yaml
```

If missing, they should be in the repository. Check git status.

### Invalid Config Structure

**Error:**
```
ValueError: Missing required config key: checkpointer in config/experiment.yaml
```

**Solution:**
Ensure config file has all required sections:
```yaml
checkpointer:  # Required
  type: sqlite
observability: # Required
  console: true
  langfuse: false
```

### Environment Variable Not Substituted

**Symptom:**
Config shows `${DATABASE_URL}` instead of actual URL.

**Solution:**
1. Check `.env` file exists in project root
2. Verify variable name matches exactly
3. Restart the server/command

### Legacy Mode Warning

**Warning:**
```
[lgp] Warning: Config file not found
[lgp] Using hardcoded configuration (legacy mode)
```

**Solution:**
This is a backward compatibility fallback. Create proper config files to use YAML configuration.

---

## Best Practices

### 1. Use Environment Variables for Secrets

**Bad:**
```yaml
auth:
  api_key: "my-secret-key-123"  # Don't hardcode secrets!
```

**Good:**
```yaml
auth:
  api_key: ${API_KEY}           # Reference .env variable
```

### 2. Document Custom Settings

Add comments to explain non-obvious settings:

```yaml
checkpointer:
  type: postgresql
  pool_size: 10                 # Tuned for 4 workers × 2.5 connections
  pool_timeout: 30              # Balance between wait time and failure
```

### 3. Use Feature Flags

Enable/disable features without code changes:

```yaml
features:
  claude_code: true             # Enable in production
  new_feature: false            # Disable while testing
```

### 4. Different Configs Per Environment

Maintain separate configs:
- `experiment.yaml` - Fast iteration, sqlite, console logs
- `hosted.yaml` - Production-ready, postgresql, Langfuse

### 5. Version Control Config Files

Commit config files to git:
```bash
git add config/experiment.yaml config/hosted.yaml
git commit -m "Update config: enable new feature"
```

**Don't commit** `.env` file (contains secrets).

---

## Migration from Hardcoded Config

If you have an older version with hardcoded configuration:

### Step 1: Check Current Behavior

```bash
lgp run workflows/my_workflow.py
```

Look for warning:
```
[lgp] Warning: Config file not found
[lgp] Using hardcoded configuration (legacy mode)
```

### Step 2: Create Config Files

Copy from templates:
```bash
# Config files should already exist in config/
ls config/experiment.yaml config/hosted.yaml
```

### Step 3: Verify New Config Works

```bash
lgp run workflows/my_workflow.py
# Should NOT show legacy mode warning
```

### Step 4: Customize Settings

Edit `config/experiment.yaml` and `config/hosted.yaml` to match your needs.

---

## See Also

- [Workflow Templates](../templates/README.md) - Quick-start workflow patterns
- [Observability Guide](observability.md) - Langfuse integration (coming soon)
- [Deployment Guide](deployment.md) - Production deployment (coming soon)
- [API Reference](api-reference.md) - API server configuration (coming soon)
