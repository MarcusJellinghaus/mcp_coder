# Summary — Issue #1314: Split `tests/cli/commands/test_commit.py` + `tests/workflow_utils/test_commit_operations.py`

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`. Sibling: #1313.

## Goal

Get both allowlisted test files under 750 lines and off `.large-files-allowlist`, by
**moving test classes verbatim** — a pure, test-only refactoring.

## Hard rules (apply to every step)

- **Move, don't change.** Classes, functions, constants move verbatim. No logic edits, no
  renames, no reordering, no reformatting beyond `run_format_code`, no test deletions or merges
  (duplicates included).
- **Only allowed edits:** import statements, `.large-files-allowlist`, and the file-name
  reference in the `vulture_whitelist.py:136` comment.
- **Use the refactoring tools — never move code by hand:** `list_symbols`, `move_symbol`
  (always `dry_run=true` first, always pass `source_file` explicitly), `find_references`.
- `move_symbol` dry runs don't show the import lines it writes → read the header of every
  touched file after each move.
- Leftover unused imports → `mcp__mcp-tools-py__run_ruff_fix(select=["F401"],
  target_directories=[<source file>, <destination file>])` — only the files the step touches,
  never the whole project. Missing imports → add by `edit_file` (import lines only).
- No new module docstrings (`D` ignored for `tests/**`; pylint `C` disabled), no stubs,
  no re-exports.
- Sources untouched: `src/mcp_coder/cli/commands/commit.py`,
  `src/mcp_coder/workflow_utils/commit_operations.py`.

## TDD note

There is no new behaviour, so no new tests. The test suite itself is the safety net. In each
step the "test" is: count collected tests before the move, then after the move check the
counts and confirm the moved tests still pass unchanged.

## Architectural / design changes

None in production code. Test layout is realigned to mirror the source modules:

- **Misplaced tests relocated.** 3 classes (14 tests) in `tests/cli/commands/test_commit.py`
  exercise only `mcp_coder.workflow_utils.commit_operations` → they move to
  `tests/workflow_utils/`, next to the module they test.
- **Split by concern inside each module's test namespace** (single source module → prefixed
  sibling test files `test_<module>_<concern>.py`):
  - `cli/commands/commit.py` → `test_commit.py` (execute/preview/validate/cwd/parser) +
    `test_commit_push.py` (the `--push` feature: `_push_after_commit` and its wiring).
  - `workflow_utils/commit_operations.py` → `test_commit_operations.py` (main
    `generate_commit_message_with_llm` suite) + `test_commit_operations_parsing.py` (pure
    text processing: `strip_claude_footers`, `parse_llm_commit_response`) +
    `test_commit_operations_default_args.py` (`generate_commit_message_with_llm(project_dir)`
    called with default args, env helpers unpatched).
- Same-named classes (`TestGenerateCommitMessageWithLLM`, `TestParseLLMCommitResponse`) each
  land in a different file → no clash, no rename.
- No conftest changes: `tests/cli/commands/conftest.py` autouse fixtures don't touch
  `commit_operations`; `tests/workflow_utils/` has no conftest.

## Target layout

| File | Symbols | Tests |
|---|---|---:|
| `tests/cli/commands/test_commit.py` (modified) | `TestCommitAutoParserNoMcpConfig`, `TestExecuteCommitAutoResolveTuple`, `TestExecuteCommitAuto`, `TestPreviewModeLogic`, `TestValidateGitRepository`, `TestCommitAutoClaudeCwd` | 18 |
| `tests/cli/commands/test_commit_push.py` (new) | `MODULE`, `TestPushAfterCommit`, `TestCommitAutoPush` | 12 |
| `tests/workflow_utils/test_commit_operations.py` (modified) | `TestGenerateCommitMessageWithLLM`, `TestParseLLMCommitResponse` (1 test) | 19 |
| `tests/workflow_utils/test_commit_operations_parsing.py` (new) | `TestStripClaudeFooters`, `TestParseLLMCommitResponse` (from `test_commit.py`, 4 tests) | 25 |
| `tests/workflow_utils/test_commit_operations_default_args.py` (new) | `TestGenerateCommitMessageWithLLM`, `TestGenerateCommitMessageWithLLMExtended` (both from `test_commit.py`) | 10 |

Totals: 84 before, 84 after. `tests/cli/commands/` −14, `tests/workflow_utils/` +14.

## Files created / modified

Created:
- `tests/cli/commands/test_commit_push.py`
- `tests/workflow_utils/test_commit_operations_parsing.py`
- `tests/workflow_utils/test_commit_operations_default_args.py`

Modified:
- `tests/cli/commands/test_commit.py` (classes moved out, imports)
- `tests/workflow_utils/test_commit_operations.py` (class moved out, imports)
- `.large-files-allowlist` (remove the two entries)
- `vulture_whitelist.py` (line 136 comment: `test_commit.py` → `test_commit_push.py`)

Not modified: all `src/` files, all `conftest.py`, `docs/architecture/architecture.md`.

## Steps (one commit each)

| Step | Move | Allowlist / whitelist |
|---|---|---|
| 1 | `TestStripClaudeFooters`: `test_commit_operations.py` → `test_commit_operations_parsing.py` | remove `tests/workflow_utils/test_commit_operations.py` |
| 2 | `TestParseLLMCommitResponse`: `test_commit.py` → `test_commit_operations_parsing.py` | — |
| 3 | `TestGenerateCommitMessageWithLLM`, `TestGenerateCommitMessageWithLLMExtended`: `test_commit.py` → `test_commit_operations_default_args.py` | — |
| 4 | `MODULE`, then `TestPushAfterCommit`, `TestCommitAutoPush`: `test_commit.py` → `test_commit_push.py` | remove `tests/cli/commands/test_commit.py`; vulture comment |

Step 1 must precede step 2: the original `TestParseLLMCommitResponse` stays in
`test_commit_operations.py` and must never share a file with the one from `test_commit.py`.

## Standard checks (end of every step)

1. `mcp__mcp-tools-py__run_format_code`
2. `mcp__mcp-tools-py__run_pylint_check`, `run_mypy_check`, `run_ruff_check`
3. `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`
4. `run_lint_imports_check`, `run_tach_check`, `run_vulture_check`
5. `mcp__mcp-workspace__check_file_size` — passes, no stale allowlist entries
6. `mcp__mcp-workspace__git` diff with `compact=true` — only import lines, new-file headers,
   allowlist/whitelist lines; moved code suppressed
7. Collect-only counts (no marker filter):
   `run_pytest_check(extra_args=["--collect-only", "-q", "<path>"])` match the step's table

Any check failing for a reason the step can't fix with import-only edits → write one line to
`pr_info/.blocked.txt` and stop.
