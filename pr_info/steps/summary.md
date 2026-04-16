# Issue #824 — Verify Output Redesign: Summary

## Goal

Refresh `mcp-coder verify` output for clarity: add an `ENVIRONMENT` section, group config by TOML section, rename status codes, and warn about unresolved `${...}` placeholders in `.mcp.json`.

No new verification logic — purely presentation + one new warnings section sourced from `.mcp.json`.

---

## Architectural / Design Changes

### 1. Status symbols become a module-level constant
`_get_status_symbols()` in `cli/utils.py` is platform-branched (Windows ASCII / Unix Unicode). Decision 3 makes everything ASCII. The function collapses to a constant:

```python
STATUS_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}
```

This constant lives in `verify.py` (its only consumer). The helper in `cli/utils.py` is deleted along with its dedicated test file. Also: Unicode `→` is replaced with ASCII `->`.

### 2. A single `_pad(title)` header helper
Every section header passes through `_pad(title)` which returns `"\n=== {title} " + "=" * fill` (pad to 60, never truncate). Replaces all header literals in `verify.py` (all 9 header-print sites: the six named sections plus the fallback-branch headers for the "langchain-mcp-adapters not installed" path and the INSTALL INSTRUCTIONS header).

### 3. New `_print_environment_section()`
Informational section at the top of the output. Uses `sys`, `os.environ`, and `importlib.metadata.version()`. Prints rows directly (mirrors the existing `PROMPTS` section style).

### 4. Config section: render-time grouping
`verify_config()` return shape is **unchanged**. `execute_verify` groups entries by `entry["label"]` (e.g., `[github]`), prints each `[section]` header once, then indents items below. Key is extracted from `entry["value"]` via `str.partition(" ")`.

### 5. MCP config warnings + scoped log filter
- Parse `.mcp.json` directly (simple regex on `mcpServers[*].env[*]` values).
- Attach a `logging.Filter` to the `"langchain_mcp_adapters"` logger around `verify_mcp_servers()` to drop the raw `WARNING: env['PYTHONPATH']...` stdout noise.
- New section `=== MCP CONFIG WARNINGS ===` rendered only when findings exist.

### 6. Section order (final)
```
ENVIRONMENT → CONFIG → PROMPTS → BASIC VERIFICATION →
LLM PROVIDER → MCP SERVERS (Claude) →
MCP SERVERS (langchain) server list → MCP CONFIG WARNINGS →
  [MCP edit smoke test + test-prompt rows are part of the langchain-MCP section
   and print AFTER the MCP CONFIG WARNINGS section] →
MLFLOW → INSTALL INSTRUCTIONS
```

Note: MCP CONFIG WARNINGS is rendered **immediately after the langchain-MCP server list, BEFORE the MCP edit smoke-test and test-prompt lines**. The smoke-test + test-prompt lines are part of the langchain-MCP section's output and follow the warnings section.

---

## Files to Modify or Create

### Modified (source)
- `src/mcp_coder/cli/commands/verify.py` — all presentation changes
- `src/mcp_coder/cli/utils.py` — delete `_get_status_symbols` and its `__all__` entry

### Modified (tests — label/arrow rename across the suite)
- `tests/cli/commands/test_verify.py`
- `tests/cli/commands/test_verify_command.py`
- `tests/cli/commands/test_verify_exit_codes.py`
- `tests/cli/commands/test_verify_format_section.py`
- `tests/cli/commands/test_verify_integration.py`
- `tests/cli/commands/test_verify_orchestration.py`

### Deleted
- `tests/cli/test_utils_status_symbols.py` — subject (`_get_status_symbols`) removed

### Created (no new source modules)
- No new files. All helpers live inside `verify.py`.

---

## Step Plan (5 commits)

| # | Step | Commit theme |
|---|------|--------------|
| 1 | Status symbols + arrow rename | ASCII-only constants; `[NO]`→`[ERR]`, `[!!]`→`[WARN]`, `→`→`->` |
| 2 | Header padding helper | Add `_pad(title)`, apply to all 6 headers |
| 3 | Environment section | New section at top of verify output |
| 4 | Config regrouping | TOML-style `[section]` grouping at render time |
| 5 | MCP config warnings + log filter | Parse `.mcp.json`, silence raw log warnings, render new section |

Each step: tests + implementation + pylint/pytest/mypy passing → one commit.

---

## Constraints Preserved from Issue #824

- `verify_config()` return shape unchanged.
- Long headers (e.g. `=== MCP SERVERS (via langchain-mcp-adapters — for completeness) ===`) never truncated — padding only when < 60 chars.
- Virtualenv detection via `sys.prefix != sys.base_prefix` (not `VIRTUAL_ENV`).
- `importlib.metadata.PackageNotFoundError` rendered as `[ERR] not installed`.
- `MCP CONFIG WARNINGS` section omitted when clean or `.mcp.json` missing/invalid.
- ASCII on all platforms (no Unicode `✓`/`✗`/`⚠`/`→`).
