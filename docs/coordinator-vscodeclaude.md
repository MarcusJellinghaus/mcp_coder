# VSCodeClaude

The `vscodeclaude launch` command automates multi-issue workspace management by launching VS Code sessions for GitHub issues that need human review.

## Quick Start

```bash
mcp-coder vscodeclaude launch
```

This will:

1. Scan configured repositories for issues requiring human action that are assigned to you (see [Issue Selection](#issue-selection))
2. Clone/update repositories into workspace folders
3. Launch VS Code with automated Claude Code sessions

## Prerequisites

### 1. Trust the Workspace Folder (One-time Setup)

Before using vscodeclaude, you need to trust the workspace base folder in VS Code. This prevents trust prompts for each new session:

1. Open VS Code
2. Go to **File → Open Folder**
3. Select your workspace base folder as defined in the config file  `~/.mcp_coder/config.toml`.
4. Click **"Yes, I trust the authors"** when prompted
5. Close VS Code

After this one-time setup, all session folders created under this directory will be automatically trusted.

### 2. Configuration

Ensure your `~/.mcp_coder/config.toml` has the vscodeclaude section:

```toml
[vscodeclaude]
workspace_base = "C:\\Users\\YourName\\Documents\\your_prefered_folder"  # Windows
# workspace_base = "/home/yourname/your_prefered_folder"        # Linux
max_sessions = 3
```

### 3. Repository Setup

Each repository needs a `.mcp.json` file for Claude Code integration. See [repository-setup/README.md](repository-setup/README.md) for details.

## Usage

### Basic Usage

```bash
# Process all configured repositories
mcp-coder vscodeclaude launch

# Process a specific repository only
mcp-coder vscodeclaude launch --repo mcp_coder

# Check session status
mcp-coder vscodeclaude status

# Explain each session's detection signals and decision (read-only)
mcp-coder vscodeclaude status --explain

# Clean up stale sessions
mcp-coder vscodeclaude launch --cleanup

# Enable debug logging
mcp-coder --log-level debug vscodeclaude launch
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

#### `status` Options

| Option | Description |
|--------|-------------|
| `--repo NAME` | Filter to specific repository only |
| `--explain` | Dump the full detection signals and decision per session (read-only; no writes) |

## How It Works

### Issue Selection

The coordinator looks for issues with these status labels (in priority order):

1. `status-07:code-review` - Code review needed
2. `status-04:plan-review` - Plan review needed  
3. `status-01:created` - New issue needs analysis

Issues must also:

- Be assigned to the GitHub user that your token authenticates as (`[github] token` or `GITHUB_TOKEN`). Nothing else is configured: assign the issue to yourself, or no session opens.
- Not already have an active session

### PR-health checks for `status-10:pr-created`

`status-10:pr-created` issues never get a session themselves, but on every `coordinator vscodeclaude` run the coordinator checks each one's PR (live GitHub data, no local checkout needed). There is no internal loop — how often this happens depends on how often you run (or schedule) the command. The checks run whether or not a session slot is free. The checks run in a fixed order and at most one acts per poll — the rest are re-checked next poll:

1. **Merge conflict** → `status-71:merge-conflict` (Jenkins runs `fix-conflict`)
2. **Failing CI** → `status-81:failing-ci` (Jenkins runs `fix-ci`)
3. **New review feedback** (unresolved thread, or a changes-requested review / PR comment newer than the last triage; comments whose first line contains ❌ are ignored) → `status-91:pr-review-comments`. Only items from trusted authors (`OWNER`, `MEMBER`, `COLLABORATOR`, or `[github] trusted_commenters`) on a PR whose author is trusted count. Untrusted feedback never escalates: the coordinator prints one line per issue (`untrusted PR feedback from @a — review manually`) and writes nothing to GitHub.

An account that posts PRs or ❌ notes on the owner's behalf (e.g. a Jenkins machine user via `github_credentials_id`) must be `COLLABORATOR` or listed in `[github] trusted_commenters` on the vscodeclaude host — otherwise its ❌ notes are dropped from the status file and its PRs never reach `status-91`.

`status-91` and the escalation labels `status-73`, `74`, `83` and `84` open an interactive session: `/pr_comment_triage` for `91`, `/check_branch_status` for the others. See [PR-health](processes-prompts/processes/71-pr-follow-up.md) for the full label flow.

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
| `.vscodeclaude_start.bat/.sh` | Thin launcher — bootstraps into `python -m mcp_coder.workflows.vscodeclaude.session_setup` (gitignored) |
| `.vscodeclaude_session.json` | Typed session spec consumed by `session_setup` at launch (gitignored) |
| `.vscode/tasks.json` | Auto-run task on folder open |
| `.vscodeclaude_status.txt` | Session status (gitignored) |

### Session Storage

Sessions are tracked in:
- **Windows**: `%USERPROFILE%\.mcp_coder\coordinator_cache\vscodeclaude_sessions.json`
- **Linux**: `~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json`

### GitHub rate limits and caches

`coordinator`, `vscodeclaude launch` and `vscodeclaude status` share one GitHub API budget. On the first rate-limit error they stop all remaining GitHub work, log one line with the reset time (`reset time unknown` for GraphQL and retry errors) and exit 0.

- **Coordinator partial dispatch** is the exception: if the Jenkins job was started but the label update hit the limit, one ERROR names the issue and the command exits non-zero.
- **`vscodeclaude launch`**: cleanup and session bookkeeping still run; restart, PR-health checks and new launches are skipped until the next run.
- **`vscodeclaude status`** (also with `--explain`) prints only the rate-limit line, no table.
- A session whose issue state cannot be fetched is never treated as closed or stale.

Cache files live next to `.issues.json` (same directory, same repo prefix) and are shared by all processes:

| File | Contents |
|------|----------|
| `<repo>.prs.json` | Open PRs and PR-health results |
| `<repo>.branches.json` | Issue → branch lookups |

Workflows that update the final label (`--update-labels`, and always for `fix-conflict`) retry a failed update once after ~30 s, then exit non-zero.

To log every GitHub request, enable `traffic_log` in the [`[github]` config section](configuration/config.md#github).

## Troubleshooting

### Sessions showing "-> Remove"

This means the session folder was deleted but the session is still tracked. Run the main command to clean up:

```bash
mcp-coder vscodeclaude launch
```

### Sessions showing "!! Manual"

The folder has uncommitted changes. Either:
1. Open the folder and commit/push your changes
2. Or discard changes: `cd <folder> && git checkout .`

Then run `mcp-coder vscodeclaude launch --cleanup` to remove the session.

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

### Keyboard focus jumps between session windows (Windows)

With several session windows open, another window can occasionally steal focus while you are typing. The generated session files no longer raise windows in the background - only launching or restarting a session does, which is intended.

Windows that were already open keep their old `.vscode/tasks.json` until they are closed and restarted - sessions pick up the new file on the next restart, there is nothing to migrate.

As a cause-agnostic backstop, tell Windows to flash the taskbar instead of switching focus when a background app asks for the foreground:

1. Open `regedit` and go to `HKEY_CURRENT_USER\Control Panel\Desktop`.
2. Set `ForegroundLockTimeout` (DWORD) to a non-zero value - e.g. `30000` (decimal), i.e. 30 seconds.
3. Reboot; the setting is read at logon.

A value of `0` lets any application take the foreground immediately.

### Trust prompts for each folder

Follow the [one-time trust setup](#1-trust-the-workspace-folder-one-time-setup) above.

## See Also

- [CLI Reference](cli-reference.md) - All mcp-coder commands
- [Repository Setup](repository-setup/README.md) - Configuring repositories for automation
- [Configuration](configuration/config.md) - Full configuration reference
