# Step 5 — Migrate `tests/cli/commands/coordinator` (4 files)

## LLM prompt

> Read `pr_info/steps/summary.md` (especially "Shared migration rules"), then implement
> `pr_info/steps/step_5.md` exactly. Run the checks listed in the summary, including the
> full fast pytest suite; all must pass. Produce one commit.

## WHERE
- `tests/cli/commands/coordinator/test_commands.py`
- `tests/cli/commands/coordinator/test_core.py`
- `tests/cli/commands/coordinator/test_integration.py`
- `tests/cli/commands/coordinator/test_issue_stats.py`

## WHAT
Inline literals → `make_issue_data(...)` per the shared rules. Helpers become thin wrappers:

| Helper | New body / signature |
|---|---|
| `test_core.py::TestDispatchWorkflowSilentFallthroughGuard::_make_issue(pickup_label) -> IssueData` | `return make_issue_data(<its non-default values>)` |
| `test_core.py::TestBuildEligibleIssuesPrefetched::_make_issue(self, number: int, assignee: str)` | return type `dict[str, object]` → `IssueData`; `return make_issue_data(number=number, assignees=[assignee], <other non-defaults>)`; retype any `list[dict[str, object]]` receivers to `list[IssueData]` |
| `test_core.py` `sample_issue` fixture | `return make_issue_data(<non-defaults>)` |
| `test_issue_stats.py` `sample_issue` / `sample_issues` fixtures | each item → `make_issue_data(<non-defaults>)` |

## HOW
`from tests.github_factories import make_issue_data`. No `cast`. Remove unused imports.

## DATA
Helper outputs keep the same values as before.

## Done when
No line in these 4 files matches `"locked":|\blocked=`.
