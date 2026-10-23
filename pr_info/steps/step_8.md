# Step 8 — Migrate remaining `tests/workflows/vscodeclaude` (14 files)

## LLM prompt

> Read `pr_info/steps/summary.md` (especially "Shared migration rules"), then implement
> `pr_info/steps/step_8.md` exactly. Run the checks listed in the summary, including the
> full fast pytest suite; all must pass. Produce one commit.

## WHERE (`tests/workflows/vscodeclaude/`)
`test_assessment_issue_facts.py`, `test_cache_aware.py`, `test_checks.py`,
`test_checks_review_comments.py`, `test_closed_issues_integration.py`, `test_helpers.py`,
`test_issues.py`, `test_launch_vscode_env_vars.py`, `test_session_launch.py`,
`test_session_launch_process_issues.py`, `test_session_launch_regenerate.py`,
`test_status_display.py`, `test_status_display_branch_indicators.py`,
`test_status_display_scenario.py`

## WHAT
Inline literals → `make_issue_data(...)` per the shared rules. Helpers become thin wrappers
(signatures unchanged unless retyping is required):

| Helper | New body |
|---|---|
| `test_assessment_issue_facts.py::_make_issue(*, ...)` | `return make_issue_data(<params + non-defaults>)` |
| `test_checks.py::_make_pr_issue(number, labels=None) -> IssueData` | `return make_issue_data(number=number, title="PR Created Issue", labels=labels if labels is not None else ["status-10:pr-created"], assignees=["testuser"])` |
| `test_checks_review_comments.py::_make_issue(number) -> IssueData` | `return make_issue_data(number=number, <non-defaults>)` |
| `test_session_launch.py::_make_issue() -> IssueData` | `return make_issue_data(<non-defaults>)` |
| `test_session_launch_regenerate.py` `mock_issue` fixture | `return make_issue_data(<non-defaults>)` |

`CommentData` / PR comment builders in these files are out of scope.

## HOW
`from tests.github_factories import make_issue_data`. Retype `dict[str, Any]` receivers to
`IssueData` where mypy requires; no `cast`. Remove unused imports.

## DATA
Same values per site as before.

## Done when
No line in these 14 files matches `"locked":|\blocked=`.
