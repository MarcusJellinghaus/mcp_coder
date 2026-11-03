# Step 5: Typed prep failure, classifier decision, core wiring

See `pr_info/steps/summary.md` (§2, Constraints of issue #1093).
The guard helper, byte restore and feedback loop follow in step 6; repair in step 7.
Here an INVALID tracker fails directly and population stays a single LLM call.

## WHERE
- `src/mcp_coder/workflows/implement/task_tracker_prep.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/prerequisites.py`, `__init__.py`: remove `has_implementation_tasks`
- `tools/jenkins_issue_patterns.toml`
- Tests: `tests/workflows/implement/test_task_tracker_prep.py`, `test_core*.py`,
  `test_core_workflow.py`, `test_prerequisites.py`, `tests/tools/test_jenkins_classify_logs.py`

## WHAT
```python
# task_tracker_prep.py
TRACKER_FILE = f"{PR_INFO_DIR}/TASK_TRACKER.md"
PREP_STAGES = {"task_tracker_prep_failed": "Task tracker preparation",
               "general": "Task tracker validation"}

class TrackerPrepError(Exception):
    def __init__(self, reason: str, message: str) -> None:  # sets .reason, .stage = PREP_STAGES[reason]

def prepare_task_tracker(project_dir, provider, mcp_config=None, settings_file=None) -> None: ...
```

## HOW
- Every `return False` in `prepare_task_tracker` becomes `raise TrackerPrepError(reason, <same text>)`.
  The steps-dir check and MISSING use `"task_tracker_prep_failed"`.
- The decision uses `classify_task_tracker` instead of `has_implementation_tasks`:
  POPULATED → return; INVALID → `TrackerPrepError("general", describe_violations(v))`;
  EMPTY → today's single population call (inline guard unchanged), then the post-check is
  "classifies as POPULATED", else `TrackerPrepError("task_tracker_prep_failed", describe_violations(...))`.
- The broad `except Exception as e` raises `TrackerPrepError(reason, f"Error preparing task tracker: {e}") from e`;
  `except TrackerPrepError: raise` comes first.
- `core.py`: replace the `if not prepare_task_tracker(...)` block with
  `try: prepare_task_tracker(...)` / `except TrackerPrepError as exc: return fail(exc.reason, stage=exc.stage, message=str(exc))`.
- Remove `has_implementation_tasks` from `prerequisites.py` (`__all__` too) and `__init__.py`;
  drop the now-unused parser imports there; delete `TestHasImplementationTasks`.
- Jenkins: add after `MC-IMPL-BLOCKED`:
  `[[signature]]` / `id = "MC-IMPL-TRACKER-INVALID"` / `regex = 'Stage: Task tracker validation'`
  (`handle_workflow_failure` logs `Stage: %s`; the prerequisites WARNING doesn't contain it).

## ALGORITHM
```
steps dir missing -> raise TrackerPrepError("task_tracker_prep_failed", ...)
state, v = classify_task_tracker(pr_info)
POPULATED -> return;  MISSING -> raise prep_failed;  INVALID -> raise TrackerPrepError("general", describe_violations(v))
EMPTY -> try: one LLM call; inline guard; classify == POPULATED else raise; commit_all_changes
         except TrackerPrepError: raise;  except Exception as e: raise TrackerPrepError("task_tracker_prep_failed", ...) from e
```

## DATA
`prepare_task_tracker` returns `None`; failures are `TrackerPrepError` with `.reason`, `.stage`, `str()` = message.

## Tests (write first)
- POPULATED → no LLM call, no commit.
- INVALID → `TrackerPrepError` reason `general`, stage "Task tracker validation", message
  names the line; no LLM call; tracker unchanged.
- EMPTY + LLM populates correctly → commit; returns `None`.
- EMPTY + LLM leaves it EMPTY or INVALID → `TrackerPrepError("task_tracker_prep_failed")`.
- Missing steps dir → `TrackerPrepError("task_tracker_prep_failed")`.
- `core`: `TrackerPrepError("general", ...)` → `fail("general", stage="Task tracker validation", ...)`.
  Existing tests patching `prepare_task_tracker` with `return_value=False` switch to
  `side_effect=TrackerPrepError("task_tracker_prep_failed", ...)`; `return_value=True` may stay.
  `test_core_workflow.py` stops patching `task_tracker_prep.has_implementation_tasks`.
- Jenkins: `classify("Stage: Task tracker validation\n", patterns)` contains `MC-IMPL-TRACKER-INVALID`.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5 only:
> write the tests first, then make `prepare_task_tracker` raise `TrackerPrepError` instead of
> returning `False`, decide with `classify_task_tracker` (INVALID fails directly), wire
> `core.py`, remove `has_implementation_tasks`, and add the Jenkins signature. Keep the single
> population call and its inline guard (step 6 replaces them). Run pylint, pytest
> (`-n auto`, unit markers) and mypy.
