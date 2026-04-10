# Step 2: Wire into RuntimeInfo + iCoder Startup Display + Event Log

## Context

See [summary.md](summary.md) for full issue context (#748).

This step wires `parse_claude_mcp_list()` (from Step 1) into the iCoder startup flow: store results in `RuntimeInfo`, display inline in the TUI, and log in the `session_start` event.

## LLM Prompt

> Implement Step 2 of issue #748 (MCP server connection status). Read `pr_info/steps/summary.md` for context and `pr_info/steps/step_2.md` for this step's details. Step 1 is already implemented — `ClaudeMCPStatus` and `parse_claude_mcp_list()` exist in `utils/mcp_verification.py`. Follow TDD: write tests first, then implement. Run all three code quality checks after changes.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/env_setup.py` | Add `mcp_connection_status` field to `RuntimeInfo`, call parser in `setup_icoder_environment()` |
| `src/mcp_coder/icoder/ui/app.py` | Extend `on_mount()` server lines with connection status |
| `src/mcp_coder/cli/commands/icoder.py` | Include connection status in `session_start` event emit |
| `tests/icoder/test_env_setup.py` | Add tests for new field |
| `tests/icoder/test_app_pilot.py` | Add test for connection status display |

## WHAT

### `RuntimeInfo` — new field

```python
@dataclass(frozen=True)
class RuntimeInfo:
    # ... existing fields ...
    mcp_connection_status: list[ClaudeMCPStatus] | None = None  # NEW — must be last (has default)
```

### `setup_icoder_environment()` — addition

After `mcp_servers = verify_mcp_servers(tool_env)`, add:

```python
# Connection status from claude mcp list (graceful fallback)
mcp_connection_status = parse_claude_mcp_list(env_vars=effective)
```

Pass `mcp_connection_status=mcp_connection_status` to the `RuntimeInfo` constructor.

### `on_mount()` — changed server lines

Current:
```python
*(f"{s.name} {s.version}" for s in info.mcp_servers),
```

New:
```python
*(
    f"{s.name} {s.version}  {_connection_status_suffix(s.name, info.mcp_connection_status)}"
    if info.mcp_connection_status is not None
    else f"{s.name} {s.version}"
    for s in info.mcp_servers
),
```

Add a small module-level helper in `app.py`:
```python
def _connection_status_suffix(
    server_name: str,
    statuses: list[ClaudeMCPStatus] | None,
) -> str:
    """Return '✓ Connected' or '✗ <text>' for a server, or '' if not found."""
```

### `execute_icoder()` — event log addition

Extend the `session_start` emit to include:
```python
mcp_connection_status={
    s.name: {"ok": s.ok, "status_text": s.status_text}
    for s in (runtime_info.mcp_connection_status or [])
},
```

## HOW

### Imports added to `env_setup.py`

```python
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus, parse_claude_mcp_list
```

### Imports added to `app.py`

```python
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus
```

### Graceful fallback

- `parse_claude_mcp_list()` returns `None` on failure → stored as `None` in `RuntimeInfo`
- `on_mount()` checks `if info.mcp_connection_status is not None` → falls back to version-only display
- `session_start` event uses `or []` to handle `None`

## ALGORITHM

### `_connection_status_suffix()`

```
1. If statuses is None, return ""
2. Find status where status.name == server_name
3. If not found, return ""
4. If status.ok, return "✓ Connected"
5. Else return "✗ {status.status_text}"
```

### `setup_icoder_environment()` addition

```
1. After verify_mcp_servers(tool_env), call parse_claude_mcp_list(effective)
2. Store result (list or None) in mcp_connection_status
3. Pass to RuntimeInfo constructor
```

## DATA

### `RuntimeInfo.mcp_connection_status`
- `None` — parser couldn't run (CLI not found, timeout, etc.)
- `list[ClaudeMCPStatus]` — parsed results (may be empty)

### `session_start` event additions
```json
{
  "mcp_connection_status": {
    "mcp-tools-py": {"ok": true, "status_text": "Connected"},
    "mcp-workspace": {"ok": true, "status_text": "Connected"}
  }
}
```

## TESTS

### `tests/icoder/test_env_setup.py` — additions to existing `TestSetupIcoderEnvironment`

- `test_mcp_connection_status_populated` — mock `parse_claude_mcp_list` to return statuses → verify `RuntimeInfo.mcp_connection_status` is populated
- `test_mcp_connection_status_none_on_failure` — mock `parse_claude_mcp_list` to return `None` → verify field is `None`
- `test_mcp_connection_status_default_none` — construct `RuntimeInfo` without the field → default is `None`

### `tests/icoder/test_app_pilot.py` — new test (or extend existing)

- `test_on_mount_shows_connection_status` — create `RuntimeInfo` with `mcp_connection_status`, verify `on_mount()` renders inline status
- `test_on_mount_no_connection_status_falls_back` — `mcp_connection_status=None` → verify version-only display (no crash)

### Unit test for `_connection_status_suffix` (in `test_app_pilot.py` or a new small test)

- `test_connection_status_suffix_connected` — returns `"✓ Connected"`
- `test_connection_status_suffix_failed` — returns `"✗ Failed to start"`
- `test_connection_status_suffix_not_found` — returns `""`
- `test_connection_status_suffix_none_statuses` — returns `""`
