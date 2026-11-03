# Step 3: Restructure check (pure functions)

See `pr_info/steps/summary.md` (§3 of issue #1093, checkbox-preservation rules).

## WHERE
- `src/mcp_coder/workflow_utils/task_tracker_classify.py`
- Tests: new `tests/workflow_utils/test_task_tracker_restructure_check.py`

## WHAT
```python
def has_completed_tasks(content: str) -> bool: ...
def check_restructure(original: str, restructured: str) -> list[str]: ...  # [] = accepted
```

## HOW
Both use `_scan_tracker` from step 2. Scope is the whole file except the "instructions"
section, so `## Step N` trackers without `## Tasks` are covered. Uses `collections.Counter`.

## ALGORITHM (`check_restructure`)
```
state, v = classify_tracker_content(restructured); if state != POPULATED: return v or ["... not populated"]
old = [l for l in _scan_tracker(original) if l.checked is not None and l.section != "instructions"]; new = same
if Counter(checked names old) != Counter(checked names new): error "[x] lines added, removed, reworded or toggled"
missing = Counter(unchecked old) - Counter(unchecked new): error per name "[ ] line removed, reworded or checked"
x_steps = {l.step for l in new if l.checked and l.step is not None}  # PR-section [x] has step None
for name, n in Counter(unchecked new in x_steps).items(): if n > Counter(unchecked old)[name]: error
```
`[ ]` lines in `## Pull Request` or in steps without `[x]` are not restricted.

## DATA
Error strings name the task, e.g. `"'commit message prepared': 3 unchecked under steps with [x], original has 2"`.

## Tests (write first)
- `has_completed_tasks`: template → False (its instruction `[x]` is ignored); `## Step N`
  tracker built from `TASK_TRACKER_TEMPLATE`'s `## Instructions for LLM` block followed by
  `## Step 1` containing an `[x]` line → True; flat list without `[x]` → False.
- Accepted: `## Step 1` tracker → `## Tasks` + `### Step 1:` + `## Pull Request` with checkbox
  lines moved verbatim; new `[ ]` in `## Pull Request`.
- Accepted: `## Pull Request` contains an `[x]` line and the restructure adds new `[ ]` PR
  tasks (PR `[ ]` lines stay unrestricted even when a PR checkbox is checked).
- Rejected: a deleted checkbox; a reworded checkbox; `[ ]`→`[x]`; `[x]`→`[ ]`; an added `[x]`;
  an added `[ ]` under a step with `[x]`; "Commit message prepared" `[ ]` count under steps
  with `[x]` higher than in the original; a result that is not POPULATED.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3 only:
> write the tests first, then add `has_completed_tasks` and `check_restructure` to
> `task_tracker_classify.py`, reusing `_scan_tracker`. Run pylint, pytest (`-n auto`,
> unit markers) and mypy.
