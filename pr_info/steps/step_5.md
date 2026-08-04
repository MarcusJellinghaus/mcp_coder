# Step 5 — Gate 1: entry gate (open-tasks pre-flight)

**Read first:** `pr_info/steps/summary.md` (§ "New gate module", § "Gate 1").
**Depends on Steps 2–4 being committed** (label `code_review_open_tasks`, the
`enforce_implementation_gates` flag + `"tasks"` failure label, and `_fail`'s
`details` param). This step is one complete vertical slice: the gate function +
its wiring into `core.body()` + tests.

## WHERE

- **New:** `src/mcp_coder/workflows/review/gates.py`
- **New test:** `tests/workflows/review/test_gates.py`
- **Modified:** `src/mcp_coder/workflows/review/core.py`

## WHAT

```python
# gates.py
from pathlib import Path
from .config import ReviewConfig

MAX_LISTED_TASKS = 10

def check_open_tasks_gate(
    config: ReviewConfig, project_dir: Path
) -> tuple[str | None, str | None]:
    """Return (reason, details): (None, None) to proceed, ("tasks", <msg>) to block."""
```

## HOW / integration points

- `gates.py` imports:
  `from mcp_coder.workflow_utils.task_tracker import (get_incomplete_tasks,
  TaskTrackerFileNotFoundError)`.
- Gate skips entirely when `not config.enforce_implementation_gates` (plan lane).
- Uses `get_incomplete_tasks(str(project_dir / "pr_info"))` — bit-identical to
  `create_pr/core.py` (default `exclude_meta_tasks=False`).
- **Wire into `core.py`** at the very top of `body()`, before the round loop:

```python
def body() -> int:
    nonlocal supervisor_sid, pending_ci_note, last_verdict
    reason, details = check_open_tasks_gate(config, project_dir)
    if reason:
        return _fail(
            config, project_dir, reason,
            update_issue_labels=update_issue_labels,
            post_issue_comments=post_issue_comments,
            details=details,
            elapsed=time.time() - start_time,
        )
    for round_number in range(1, REVIEW_MAX_ROUNDS + 1):
        ...
```

  Add `from .gates import check_open_tasks_gate` to core's imports.

## ALGORITHM (check_open_tasks_gate)

```
if not config.enforce_implementation_gates: return None, None
try:
    tasks = get_incomplete_tasks(str(project_dir / "pr_info"))
except TaskTrackerFileNotFoundError:
    return None, None                                    # missing tracker → skip
except Exception as exc:                                 # no ## Tasks section / other → block
    return "tasks", (f"`pr_info/TASK_TRACKER.md` could not be read as a task "
                     f"list ({exc}) — fix the tracker structure; "
                     f"`/implementation_finalise` will not repair this.")
if not tasks: return None, None
shown = tasks[:MAX_LISTED_TASKS]
more = len(tasks) - len(shown)
listing = ", ".join(shown) + (f" … and {more} more" if more else "")
return "tasks", (f"{len(tasks)} open task(s) in `pr_info/TASK_TRACKER.md`: "
                 f"{listing} — run `/implementation_finalise`.")
```

## DATA

- Returns `tuple[str | None, str | None]` = `(reason, details)`.
- `reason` is `None` (proceed) or `"tasks"` (block → `status-17f-tasks`, RC=1).

## TDD — `tests/workflows/review/test_gates.py`

Patch `mcp_coder.workflows.review.gates.get_incomplete_tasks`:

- `enforce_implementation_gates=False` (use `REVIEW_PLAN`) → `(None, None)`, and
  `get_incomplete_tasks` **not called**.
- Returns `[]` → `(None, None)`.
- Returns `["A", "B"]` → `("tasks", details)`, details lists both and names
  `/implementation_finalise`.
- Returns 12 tasks → details lists exactly 10 + `… and 2 more`.
- Raises `TaskTrackerFileNotFoundError` → `(None, None)` (skip).
- Raises `TaskTrackerSectionNotFoundError` → `("tasks", details)` where details
  names the malformed tracker (not implying `/implementation_finalise` fixes it).

Optionally a `core`-level test: patch `check_open_tasks_gate` to return
`("tasks", "d")` and assert `run_review_workflow` returns `1` without entering
the round loop.

## Checks

pylint / pytest / mypy green. Confirm `core.py` still < 600 lines
(`mcp-coder check file-size --max-lines 600`).

## Commit

`Add open-tasks entry gate to review-implementation`
