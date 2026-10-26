# Summary — Split `tests/workflows/vscodeclaude/test_issues.py` (#1316)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal
Get `tests/workflows/vscodeclaude/test_issues.py` (948 lines) under the 750-line limit, take it off
`.large-files-allowlist`, and move the misplaced `TestBuildEligibleIssuesPrefetched` out of
`tests/cli/commands/coordinator/test_core.py` into the `issues.py` test namespace.

## Pure refactoring — rules
- **Move, don't change.** Classes move verbatim: no logic edits, renames, reorders, merges or deletions.
- **Only allowed edits:** import statements and the one `.large-files-allowlist` line.
- **Refactoring tools only:** `mcp__mcp-tools-py__move_symbol` (dry run first), `list_symbols`,
  `find_references`. Never move code by hand.
- **MCP tools only — no Bash** for checks. No stubs, no re-exports.
- TDD does not apply: no behaviour changes. Each step instead proves "no change" with
  collected-test counts before/after plus the full check suite.

## Design change (test layout only — `src/` is untouched)
`src/mcp_coder/workflows/vscodeclaude/issues.py` (408 lines) stays as is. Its tests split into
the base file plus one prefixed sibling (`foo.py` ↔ `test_foo.py` + `test_foo_<concern>.py`):

| Test file | Covers `issues.py` section | Classes | Tests | ~Lines |
|---|---|---|---:|---:|
| `test_issues.py` (kept) | Label config, status rules, eligibility (25–300) | `TestIssueSelection`, `TestFilterEligibleVscodeclaudeIssues`, `TestGetCachedEligibleVscodeclaudeIssues`, `TestNumericPriorityExtraction`, `TestGetIgnoreLabels`, `TestGetMatchingIgnoreLabel`, `TestIsStatusEligibleForSession`, `TestStatusRequiresLinkedBranch` | 40 | ~560 |
| `test_issues_branch_check.py` (new) | Branch check (303–408) | `TestBuildEligibleIssuesWithBranchCheck` (from `test_issues.py`), `TestBuildEligibleIssuesPrefetched` (from `coordinator/test_core.py`) | 9 | ~530 |
| `test_issues_branch_requirements.py` | — | unchanged | 5 | 32 |

`tests/cli/commands/coordinator/test_core.py` loses only `TestBuildEligibleIssuesPrefetched`
(52 → 50 tests, 1298 → ~1172 lines) and **stays allowlisted** (its split is a separate issue).

### Deviation from the issue's target layout (KISS)
The issue planned a third file, `test_issues_eligibility.py`. That layout was sized when
`test_issues.py` was 1158 lines. Since #1309 (`make_issue_data` factory) it is 948 lines, so
moving only the branch-check class already leaves `test_issues.py` at ~560 lines (< 600 soft
target). Dropping the eligibility file means 2 moves instead of 3 and one new file instead of two.
Every "Done when" criterion of the issue still holds.

### Other drift from the issue text (since #1309)
- `cast` is no longer imported; `make_issue_data` (`tests.github_factories`) is.
- `TestBuildEligibleIssuesPrefetched` has no `# type: ignore[arg-type]` any more; it uses
  `IssueData` annotations and `make_issue_data` instead. Mypy now proves `IssueData` resolves in
  the destination.
- Line numbers: `TestBuildEligibleIssuesWithBranchCheck` 562–948 in `test_issues.py`;
  `TestBuildEligibleIssuesPrefetched` 1173–1298 in `coordinator/test_core.py`.

### Fixtures
No `conftest.py` change. `tests/cli/commands/conftest.py` autouse fixtures stop applying to the
moved Prefetched class, but they patch only `mcp_coder.cli.commands.*`, which `issues.py` never
reaches; `tests/workflows/vscodeclaude/conftest.py` has no autouse fixtures. Step 2 proves this
by running the two tests before and after the move.

## Files created / modified
| Path | Change |
|---|---|
| `tests/workflows/vscodeclaude/test_issues_branch_check.py` | **new** — receives both branch-check classes |
| `tests/workflows/vscodeclaude/test_issues.py` | loses `TestBuildEligibleIssuesWithBranchCheck`; imports trimmed |
| `tests/cli/commands/coordinator/test_core.py` | loses `TestBuildEligibleIssuesPrefetched`; imports unchanged |
| `.large-files-allowlist` | remove `tests/workflows/vscodeclaude/test_issues.py` |

No `src/`, `conftest.py`, `.importlinter`, `tach.toml` or `vulture_whitelist.py` changes.

## Steps
1. `step_1.md` — move `TestBuildEligibleIssuesWithBranchCheck` → `test_issues_branch_check.py`; drop allowlist entry.
2. `step_2.md` — move `TestBuildEligibleIssuesPrefetched` → `test_issues_branch_check.py`.

## Check suite (run at the end of every step)
- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_ruff_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]` (moved tests carry no integration markers)
- `mcp__mcp-tools-py__run_lint_imports_check`, `mcp__mcp-tools-py__run_tach_check`, `mcp__mcp-tools-py__run_vulture_check`
- `mcp__mcp-workspace__check_file_size` — passes, no stale allowlist entries
- `mcp__mcp-workspace__git` `diff` (`compact=true`) — only import hunks, the new file header,
  moved-block summary lines, blank-line-only hunks and the allowlist line. Moved code suppressed.
