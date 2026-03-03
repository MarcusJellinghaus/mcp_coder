# MLflow Integration Guide

MLflow integration provides enhanced visibility and analytics for your Claude Code conversations.

## Installation

Install the optional MLflow dependency:

```bash
# With pip (development)
pip install -e ".[mlflow]"

# With uv (development)
uv pip install -e ".[mlflow]"

# From PyPI (when available)
pip install mcp-coder[mlflow]
uv pip install mcp-coder[mlflow]
```

## Configuration

Add MLflow settings to your `config.toml` file:

**Location**: 
- Windows: `%USERPROFILE%\.mcp_coder\config.toml`
- Linux/macOS: `~/.config/mcp_coder/config.toml`

**Recommended (SQLite backend)**:
```toml
[mlflow]
enabled = true
tracking_uri = "sqlite:///~/mlflow_data/mlflow.db"
experiment_name = "mcp-coder-conversations"
```

**Legacy (Filesystem backend - deprecated)**:
```toml
[mlflow]
enabled = true
tracking_uri = "~/mlflow_data"  # ⚠️ Deprecated as of Feb 2026
experiment_name = "mcp-coder-conversations"
```

### Configuration Options

- `enabled` (boolean): Enable/disable MLflow logging
- `tracking_uri` (string): Where to store MLflow data
  - `"sqlite:///~/mlflow_data/mlflow.db"` - **SQLite database (RECOMMENDED)** - Better performance, future-proof
  - `"sqlite:////absolute/path/to/mlflow.db"` - SQLite with absolute path
  - `"~/mlflow_data"` - ⚠️ **DEPRECATED** Local file system (MLflow warns this is deprecated as of Feb 2026)
  - `"/absolute/path/to/mlruns"` - ⚠️ **DEPRECATED** Absolute path filesystem
  - `"http://localhost:5000"` - Remote MLflow server
  - **Note**: 
    - SQLite URIs: Use 3 slashes for relative (`sqlite:///`), 4 slashes for absolute (`sqlite:////`)
    - Filesystem paths are automatically converted to proper file URIs but generate deprecation warnings
- `experiment_name` (string): Name for your experiment group (default: "mcp-coder-conversations")

### Environment Variables (Higher Priority)

- `MLFLOW_TRACKING_URI`: Override tracking_uri setting
- `MLFLOW_EXPERIMENT_NAME`: Override experiment_name setting

### Migrating from Filesystem to SQLite

If you're currently using the filesystem backend and want to migrate to SQLite:

**Option 1: Start Fresh (Simplest)**
1. Update your `config.toml` to use SQLite:
   ```toml
   tracking_uri = "sqlite:///~/mlflow_data/mlflow.db"
   ```
2. Your old data remains in `~/mlflow_data/` (safe to delete after verifying new setup works)

**Option 2: Migrate Existing Data**
Use MLflow's official migration tool:
```bash
# Install migration tool
pip install mlflow[migration]

# Migrate data
mlflow db upgrade sqlite:///~/mlflow_data/mlflow.db

# Copy data from filesystem
mlflow experiments restore --from-directory ~/mlflow_data --to-db sqlite:///~/mlflow_data/mlflow.db
```

For detailed migration guidance, see: https://mlflow.org/docs/latest/self-hosting/migrate-from-file-store

## Usage

### Starting the MLflow UI

**Recommended: Use the provided scripts** (automatically reads your `config.toml`):

**Windows:**
```cmd
tools\start_mlflow.bat
```

**Linux/macOS:**
```bash
./tools/start_mlflow.sh
```

The scripts will:
- Read your tracking URI from `config.toml`
- Create the directory if needed
- Handle platform-specific path formatting
- Start the MLflow UI server

---

**Manual Start (Alternative):**

If you prefer to start MLflow manually:

**SQLite Backend (Recommended):**
```bash
# Linux/macOS
mlflow ui --backend-store-uri sqlite:///~/mlflow_data/mlflow.db

# Windows
mlflow ui --backend-store-uri "sqlite:///C:/Users/YourName/mlflow_data/mlflow.db"
```

**Filesystem Backend (Deprecated):**
```bash
# Linux/macOS - ⚠️ Shows deprecation warning
mlflow ui --backend-store-uri ~/mlflow_data
# Or from the directory
cd ~/mlflow_data
mlflow ui

# Windows - ⚠️ Shows deprecation warning
mlflow ui --backend-store-uri "file:///C:/Users/YourName/mlflow_data"
# Or from the directory
cd %USERPROFILE%\mlflow_data
mlflow ui
```

