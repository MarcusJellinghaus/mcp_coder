# Issue #748: MCP Server Connection Status at Startup + Verify

## Summary

Surface MCP server **connection status** from `claude mcp list` in two places:
1. **iCoder TUI startup** — inline status on existing server lines (`✓ Connected` / `✗ Failed`)
2. **`mcp-coder verify`** — provider-aware MCP sections (active provider first, other "for completeness")

Currently only binary existence is checked (`--version`). Whether Claude Code actually connected to the servers is invisible — errors surface later as cryptic tool failures.

## Architectural / Design Changes

### New Abstractions

| What | Where | Purpose |
|------|-------|---------|
| `ClaudeMCPStatus` dataclass | `utils/mcp_verification.py` | Structured result per server: `name`, `status_text`, `ok` |
| `parse_claude_mcp_list()` function | `utils/mcp_verification.py` | Runs `claude mcp list`, parses output, filters to known servers |
| `_format_claude_mcp_section()` function | `cli/commands/verify.py` | Formats the "MCP SERVERS (via Claude Code)" section |

### Modified Structures

| What | Where | Change |
|------|-------|--------|
| `RuntimeInfo` dataclass | `icoder/env_setup.py` | New optional field `mcp_connection_status: list[ClaudeMCPStatus] \| None = None` |
| `_compute_exit_code()` | `cli/commands/verify.py` | New `claude_mcp_ok: bool \| None = None` parameter (`None`=not checked, `True`=ok, `False`=failure; only `False` triggers exit 1) |
| `execute_verify()` | `cli/commands/verify.py` | Provider-aware dual MCP sections |
| `on_mount()` | `icoder/ui/app.py` | Inline connection status on server lines |
| `execute_icoder()` | `cli/commands/icoder.py` | Include connection status in `session_start` event |

### Design Decisions

- **No `status_icon` field** — UI generates its own symbols via `_get_status_symbols()`. We store `ok` (bool) and `status_text` (str) only.
- **`RuntimeInfo` stays frozen** — new field has `None` default, no breaking change.
- **Graceful fallback everywhere** — if `claude mcp list` fails, `parse_claude_mcp_list` returns `None`. Callers fall back to current behavior.
- **Name mapping** — `claude mcp list` shows `tools-py`/`workspace`; `MCP_SERVER_NAMES` uses `mcp-tools-py`/`mcp-workspace`. Parser prepends `mcp-` prefix.
- **60s timeout** — servers need time for health probes.
- **`env_vars` passed explicitly** — no `os.environ` mutation, consistent with existing pure-function pattern in `setup_icoder_environment()`.
- **Synchronous execution** — matches existing `claude --version` call pattern in startup.

### Data Flow

```
parse_claude_mcp_list(env_vars)
  → runs: claude --mcp-config .mcp.json --strict-mcp-config mcp list
  → parses stdout with regex
  → filters to MCP_SERVER_NAMES
  → returns list[ClaudeMCPStatus] | None

iCoder startup:
  setup_icoder_environment()
    → calls parse_claude_mcp_list(effective)
    → stores in RuntimeInfo.mcp_connection_status
  on_mount()
    → reads RuntimeInfo.mcp_connection_status
    → appends status to server version lines

verify:
  execute_verify()
    → calls parse_claude_mcp_list(env_vars)
    → formats with _format_claude_mcp_section()
    → shows active provider first, other "for completeness"
    → passes claude_mcp_ok to _compute_exit_code()
```

## Files to Create or Modify

### Modified Files

| File | Change |
|------|--------|
| `src/mcp_coder/utils/mcp_verification.py` | Add `ClaudeMCPStatus`, `parse_claude_mcp_list()` |
| `src/mcp_coder/icoder/env_setup.py` | Add `mcp_connection_status` field to `RuntimeInfo`, call parser |
| `src/mcp_coder/icoder/ui/app.py` | Extend `on_mount()` server lines with connection status |
| `src/mcp_coder/cli/commands/icoder.py` | Include connection status in `session_start` event |
| `src/mcp_coder/cli/commands/verify.py` | Add `_format_claude_mcp_section()`, update `execute_verify()`, update `_compute_exit_code()` |
| `tests/utils/test_mcp_verification.py` | Tests for `parse_claude_mcp_list()` |
| `tests/icoder/test_env_setup.py` | Tests for `mcp_connection_status` in `RuntimeInfo` |
| `tests/icoder/test_app_pilot.py` | Test connection status display in `on_mount()` |
| `tests/cli/commands/test_verify_exit_codes.py` | Tests for `claude_mcp_ok` in `_compute_exit_code()` |
| `tests/cli/commands/test_verify_format_section.py` | Tests for `_format_claude_mcp_section()` |
| `tests/cli/commands/test_verify_command.py` | Integration tests for provider-aware MCP sections |

### No New Files Created

All changes fit within existing modules.

## Implementation Steps

- **Step 1**: Parser + dataclass in `mcp_verification.py` (with tests)
- **Step 2**: Wire into `RuntimeInfo` + iCoder startup display + event log (with tests)
- **Step 3**: Verify command — format helper, provider-aware sections, exit code (with tests)
