# Step 6 — Deallowlist + final verification

> Read `pr_info/steps/summary.md` first. This step contains **no code moves** —
> it removes the two allowlist entries now that both files are under 750, and runs
> the whole-PR verification gate.

## WHERE

- **Modified:** `.large-files-allowlist`
- **Verify only:** `src/mcp_coder/workflows/implement/__init__.py`

## WHAT

Remove exactly these two lines from `.large-files-allowlist`:

```
src/mcp_coder/workflows/implement/core.py
tests/workflows/implement/test_core.py
```

Leave every other allowlist entry untouched. Preserve the file's sorted order and
comment header.

## HOW

- **`__init__.py` sanity check (no edit expected):** confirm Step 3's
  `move_symbol` already repointed the re-exports so
  `log_progress_summary` and `prepare_task_tracker` import from
  `.task_tracker_prep`, `run_implement_workflow` still imports from `.core`, and
  `__all__` is byte-identical to the original. Only correct it here if something
  drifted.
- Removing an allowlist entry only passes CI if the file is genuinely under 750
  (done in Steps 4 and 5). The file-size check also reports **stale** allowlist
  entries, so a leftover line would fail.

## ALGORITHM

```
1. Edit .large-files-allowlist: delete the two core.py / test_core.py lines.
2. Diff-check __init__.py re-exports + __all__ against the original API.
3. Run check_file_size(max 750) → no offenders, no stale allowlist entries.
4. Run the full quality gate (format/ruff/lint-imports/pytest/pylint/mypy).
5. Run integration marker (execution_dir / claude_cli_integration) → confirm
   test_execution_dir_integration.py passes with the moved patch targets.
6. Run compact-diff over the whole PR → only imports/patch-paths/helper/headers.
```

## DATA

No code/data structures. Net PR effect: `core.py` ~500 lines, `test_core.py`
~700 lines, 4 new source modules + 6 new test files, package API (`__all__`)
unchanged.

## Checks (one commit)

- `mcp__mcp-workspace__check_file_size(max_lines=750)` — zero offenders **and**
  zero stale allowlist entries.
- Full gate: `run_format_code`, `run_ruff_fix`, `run_ruff_check`,
  `run_lint_imports_check`, `run_pytest_check` (fast unit markers),
  `run_pylint_check`, `run_mypy_check`.
- **Integration patch-target run:** `run_pytest_check(markers=["execution_dir"])`
  (or `["claude_cli_integration"]`) once, so
  `tests/integration/test_execution_dir_integration.py` (which patches
  `core.<moved-name>` targets, skipped by the fast-unit gate) is confirmed green
  end-to-end.
- Whole-PR purity: `mcp-coder git-tool compact-diff` shows only import changes,
  `patch()` target-path changes, the duplicated `_make_llm_response` helper, and
  new/deleted file headers — no logic changes anywhere.

## LLM prompt

> Implement Step 6 of `pr_info/steps/summary.md` (Issue #1025). Remove the two
> lines `src/mcp_coder/workflows/implement/core.py` and
> `tests/workflows/implement/test_core.py` from `.large-files-allowlist`, leaving
> all other entries and the sorted/commented structure intact. Verify (and only
> fix if drifted) that `src/mcp_coder/workflows/implement/__init__.py` re-exports
> `log_progress_summary`/`prepare_task_tracker` from `.task_tracker_prep`,
> `run_implement_workflow` from `.core`, with `__all__` unchanged. Run
> `check_file_size` (max 750 — expect zero offenders and zero stale allowlist
> entries), then the full gate (`run_format_code`, `run_ruff_fix`,
> `run_ruff_check`, `run_lint_imports_check`, `run_pytest_check` with fast unit
> markers, `run_pylint_check`, `run_mypy_check`), and finally a whole-PR
> `compact-diff` confirming only import/patch-path/helper/header changes. One
> commit.
