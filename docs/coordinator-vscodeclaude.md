# Coordinator VSCodeClaude

The `coordinator vscodeclaude` command automates multi-issue workspace management by launching VS Code sessions for GitHub issues that need human review.

## Quick Start

```bash
mcp-coder coordinator vscodeclaude
```

This will:

1. Scan configured repositories for issues requiring human action
2. Clone/update repositories into workspace folders
3. Launch VS Code with automated Claude Code sessions

## Prerequisites

### 1. Trust the Workspace Folder (One-time Setup)

Before using vscodeclaude, you need to trust the workspace base folder in VS Code. This prevents trust prompts for each new session:

1. Open VS Code
2. Go to **File → Open Folder**
3. Select your workspace base folder as defined in the config file  `~/.config/mcp_coder/config.toml`.
4. Click **"Yes, I trust the authors"** when prompted
5. Close VS Code

After this one-time setup, all session folders created under this directory will be automatically trusted.

### 2. Configuration

Ensure your `~/.config/mcp_coder/config.toml` has the vscodeclaude section:

```toml
[vscodeclaude]
workspace_base = "C:\\Users\\YourName\\Documents\\your_prefered_folder"  # Windows
# workspace_base = "/home/yourname/your_prefered_folder"        # Linux
max_sessions = 3
```

### 3. Repository Setup

Each repository needs a `.mcp.json` file for Claude Code integration. See [repository-setup.md](repository-setup.md) for details.

## Usage

### Basic Usage

```bash
# Process all configured repositories
mcp-coder coordinator vscodeclaude

# Process a specific repository only
mcp-coder coordinator vscodeclaude --repo mcp_coder

# Check session status
mcp-coder coordinator vscodeclaude status

# Clean up stale sessions
mcp-coder coordinator vscodeclaude --cleanup

# Enable debug logging
mcp-coder --log-level debug coordinator vscodeclaude
```

### Options

| Option | Description |
|--------|-------------|
| `--repo NAME` | Filter to specific repository only |
| `--max-sessions N` | Override max concurrent sessions (default: from config or 3) |
| `--cleanup` | Delete stale clean folders (without this, only lists them) |
| `--intervene` | Force open a bot_busy issue for debugging |
| `--issue NUMBER` | Issue number for intervention mode (requires `--intervene`) |

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `status` | Show current session status table |

## How It Works

### Issue Selection

The coordinator looks for issues with these status labels (in priority order):

1. `status-10:pr-created` - PR created (displayed only, no session needed)
2. `status-07:code-review` - Code review needed
3. `status-04:plan-review` - Plan review needed  
4. `status-01:created` - New issue needs analysis

Issues must also:

- Be assigned to the configured GitHub user
- Not already have an active session

### Session Lifecycle

1. **Workspace Setup**: Creates folder like `mcp-coder_123` in workspace base
2. **Git Clone/Pull**: Clones repository or pulls latest changes
3. **Dependency Installation**: Installs complete development environment with `uv sync --extra dev` (includes test utilities, type stubs, and development tools)
4. **VS Code Launch**: Opens workspace with auto-run task
5. **Claude Session**: Starts appropriate Claude Code command based on issue status

### Session States

Sessions can be in different states, shown in the `status` command:

| State | VSCode | Folder | Description | Next Action |
|-------|--------|--------|-------------|-------------|
| Active | Running | Exists | Working normally | `(active)` |
| Closed | Closed | Exists, Clean | VSCode closed, can restart | `-> Restart` |
| Stale | Closed | Exists, Clean | Issue status changed | `-> Delete (with --cleanup)` |
| Dirty | Closed | Has changes | Uncommitted work | `!! Manual` - commit or discard changes |
| Orphaned | Closed | Missing | Folder deleted externally | `-> Remove` |

**Automatic behavior:**
- **Closed sessions** are automatically restarted when you run the main command
- **Orphaned sessions** are automatically removed when you run the main command
- **Stale sessions** require `--cleanup` flag to delete
- **Dirty sessions** require manual intervention (commit or discard changes)

### Generated Files

Each session creates:

| File | Purpose |
|------|---------|
| `<repo>_<issue>.code-workspace` | VS Code workspace file |
| `.vscodeclaude_start.bat/.sh` | Startup script |
| `.vscode/tasks.json` | Auto-run task on folder open |
| `.vscodeclaude_status.txt` | Session status (gitignored) |

### Session Storage

Sessions are tracked in:
- **Windows**: `%USERPROFILE%\.mcp_coder\coordinator_cache\vscodeclaude_sessions.json`
- **Linux**: `~/.config/mcp_coder/coordinator_cache/vscodeclaude_sessions.json`

## Troubleshooting

### Sessions showing "-> Remove"

This means the session folder was deleted but the session is still tracked. Run the main command to clean up:

```bash
mcp-coder coordinator vscodeclaude
```

### Sessions showing "!! Manual"

The folder has uncommitted changes. Either:
1. Open the folder and commit/push your changes
2. Or discard changes: `cd <folder> && git checkout .`

Then run `mcp-coder coordinator vscodeclaude --cleanup` to remove the session.

### "Access is denied" errors on Windows

Git pack files may be read-only. The coordinator automatically handles this, but if issues persist:

- Close any applications that may have the repository open
- Delete the problematic folder manually and retry

### VS Code not launching

Ensure `code` is in your PATH:

```bash
code --version
```

If not, add VS Code to PATH via VS Code: `Ctrl+Shift+P` → "Shell Command: Install 'code' command in PATH"

### Trust prompts for each folder

Follow the [one-time trust setup](#1-trust-the-workspace-folder-one-time-setup) above.

## See Also

- [CLI Reference](cli-reference.md) - All mcp-coder commands
- [Repository Setup](repository-setup.md) - Configuring repositories for automation
- [Configuration](configuration/config.md) - Full configuration reference
