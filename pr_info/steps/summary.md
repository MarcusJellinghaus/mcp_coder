# Issue #570: Restructure CLI Commands

## Summary

Restructure CLI commands for better organization: flatten `coordinator` to a direct command with `--dry-run`, promote `vscodeclaude` to top-level, move `define-labels` and `issue-stats` under `gh-tool`.

**Clean break** — no backward compatibility. Old commands stop working. Old config keys stop working silently.

## Command Migration

| Old Command | New Command |
|---|---|
| `coordinator run` | `coordinator` (direct, default behavior) |
| `coordinator test` | `coordinator --dry-run` |
| `coordinator vscodeclaude` | `vscodeclaude launch` |
| `coordinator vscodeclaude status` | `vscodeclaude status` |
| `coordinator issue-stats` | `gh-tool issue-stats` |
| `define-labels` | `gh-tool define-labels` |

## Config Migration

| Old Key | New Key |
|---|---|
| `coordinator.vscodeclaude.workspace_base` | `vscodeclaude.workspace_base` |
| `coordinator.vscodeclaude.max_sessions` | `vscodeclaude.max_sessions` |

## Architecture / Design Changes

### Before
```
coordinator (subcommand group)
├── test          → triggers Jenkins test for repo/branch
├── run           → monitors issues, dispatches workflows
├── vscodeclaude  → manages VSCode/Claude sessions
│   └── status    → shows session status
└── issue-stats   → displays issue statistics

define-labels     → top-level command, syncs GitHub labels
gh-tool
└── get-base-branch
```

### After
```
coordinator       → direct command (was "coordinator run"), --dry-run (was "coordinator test")
vscodeclaude      → top-level (promoted from coordinator)
├── launch        → was "coordinator vscodeclaude"
└── status        → was "coordinator vscodeclaude status"
gh-tool
├── get-base-branch  → unchanged
├── define-labels    → moved from top-level
└── issue-stats      → moved from coordinator
```

### Key Design Decisions

1. **Re-route, don't rewrite**: Business logic stays in existing modules. Only CLI surface (parsing + routing) changes. No new command module file needed — `main.py` calls existing execute functions directly.

2. **Coordinator flattening**: `coordinator` becomes a direct command like `implement`. `--dry-run` flag replaces the separate `test` subcommand. The `--all`/`--repo` args from `run` become direct args on `coordinator`. The `repo_name`/`--branch-name` args from `test` are added as optional args for `--dry-run` mode.

3. **Config key migration**: `coordinator.vscodeclaude` → top-level `vscodeclaude` section. `coordinator.repos[].setup_commands_*` stays under `coordinator.repos[]` (repo config is shared, not vscodeclaude-specific).

## Files Modified

### CLI Code (Steps 1-4)
- `src/mcp_coder/cli/commands/help.py` — update COMMAND_CATEGORIES
- `src/mcp_coder/cli/parsers.py` — restructure all parser definitions
- `src/mcp_coder/cli/main.py` — update command routing

### Config (Step 5)
- `src/mcp_coder/workflows/vscodeclaude/config.py` — change config key strings
- `src/mcp_coder/utils/user_config.py` — update default config template

### Tests (Steps 1-5, alongside each change)
- `tests/cli/commands/test_help.py`
- `tests/cli/test_main.py`
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`
- `tests/cli/commands/coordinator/test_issue_stats_cli.py`
- `tests/cli/commands/coordinator/test_commands.py`
- `tests/cli/commands/test_gh_tool.py`
- `tests/workflows/vscodeclaude/test_config.py`

### Documentation (Step 6)
- `docs/cli-reference.md`
- `docs/coordinator-vscodeclaude.md`
- `docs/getting-started/label-setup.md`
- `docs/configuration/config.md`

### Slash Commands (Step 6)
- `.claude/commands/*.md` — update any command name references

## No Files Created

The original issue suggested `src/mcp_coder/cli/commands/vscodeclaude.py`, but this is unnecessary — `main.py` routes directly to existing workflow functions, avoiding empty wrapper modules.

## Implementation Steps

| Step | Description | Key Files |
|------|-------------|-----------|
| 1 | Update help categories | `help.py`, `test_help.py` |
| 2 | Flatten coordinator (direct + --dry-run) | `parsers.py`, `main.py`, coordinator tests |
| 3 | Add vscodeclaude top-level command | `parsers.py`, `main.py`, vscodeclaude CLI tests |
| 4 | Move define-labels + issue-stats to gh-tool | `parsers.py`, `main.py`, gh-tool + issue-stats tests |
| 5 | Migrate config keys | `vscodeclaude/config.py`, `user_config.py`, config tests |
| 6 | Update documentation + slash commands | docs/, .claude/commands/ |
