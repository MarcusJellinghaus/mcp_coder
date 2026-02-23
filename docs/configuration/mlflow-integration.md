# MLflow Integration Guide

MLflow integration provides enhanced visibility and analytics for your Claude Code conversations.

## Installation

Install the optional MLflow dependency:

```bash
# For development
pip install -e ".[mlflow]"

# Or from PyPI (when available)
pip install mcp-coder[mlflow]
```

## Configuration

Add MLflow settings to your `config.toml` file:

**Location**: 
- Windows: `%USERPROFILE%\.mcp_coder\config.toml`
- Linux/macOS: `~/.config/mcp_coder/config.toml`

```toml
[mlflow]
enabled = true
tracking_uri = "file:///path/to/mlruns"
experiment_name = "claude-conversations"
```

### Configuration Options

- `enabled` (boolean): Enable/disable MLflow logging
- `tracking_uri` (string): Where to store MLflow data
  - `"file:///path/to/mlruns"` - Local file system
  - `"http://localhost:5000"` - Remote MLflow server
  - `"sqlite:///mlflow.db"` - SQLite database
- `experiment_name` (string): Name for your experiment group

### Environment Variables (Higher Priority)

- `MLFLOW_TRACKING_URI`: Override tracking_uri setting
- `MLFLOW_EXPERIMENT_NAME`: Override experiment_name setting

## Usage

### Starting the MLflow UI

```bash
# In your project directory
mlflow ui

# Or specify custom tracking URI
mlflow ui --backend-store-uri file:///path/to/mlruns
```

Open http://localhost:5000 in your browser.

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