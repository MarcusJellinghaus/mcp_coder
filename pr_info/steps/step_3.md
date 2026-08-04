# Step 3 — `ReviewConfig.enforce_implementation_gates` + failure_labels entries

**Read first:** `pr_info/steps/summary.md` (§ "One new `ReviewConfig` field").
This step adds the single flag that gates *both* gates and maps the two new
failure reasons to the Step 2 labels. Nothing consumes the flag yet — that is a
valid intermediate commit; Steps 5 and 6 wire it in.

## WHERE

- **Modified:** `src/mcp_coder/workflows/review/config.py`
- **Modified test:** `tests/workflows/review/test_config.py`

## WHAT

1. Add a field to the `ReviewConfig` dataclass, placed **after** `tie_break` (the
   last defaulted field) with a default so field-ordering stays valid:

```python
enforce_implementation_gates: bool = False
```

   Docstring:
   > Whether the implementation-lane safety gates run: the pre-flight
   > open-tasks check (Gate 1) and the CI-proven exit guard (Gate 2). ``True``
   > for ``review-implementation`` only. Deliberately distinct from
   > ``run_after_steps`` (which means "run rebase + CI").

2. Set it explicitly on both instances:
   - `REVIEW_IMPLEMENTATION` → `enforce_implementation_gates=True`
   - `REVIEW_PLAN` → `enforce_implementation_gates=False`

3. Extend `REVIEW_IMPLEMENTATION.failure_labels` with the two new reasons
   (leave `REVIEW_PLAN.failure_labels` unchanged):

```python
failure_labels={
    "general": "code_review_failed",
    "timeout": "code_review_timeout",
    "mcp_unavailable": "code_review_mcp",
    "ci": "code_review_ci",
    "tasks": "code_review_open_tasks",       # NEW
    "ci_unknown": "code_review_ci_unknown",  # NEW
},
```

## HOW / integration points

- No import changes. `failure_labels` values are label `internal_id`s that must
  match the labels added in Step 2.

## TDD — `tests/workflows/review/test_config.py`

- Assert `REVIEW_IMPLEMENTATION.enforce_implementation_gates is True` and
  `REVIEW_PLAN.enforce_implementation_gates is False`.
- Assert `REVIEW_IMPLEMENTATION.failure_labels["tasks"] == "code_review_open_tasks"`
  and `["ci_unknown"] == "code_review_ci_unknown"`.
- Assert `"tasks"` / `"ci_unknown"` are **absent** from
  `REVIEW_PLAN.failure_labels` (plan lane unchanged).

## DATA

`ReviewConfig` frozen dataclass gains one `bool` field; two new dict entries on
the implementation instance.

## Checks

pylint / pytest / mypy green.

## Commit

`Add enforce_implementation_gates flag and tasks/ci_unknown failure labels`
