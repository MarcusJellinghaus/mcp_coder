# Issue #553: mcp-coder verify — contextual install instructions

## Summary

Add contextual install instructions to `mcp-coder verify` based on the active provider (`default_provider`). Three changes:

1. **Install hints in domain modules** — Each verification result entry gains an `install_hint` string field when `ok=False`, so the data layer knows what to suggest.
2. **Conditional Claude section** — When langchain is active, replace the full Claude verification with a quick binary-existence check (one-liner if found, skip if not).
3. **Orchestrator rendering** — `_format_section()` renders inline hints; `execute_verify()` collects them and prints a summary `pip install ...` block at the end.

## Architectural / Design Changes

### Data-layer change (result dicts)

The verification result dicts gain one optional field:

```python
# Before
{"ok": False, "value": "not installed"}

# After
{"ok": False, "value": "not installed", "install_hint": "pip install langchain-core"}
```

This is additive — existing consumers that don't read `install_hint` are unaffected.

### Display-layer change (verify.py orchestrator)

- `_format_section()` checks each entry for `install_hint` and renders an indented `→` line below failures. No signature change.
- New helper `_collect_install_hints(result_dict) -> list[str]` — simple loop, used by `execute_verify()` to gather hints for the summary block.
- `execute_verify()` conditionally shows the Claude section based on `active_provider`:
  - `claude` → full verification (unchanged)
  - `langchain` + CLI binary found → one-liner: "Claude CLI: available (not active)"
  - `langchain` + CLI binary not found → skip Claude section entirely
- `execute_verify()` prints an `=== INSTALL INSTRUCTIONS ===` summary block when any hints were collected.

### No changes to

- `_compute_exit_code()` — exit logic unchanged
- `_format_mcp_section()` — MCP section unchanged
- `_LABEL_MAP` — no new keys needed (install_hint is not a displayed row)
- Any module outside the 3 target files

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/verification.py` | Add `install_hint` to package check results when `ok=False` |
| `src/mcp_coder/llm/providers/claude/claude_cli_verification.py` | Add `install_hint` (docs URL) to `cli_found` when `ok=False` |
| `src/mcp_coder/cli/commands/verify.py` | Conditional Claude display, inline hint rendering, summary block |
| `tests/llm/providers/langchain/test_langchain_verification.py` | Tests for `install_hint` fields |
| `tests/llm/providers/claude/test_claude_cli_verification.py` | Test for `install_hint` on `cli_found` |
| `tests/cli/commands/test_verify_format_section.py` | Test inline hint rendering |
| `tests/cli/commands/test_verify_orchestration.py` | Tests for conditional Claude display + summary block |

## Implementation Steps

| Step | Scope | Commit |
|------|-------|--------|
| 1 | LangChain `verification.py` — add `install_hint` fields + tests | `feat(verify): add install hints to langchain verification results` |
| 2 | Claude `claude_cli_verification.py` — add `install_hint` + test | `feat(verify): add install hint to claude CLI verification` |
| 3 | Orchestrator `verify.py` — conditional display, inline hints, summary block + tests | `feat(verify): contextual display and install summary in verify command` |
