# Step 4 — Move branch-name tests, drop allowlist entry, final verification

## LLM prompt
Read `pr_info/steps/summary.md` (rules, move procedure, import fix-up, standard checks), then
implement this step exactly. This is a pure move plus one allowlist line: no logic edits. On any failed
check, write one line to `pr_info/.blocked.txt` and stop. Commit once at the end.

## WHERE
- Source: `tests/workflows/implement/test_task_processing.py`
- Destination (new): `tests/workflows/implement/test_task_processing_branch_name.py`
- `.large-files-allowlist`

## WHAT
- Move `TestBranchNameSource` (2 tests) unchanged.
- Delete the line `tests/workflows/implement/test_task_processing.py` from `.large-files-allowlist`.

## HOW
1. `move_symbol(source_file="tests/workflows/implement/test_task_processing.py", symbol_names=["TestBranchNameSource"], dest_file="tests/workflows/implement/test_task_processing_branch_name.py")`
   (dry run first).
2. Fix imports per the summary's import fix-up.
3. Remove the allowlist line with `edit_file`. Leave the rest of the file unchanged.
4. Run the standard checks, then the final verification below.

## ALGORITHM
```
dry-run + move [TestBranchNameSource]; verify _PROJECT_DIR stayed inside the class
fix module-level imports; remove allowlist line
standard checks + lint-imports + tach + vulture + check_file_size
collect counts (per file, directory, whole suite) + searches + compact diff
commit
```

## DATA — expected end state
`test_task_processing_branch_name.py` imports: `Path`, `MagicMock, patch`,
`from mcp_coder.workflows.implement.task_processing import check_and_fix_mypy, process_single_task`,
`from tests.workflows.implement.test_task_processing import _make_llm_response`.

`test_task_processing.py` imports: `Iterator` (collections.abc), `Path`, `ANY, MagicMock, patch`,
`pytest`, and from `mcp_coder.workflows.implement.task_processing`:
`RETRY_REMINDER, TaskOutcome, _cleanup_commit_message_file, process_single_task, process_task_with_retry`.
The docstring, `_make_llm_response`, `_tracker_count_always_decreases` and the method-local imports
in `TestProcessSingleTask` are unchanged.

Final verification. Any failure → blocked:
- `run_lint_imports_check`, `run_tach_check` and `run_vulture_check` pass. The whitelist entry for
  the fixture stays valid.
- `check_file_size` passes and reports no stale allowlist entries. All five files are under 750 lines.
- Collect counts: base **18**, `_blocked` **21**, `_mypy` **6**, `_retry` **8**, `_branch_name`
  **2**, directory **193**. Whole suite (`--collect-only -q`) is **6463**.
- The five files run with `-n auto` and the fast-unit filter: **55 passed**.
- `search_files(pattern="test_task_processing\\w*\\.(?!py\\b)\\w", glob="tests/**/*.py")` → 0 matches.
- `search_files(pattern="_tracker_count_always_decreases", glob="tests/**/*.py")` → only the two
  definitions (in `test_task_processing.py` and `test_task_progress_gate.py`).
- Compact diff (`mcp__mcp-workspace__git` `diff` against the base branch, `compact=true`). Allowed
  outside suppressed moved blocks:
  - import blocks;
  - headers of the new files;
  - moved-block preview/summary lines;
  - blank-line-only hunks;
  - the one allowlist removal.

  Any hunk in a test body, in `_make_llm_response`, in the fixture, in the docstring, in
  `vulture_whitelist.py` or in `docs/` → blocked.

Commit message: `test(implement): move branch-name tests, drop test_task_processing.py from allowlist (#1329)`
