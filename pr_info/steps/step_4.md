# Step 4: Verify exports, allowlist, and import linter

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #310

## WHERE

- `src/mcp_coder/workflows/implement/__init__.py` — verify (likely no change)
- `.large-files-allowlist` — verify (likely no change)
- `.importlinter` — verify (likely no change)

## WHAT

Verify that no re-exports, allowlist entries, or import linter contracts need updating after the extraction. Make changes only if needed.

## HOW

### 1. Check __init__.py

`check_and_fix_ci` is **not** in the current `__all__` list of `__init__.py`. The new `ci_operations.py` symbols (`CIFixConfig`, `_short_sha`, etc.) are all internal. **No change needed.**

Verify: `_poll_for_ci_completion` is also not exported (it's a private function). **No change needed.**

### 2. Check .large-files-allowlist

`src/mcp_coder/workflows/implement/core.py` is already on the allowlist and stays there (~803 lines, still above 750). The new `ci_operations.py` (~550 lines) is under 750 and doesn't need to be added. **No change needed.**

Also verify `tests/workflows/implement/test_core.py` is on the allowlist — it is, and after removing ~180 lines it may drop below 750. If it does, **remove it from the allowlist**.

### 3. Check .importlinter

The layered architecture contract has `mcp_coder.workflows` as one layer. Internal modules within `workflows.implement` (core.py, ci_operations.py, task_processing.py, etc.) are siblings — no layering contract governs their mutual imports. **No change needed.**

### 4. Run file-size check

Run `mcp-coder check file-size --max-lines 750` to verify:
- `core.py` is ~803 lines (still on allowlist, acceptable per issue)
- `ci_operations.py` is under 750 lines
- `test_core.py` — check if now under 750; if so, remove from allowlist

## DATA

No functional changes. Only configuration file updates if file sizes changed.

## ALGORITHM

```
1. Verify __init__.py exports are unchanged
2. Verify .large-files-allowlist is correct
3. Verify .importlinter has no new violations
4. Run file-size check
5. Update allowlist if test_core.py dropped below 750 lines
```

## Tests

Run full test suite to confirm nothing broke. Run import linter check.

## LLM Prompt

```
Implement Step 4 from pr_info/steps/step_4.md (see also pr_info/steps/summary.md).

Verify that __init__.py exports, .large-files-allowlist, and .importlinter are correct after the CI operations extraction. Update the allowlist if test_core.py dropped below 750 lines. Run all quality checks.

After changes (if any): run pylint, pytest, mypy and fix any issues.
Write commit message to pr_info/.commit_message.txt.
```
