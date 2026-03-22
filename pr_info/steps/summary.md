# Issue #532: Refactor vscodeclaude startup commands to ordered commands list

## Problem

The vscodeclaude startup script uses a rigid `initial_command`/`followup_command` two-field model in `labels.json`. This causes:

1. **Timeout failures**: Single-command flows (e.g. `/implementation_review_supervisor`) are forced through the automated `mcp-coder prompt` path with a 300s timeout, but some commands take longer.
2. **Unnecessary 3-step flow**: The follow-up step (`/discuss`) runs as a separate automated subprocess, then hands off to a bare `claude --resume` — these can be merged into one interactive step.

## Solution: Architectural / Design Changes

### Schema change in `labels.json`

Replace `initial_command` (string|null) + `followup_command` (string|null) with a single `commands` field (list of strings, optional).

**Before:**
```json
"vscodeclaude": {
  "emoji": "📝", "display_name": "ISSUE ANALYSIS", "stage_short": "new",
  "initial_command": "/issue_analyse",
  "followup_command": "/discuss"
}
```

**After:**
```json
"vscodeclaude": {
  "emoji": "📝", "display_name": "ISSUE ANALYSIS", "stage_short": "new",
  "commands": ["/issue_analyse", "/discuss"]
}
```

Display-only entries (pr-created) keep `emoji`/`display_name`/`stage_short` but omit `commands`.

### Execution model change

The number of commands determines the execution strategy:

| Commands | Behavior |
|----------|----------|
| 0 or absent | Display-only, no session |
| 1 | **Interactive from start** — `claude "{cmd} {issue_number}"`. No timeout, no session ID capture, no step labels. Solves the timeout problem. |
| 2+ | **Automated first, interactive last** — Command[0] via `mcp-coder prompt` (captures session ID), command[1..n-1] via `mcp-coder prompt --session-id`, command[last] via `claude --resume %SESSION_ID% "{cmd}"` (interactive). Step labels shown. |

### Template changes

| Old template | New template | Purpose |
|---|---|---|
| `AUTOMATED_SECTION_WINDOWS` | `AUTOMATED_SECTION_WINDOWS` | Unchanged — first command in multi-command flow |
| `DISCUSSION_SECTION_WINDOWS` | _(removed)_ | Replaced by generalized templates below |
| _(new)_ | `AUTOMATED_RESUME_SECTION_WINDOWS` | Middle commands in multi-command — `mcp-coder prompt "{cmd}" --session-id` |
| _(new)_ | `INTERACTIVE_ONLY_SECTION_WINDOWS` | Single-command — `claude "{cmd} {issue_number}"`, no step labels |
| _(new)_ | `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS` | Last command in multi-command — `claude --resume %SESSION_ID% "{cmd}"` |
| `INTERACTIVE_SECTION_WINDOWS` | _(removed)_ | Becomes dead code — no flow uses bare resume without command |

### `STARTUP_SCRIPT_WINDOWS` template change

The main script template changes from fixed `{automated_section}{discussion_section}{interactive_section}` placeholders to a single `{command_sections}` placeholder. The `create_startup_script()` function builds command sections dynamically based on the commands list.

### Eligibility check change

`is_status_eligible_for_session()` changes from:
```python
config.get("initial_command") is not None
```
to:
```python
len(config.get("commands", [])) > 0
```

## Files to Modify

| File | Change type |
|------|-------------|
| `src/mcp_coder/config/labels.json` | Schema: replace `initial_command`/`followup_command` with `commands` |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Remove old templates, add new ones, update main script template |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Rewrite `create_startup_script()` normal-mode logic |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | Update `is_status_eligible_for_session()` |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Update docstring references |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Update docstring references |
| `tests/workflows/vscodeclaude/test_types.py` | Update schema validation assertions |
| `tests/workflows/vscodeclaude/test_workspace.py` | Update mock configs, template assertions |
| `tests/workflows/vscodeclaude/test_issues.py` | Update eligibility test comments |
| `tests/workflows/vscodeclaude/test_cleanup.py` | Update test comments |

### Files confirmed no change needed

| File | Reason |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/config.py` | `get_vscodeclaude_config()` returns raw dict — transparent to schema change |

## Implementation Steps

| Step | Focus | TDD approach |
|------|-------|--------------|
| 1 | `labels.json` schema + `test_types.py` | Tests first: update schema assertions, then update labels.json |
| 2 | `templates.py` + `issues.py` + docstrings | Update templates and eligibility check (no test changes yet — tested via step 3) |
| 3 | `workspace.py` + `test_workspace.py` | Tests first: update mock configs and assertions, then update script generation logic |
| 4 | `test_issues.py` + `test_cleanup.py` comments | Update remaining test comments, run full quality checks |
