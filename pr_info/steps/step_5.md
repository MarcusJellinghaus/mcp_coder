# Step 5 — Move group D and `_make_assessment`, delete the original, update the allowlist

## LLM prompt
> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_5.md`) exactly.
> This is a pure refactoring. Do two `move_symbol` calls in this order, each with a dry run first: the class, then the helper. Then delete the drained file and remove its allowlist line.
> The only hand edits allowed are import lines and the one allowlist line.
> Use MCP tools only. Finish with the standard checks from the summary plus the final verification below, then make one commit.

## WHERE
- Source: `tests/workflows/vscodeclaude/test_session_restart.py` (**deleted** at the end)
- `tests/workflows/vscodeclaude/test_session_restart_issue_status.py` (**new**, no module docstring)
- `tests/workflows/vscodeclaude/conftest.py` (receives `_make_assessment`)
- `tests/workflows/vscodeclaude/test_session_restart_lifecycle.py` (its import of `_make_assessment` is rewritten)
- `.large-files-allowlist`

## WHAT
1. **Move the class.** `move_symbol(source_file=".../test_session_restart.py", symbol_names=["TestRestartClosedSessionsIssueStatus"], dest_file=".../test_session_restart_issue_status.py")`.
   - The class holds 7 tests: `..._skips_blocked_issues`, `..._updates_session_status`, `..._skips_closed_issues`, `..._skips_bot_stage_issues`, `..._skips_pr_created_issues`, `..._restarts_eligible_issues`, `..._eligible_to_eligible_transition`.
   - Its dry run must list only the source and the new file.
2. **Move the helper.** `move_symbol(source_file=".../test_session_restart.py", symbol_names=["_make_assessment"], dest_file="tests/workflows/vscodeclaude/conftest.py")`.
   - Its dry run must list exactly `test_session_restart.py`, `conftest.py`, `test_session_restart_lifecycle.py` and `test_session_restart_issue_status.py`.
3. **Delete the drained file.** `mcp__mcp-workspace__delete_this_file("tests/workflows/vscodeclaude/test_session_restart.py")`, after the pre-delete checks below.
4. **Update the allowlist.** In `.large-files-allowlist`, remove the line whose text is exactly `tests/workflows/vscodeclaude/test_session_restart.py`. Use `edit_file` and match by text, not line number.

## HOW
- **`conftest.py`:**
  - The helper, including its docstring, must match the original `_make_assessment` exactly. Signature: `_make_assessment(folder: str, *, active: bool = False, action: SessionAction = SessionAction.RESTART) -> SessionAssessment`.
  - `Decision` and `SessionAction` are added to the existing `from mcp_coder.workflows.vscodeclaude.types import (...)` block. If rope wrote a separate `types` import line, merge it into the block.
  - No other changes.
- **Importers (`_lifecycle`, `_issue_status`):** each must contain exactly `from tests.workflows.vscodeclaude.conftest import _make_assessment`. If rope wrote another form (`from tests.workflows.vscodeclaude import conftest`, a relative import, etc.), rewrite only that import line.
- **`test_session_restart_issue_status.py` imports** (from the original's modules): `json`, `Path`, `pytest`, `IssueData`, `BranchPrepResult`, `restart_closed_sessions`, `make_issue_data`, `_make_assessment` (from conftest). Ruff `F401`/`F821`/`F811` decides the final set.

## ALGORITHM
```
dry run + move TestRestartClosedSessionsIssueStatus -> new file
dry run (must list exactly 4 files) + move _make_assessment -> conftest.py
fix import lines (conftest types block; both importers use the absolute conftest import)
gate: directory collect 688; source collects 0; 4 destination files -> 22 passed
pre-delete: list_symbols(source) == [TestSessionRestart]; no importers -> delete file; edit allowlist
run_format_code; standard checks; final verification; commit
```

## DATA / gates
- **Either dry run** lists unexpected files → write one line to `pr_info/.blocked.txt` and stop.
- **Call-site check:** `search_files(pattern="conftest\\._make_assessment\\(|test_session_restart\\._make_assessment\\(", glob="tests/**/*.py")` → **0** hits.
  - On a hit: move the helper and then the class back with `move_symbol`, write one line to `pr_info/.blocked.txt` and stop.
- **Gate before the delete:**
  - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/test_session_restart.py"])` → **0**.
  - Directory collect-only → **688**.
  - `run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_restart_lifecycle.py", "tests/workflows/vscodeclaude/test_session_restart_issue_status.py", "tests/workflows/vscodeclaude/test_session_launch_prepare.py", "tests/workflows/vscodeclaude/test_session_launch_process_issues.py"])` → **22 passed**, split **5 / 7 / 3 / 7** by file.
  - If any of these fails: write one line to `pr_info/.blocked.txt` and stop.
- **Pre-delete checks:**
  - `list_symbols` on the source shows only `TestSessionRestart`.
  - `search_files(pattern="test_session_restart import|test_session_restart\\.", glob="tests/**/*.py")` → **0** hits.
  - If either check fails: don't delete. Write one line to `pr_info/.blocked.txt` and stop.

## Final verification (after the delete and allowlist edit)
- **Standard checks** from the summary: format, ruff, pylint, mypy, fast unit tests with `-n auto`, directory collect **688**. The 22-passed `-v` run of the four files above must still pass.
- **`search_files(pattern="from tests\\.workflows\\.vscodeclaude\\.conftest import _make_assessment", glob="tests/**/*.py")`** → **2** hits (`_lifecycle`, `_issue_status`).
- **`search_files(pattern="test_session_restart import", glob="tests/**/*.py")`** → **0** hits.
- **Other checks:** `run_lint_imports_check`, `run_tach_check` and `run_vulture_check` pass.
- **`mcp__mcp-workspace__check_file_size`** passes with no stale allowlist entries. Every created or receiving file is under 600 lines.
- **Compact diff of the whole branch** against the base branch (`mcp__mcp-workspace__git` diff, `compact=true`). Only these may appear:
  - the deleted-file header;
  - the three new-file headers;
  - import changes in the new files and in `conftest.py`;
  - exactly four 2-line class headers;
  - moved blocks (suppressed) and blank-line hunks;
  - the one allowlist removal.

  Anything else → write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(vscodeclaude): move issue-status tests and _make_assessment, delete test_session_restart.py`
