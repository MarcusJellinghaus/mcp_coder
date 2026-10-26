# Summary — Split `tests/workflows/implement/test_task_processing.py` (#1329)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal
Split the 1361-line test file (allowlisted) into the base file plus four prefixed siblings, one per
source function family of `src/mcp_coder/workflows/implement/task_processing.py`. Then remove the
file from `.large-files-allowlist`.

## Pure refactoring — rules for every step
- **Move, don't change.** Classes move verbatim. No logic edits, renames, test deletions or merges.
- **Only allowed edits:** import statements, and removing the one `.large-files-allowlist` line.
  Nothing else is touched: no `pytestmark` (the source has none), no docstrings (`D` is ignored for
  `tests/**`), no `conftest.py`, no `vulture_whitelist.py`, no `docs/`.
- **Use the refactoring tools:** `mcp__mcp-tools-py__move_symbol` (dry run first, ≤ 2 symbols per
  call), `list_symbols`, `find_references`. Never move code by hand.
- **MCP tools only, no Bash** (commits excepted, per CLAUDE.md).
- **Failure action:** on any failed precondition or check named in a step, write one line to
  `pr_info/.blocked.txt` and stop. Don't hand-edit to work around it.

## Architectural / design changes
None in `src/`. The source module stays as it is: it is under the limit and cohesive.

Test layout only. The tests mirror the single source module as prefixed siblings in the same directory,
so the conftest chain (`tests/conftest.py` → `tests/workflows/implement/conftest.py`) is unchanged.

Key constraint: the **autouse fixture `_tracker_count_always_decreases`** only applies to tests in
its own module. Three classes reach the progress gate and need it: `TestProcessSingleTask`,
`TestProcessSingleTaskGating` and `TestIntegration`. They stay in the base file with the fixture.
Probes showed that the moved classes pass without it.

The helper `_make_llm_response` stays in the base file. The siblings `_blocked`, `_mypy` and
`_branch_name` import it with
`from tests.workflows.implement.test_task_processing import _make_llm_response`.
Siblings never import a `Test*` class (it would be collected twice) and never import the fixture.

| File | Contents | Tests |
|---|---|---:|
| `test_task_processing.py` (keep) | `_make_llm_response`, `_tracker_count_always_decreases`, `TestCommitMessageFile`, `TestProcessSingleTask`, `TestProcessSingleTaskGating`, `TestIntegration` | 18 |
| `test_task_processing_blocked.py` (new) | `TestReadAndClearBlocked`, `TestBlockedExitInPrompts`, `TestProcessSingleTaskBlocked` | 21 |
| `test_task_processing_mypy.py` (new) | `TestCheckAndFixMypy` | 6 |
| `test_task_processing_retry.py` (new) | `TestProcessTaskWithRetry` | 8 |
| `test_task_processing_branch_name.py` (new) | `TestBranchNameSource` | 2 |

Total: 55 tests, which is unchanged. Collected tests in `tests/workflows/implement/` = 193. Whole
suite = 6463 (2026-10-26; step 1 records the actual values).

## Files created / modified
- Modified: `tests/workflows/implement/test_task_processing.py` (classes moved out, import block shrinks)
- Created: `tests/workflows/implement/test_task_processing_blocked.py`
- Created: `tests/workflows/implement/test_task_processing_mypy.py`
- Created: `tests/workflows/implement/test_task_processing_retry.py`
- Created: `tests/workflows/implement/test_task_processing_branch_name.py`
- Modified: `.large-files-allowlist` (remove `tests/workflows/implement/test_task_processing.py`)
- Not touched: `src/`, `conftest.py`, `__init__.py`, `vulture_whitelist.py`, `docs/`, `test_task_progress_gate.py`

## TDD note
There is no new behaviour to test first. The 55 existing tests are the safety net: each step must
leave them collected and passing with the same counts.

## Shared definitions used by every step
**Fast-unit pytest filter** (the `-m` value):
`not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration`

**Collect counts** (one call): `run_pytest_check(extra_args=["--collect-only", "-qq", "tests/workflows/implement/"])`
prints one `path: N` line per file. If it does not print those lines, use `--collect-only -q <file>`
for each file instead.

**Move procedure** for each `move_symbol` call:
1. Dry run. It must list exactly `tests/workflows/implement/test_task_processing.py` and that step's
   destination. Anything else → blocked.
2. Real call. A timeout, `Token <…> cannot be matched`, or an empty destination → blocked.
3. Check the destination: class bodies, decorators, `@patch` strings and method-local imports are
   unchanged.

**Import fix-up** (the only hand edits allowed):
- Rewrite a relative import of `_make_llm_response` to the absolute form.
- Remove a *module-level* import that ruff reports as `F401` / `F811`. Never touch a method-local
  import.
- If `move_symbol` imported a name from a different module than the original, restore the original
  module.

**Standard checks per step:** `run_format_code`, `run_ruff_check`, `run_pylint_check`,
`run_mypy_check`, then pytest with `-n auto` and the fast-unit filter. Then run the collect counts.
