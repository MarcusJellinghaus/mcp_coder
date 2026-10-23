# Step 4 — Migrate `tests/cli/commands` (6 files)

## LLM prompt

> Read `pr_info/steps/summary.md` (especially "Shared migration rules"), then implement
> `pr_info/steps/step_4.md` exactly. Run the checks listed in the summary, including the
> full fast pytest suite; all must pass. Produce one commit.

## WHERE
- `tests/cli/commands/test_define_labels_execute.py`
- `tests/cli/commands/test_define_labels_staleness.py`
- `tests/cli/commands/test_define_labels_status.py`
- `tests/cli/commands/test_define_labels_validate.py`
- `tests/cli/commands/test_set_status.py`
- `tests/cli/commands/test_set_status_from_status.py`

## WHAT
Replace every full issue literal (`"locked": False` / `locked=False` sites) with
`make_issue_data(...)` per the shared migration rules. No new tests: behaviour is unchanged,
and the existing tests verify the conversion.

## HOW
`from tests.github_factories import make_issue_data`. Retype `dict[str, Any]` receivers
to `IssueData` where mypy requires; remove imports left unused.

## ALGORITHM (per site)
```
values = literal's key/value pairs
drop pairs equal to factory result (see summary list)
if remaining == sentinel shape (number=0, empty strings): use create_empty_issue_data()
else: make_issue_data(**remaining)
```

## DATA
Each site still yields the same dict values as before.

## Done when
No line in these 6 files matches `"locked":|\blocked=`.
