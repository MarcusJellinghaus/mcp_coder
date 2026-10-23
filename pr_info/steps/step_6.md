# Step 6 — Migrate `tests/workflows/create_plan` (6 files)

## LLM prompt

> Read `pr_info/steps/summary.md` (especially "Shared migration rules"), then implement
> `pr_info/steps/step_6.md` exactly. Run the checks listed in the summary, including the
> full fast pytest suite; all must pass. Produce one commit.

## WHERE
- `tests/workflows/create_plan/test_failure_handling.py`
- `tests/workflows/create_plan/test_guard_net.py`
- `tests/workflows/create_plan/test_main.py`
- `tests/workflows/create_plan/test_prerequisites.py`
- `tests/workflows/create_plan/test_prompt_execution.py`
- `tests/workflows/create_plan/test_success_label_gate.py`

## WHAT
- `mock_issue_data` fixtures (failure_handling, guard_net, main, success_label_gate):
  `return make_issue_data(number=123, title="Test Issue", body="Test issue body", ...)`,
  i.e. every value that differs from the factory default.
- `test_prompt_execution.py::_make_issue_data() -> IssueData`: same treatment.
- Empty sentinels (`test_failure_handling.py` `empty_issue` ~line 186,
  `test_main.py` `empty_issue_data` ~line 131,
  `test_prerequisites.py` `empty_issue_data` ~line 55) → `create_empty_issue_data()`
  from `mcp_coder.mcp_workspace_github`.
- All other literals → `make_issue_data(...)`.

## HOW
`from tests.github_factories import make_issue_data`. Remove imports left unused
(`IssueData` stays where it annotates fixtures/parameters).

## DATA
Fixture values unchanged.

## Done when
No line in these 6 files matches `"locked":|\blocked=`.