**Note**: 
- **SQLite is now recommended** - the filesystem backend generates deprecation warnings as of Feb 2026
- The provided scripts (`start_mlflow.sh` / `start_mlflow.bat`) will work with either backend

---

Open http://localhost:5000 in your browser.

### Stopping the MLflow UI

**Windows:**
```cmd
tools\stop_mlflow.bat
```

**Linux/macOS:**
```bash
./tools/stop_mlflow.sh
```

Or press `Ctrl+C` in the terminal where MLflow is running.

### What Gets Logged

**Metrics:**
- Conversation duration (ms)
- Token usage (input/output)  
- Cost (if available)
- Number of turns

**Parameters:**
- Model used
- Provider (Claude)
- Method (CLI/API)
- Working directory
- Branch name

**Artifacts:**
- Full conversation JSON
- Prompt text
- Response text

## Testing the Integration

### Quick Test

Test MLflow logging with a simple prompt:

```bash
mcp-coder --log-level DEBUG prompt "What is 2+2?"
```

**With MLflow enabled and installed**, you'll see DEBUG logs:
```
DEBUG:mcp_coder.llm.mlflow_logger:MLflow is available
DEBUG:mcp_coder.llm.mlflow_logger:Started MLflow run: <run_id>
DEBUG:mcp_coder.llm.mlflow_logger:Logged X parameters to MLflow
DEBUG:mcp_coder.llm.mlflow_logger:Logged X metrics to MLflow
DEBUG:mcp_coder.llm.mlflow_logger:Ended MLflow run: <run_id>
```

**Note**: If using the filesystem backend (`~/mlflow_data`), you may see a FutureWarning:
```
FutureWarning: The filesystem tracking backend (e.g., './mlruns') is deprecated as of February 2026.
Consider transitioning to a database backend (e.g., 'sqlite:///mlflow.db')
```
This is harmless but indicates you should migrate to SQLite (see "Migrating from Filesystem to SQLite" section above).

**Without MLflow installed**, the command works normally (graceful fallback):
```
DEBUG:mcp_coder.llm.mlflow_logger:MLflow is not installed
```

### Verify in MLflow UI

1. Start the MLflow UI (if not already running):
   ```bash
   # Windows
   tools\start_mlflow.bat
   
   # Linux/macOS
   ./tools/start_mlflow.sh
   ```

2. Open http://localhost:5000 in your browser

3. Run test commands:
   ```bash
   mcp-coder prompt "Hello Claude, testing MLflow!"
   mcp-coder prompt "Explain MLflow in one sentence"
   ```

4. In the MLflow UI, you should see:
   - New runs in the "mcp-coder-conversations" experiment
   - Metrics: `duration_ms`, `cost_usd`, `usage_input_tokens`, `usage_output_tokens`
   - Parameters: `model`, `provider`, `branch_name`, `working_directory`
   - Artifacts: Click on a run → "Artifacts" tab → `prompt.txt`, `conversation.json`

### Test Session Continuation

Test that MLflow logs multi-turn conversations:

```bash
# First turn
mcp-coder prompt "What is 2+2?" --store-response

# Continue the conversation
mcp-coder prompt "Now multiply that by 3" --continue-session
```

Both turns should be logged as separate MLflow runs with the same session context.

### Test Without MLflow (Graceful Fallback)

Verify that mcp-coder works without MLflow:

1. Temporarily disable MLflow in `config.toml`:
   ```toml
   [mlflow]
   enabled = false
   ```

2. Run the same test:
   ```bash
   mcp-coder --log-level DEBUG prompt "What is 2+2?"
   ```

3. The command should succeed without any MLflow logging.

4. Re-enable MLflow:
   ```toml
   [mlflow]
   enabled = true
   ```

## Benefits

1. **Visibility**: See all your conversations in one place
2. **Analytics**: Track usage patterns and costs over time
3. **Comparison**: Compare different prompting approaches
4. **Search**: Find specific conversations by content or metadata
5. **History**: Keep long-term conversation history

## Troubleshooting

### MLflow not installed
```
ImportError: No module named 'mlflow'
```
Install with: `pip install -e ".[mlflow]"`

### Permission errors
Ensure the tracking_uri directory is writable:
```bash
mkdir -p /path/to/mlruns
chmod 755 /path/to/mlruns
```

### UI not accessible
Check if port 5000 is available:
```bash
mlflow ui --port 5001
```