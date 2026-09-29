# Step 4 — Progress gate in `process_single_task`

See [summary.md](./summary.md). Replaces "any file changed = success" with "the count of
incomplete non-meta tasks decreased", and stops `get_next_task` from swallowing tracker errors.

This step lands **last** of the four code steps because it is the emitter. Step 3's retry loop
already consumes `no_progress` and Step 2 already routes the `no_progress_after_retries` that
results, so the reason never reaches `core.py`'s else-less failure chain — not even for a single
intermediate commit.

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py`
- `tests/workflows/implement/test_task_progress_gate.py` (extend — created in Step 3; autouse fixture)
- `tests/workflows/implement/test_task_processing.py` (autouse fixture + 2 rewritten tests)

## WHAT

```python
def _count_incomplete_tasks(project_dir: Path) -> int:
    """Count incomplete non-meta tasks. Raises TaskTrackerError if unreadable."""
```

`get_next_task(project_dir) -> Optional[str]` — signature unchanged; the blanket
`except Exception: return None` at the end is **deleted** so tracker read failures propagate.

`process_single_task(...)` — signature unchanged in this step (Step 3 already added
`previous_reason`). New reason `"no_progress"`, with `detail` carrying the selected task name.

## HOW

- `TaskTrackerError` is the base class of both `TaskTrackerFileNotFoundError` and
  `TaskTrackerSectionNotFoundError` (`workflow_utils/task_tracker.py:76-84`). Import it
  alongside the existing `get_incomplete_tasks` import at `task_processing.py:27`:
  `from mcp_coder.workflow_utils.task_tracker import TaskTrackerError, get_incomplete_tasks`.
- One `except TaskTrackerError` clause, not two: the exception text already distinguishes the
  missing-file case from the missing-header case, so a single branch still yields an accurate
  message.
- **The blanket `except Exception` is re-homed, not dropped.** Deleting it from `get_next_task`
  also un-swallows the non-tracker failures it used to absorb — `Path.read_text` raises
  `OSError` and `UnicodeDecodeError` unwrapped (`task_tracker.py:103`), and those are *not*
  `TaskTrackerError`. Catching only `TaskTrackerError` would let them escape
  `process_single_task` into `run_guarded`, which fails the run as a bare `implementing_failed`
  with no message — the same silent-cause problem this step exists to fix. The call site
  therefore keeps a second, broad clause mapping anything else to the same `"error"` reason.
  The move is deliberate: the reason mapping stays where it can name the tracker in `detail`.
- `_count_incomplete_tasks` stays private — `__init__.py` and the public surface do not change.
- The after-read goes at the **very end** of the function, replacing only the final
  `return TaskOutcome(True, "completed")`. Steps 7–10 (mypy, formatters, commit, push) are not
  moved, not extracted and not re-ordered: commit and push cannot change checkbox counts, and
  the no-progress work must be committed anyway.

## ALGORITHM

Replace the `next_task = get_next_task(...)` block near `:388`:

```
try:
    next_task = get_next_task(project_dir)
    tasks_before = _count_incomplete_tasks(project_dir)
except TaskTrackerError as e:
    return TaskOutcome(False, "error", f"Cannot read pr_info/TASK_TRACKER.md: {e}")
except Exception as e:  # pylint: disable=broad-exception-caught
    return TaskOutcome(False, "error",
                       f"Cannot read pr_info/TASK_TRACKER.md: unexpected {type(e).__name__}: {e}")
if not next_task:
    return TaskOutcome(False, "no_tasks")
```

Replace the final `return TaskOutcome(True, "completed")` at `:541-542`:

```
try:
    tasks_after = _count_incomplete_tasks(project_dir)
except Exception:                           # pylint: disable=broad-exception-caught
    tasks_after = None                      # unreadable after-read == no progress, not a crash
if tasks_after is None or tasks_after >= tasks_before:
    log warning naming next_task, tasks_before, tasks_after
    return TaskOutcome(False, "no_progress", next_task)
return TaskOutcome(True, "completed")
```

Everything between the two blocks — the blocked/timeout/`mcp_unavailable` branches, the
zero-change `no_changes` check, mypy, formatters, commit, push — is untouched.

## DATA

| Situation | Return |
|-----------|--------|
| count decreased | `TaskOutcome(True, "completed")` |
| count flat or higher | `TaskOutcome(False, "no_progress", <task name>)` |
| after-read raises anything | `TaskOutcome(False, "no_progress", <task name>)` |
| before-read raises `TaskTrackerError` | `TaskOutcome(False, "error", "Cannot read pr_info/TASK_TRACKER.md: …")` |
| before-read raises anything else | `TaskOutcome(False, "error", "Cannot read pr_info/TASK_TRACKER.md: unexpected …")` |
| no tasks | `TaskOutcome(False, "no_tasks")` — unchanged |

Two tracker reads per round instead of one. Both are small local markdown reads; the second
read is deliberately not shared with `get_next_task` so that the ~24 existing tests patching
`get_next_task` keep working unchanged.

## Tests (write first)

Extend `tests/workflows/implement/test_task_progress_gate.py` (created in Step 3), patching
`get_next_task`,
`_count_incomplete_tasks`, `get_prompt`, `prompt_llm`, `store_session`, `get_full_status`,
`commit_changes`, `push_changes`:

1. `side_effect=[3, 2]` → `TaskOutcome(True, "completed")`.
2. `side_effect=[3, 3]` → reason `"no_progress"`, `detail` is the task name, **and**
   `commit_changes` / `push_changes` were both called.
3. `side_effect=[3, 4]` → `"no_progress"` (a rise is not progress).
4. After-read raises `TaskTrackerFileNotFoundError` → `"no_progress"`, no exception escapes.
5. Before-read (`get_next_task`) raises `TaskTrackerFileNotFoundError` → reason `"error"`,
   `"TASK_TRACKER.md"` in `detail`.
6. `TaskTrackerSectionNotFoundError` on the before-read → same, with the section fault named
   in `detail`.
7. Before-read raises a **non**-`TaskTrackerError` (`OSError`, and `UnicodeDecodeError` as a
   second parameterized case) → reason `"error"` with `"TASK_TRACKER.md"` in `detail`; nothing
   escapes `process_single_task`. This is the behaviour the deleted blanket `except` used to
   provide and the narrow clause alone would lose.
8. Zero file changes still returns `"no_changes"`, not `"no_progress"` — the existing gate wins
   because it runs first.

The same autouse fixture goes in **both** test files — `test_task_processing.py` and
`test_task_progress_gate.py`:

```python
@pytest.fixture(autouse=True)
def _tracker_count_always_decreases():
    with patch(
        "mcp_coder.workflows.implement.task_processing._count_incomplete_tasks",
        side_effect=itertools.count(5, -1),
    ):
        yield
```

Function-scoped, so each test gets a fresh strictly-decreasing sequence regardless of how many
reads its code path performs.

`test_task_progress_gate.py` needs it too: Step 3's prompt-assembly test (`step_3.md:128`)
calls `process_single_task` directly and patches only `prompt_llm` / `get_next_task`, so without
the fixture the new before-read hits the real tracker, returns `"error"` before the LLM call and
the test fails — Step 4 would not land with checks green. The fixture is compatible with the
gate tests above: a `@patch(... _count_incomplete_tasks)` decorator is applied when the test
function is called, i.e. *after* fixture setup, so the per-test patch wins and is restored
cleanly.

Rewrite the two tests that assert the swallowed error:

- `test_get_next_task_exception` (`:71-77`) → `pytest.raises(TaskTrackerError)` when
  `get_incomplete_tasks` raises `TaskTrackerFileNotFoundError`. Keep a separate case showing a
  non-tracker `Exception` also propagates now.
- `test_error_recovery_patterns` (`:968-979`) → same change; it asserts the same removed
  behaviour.

## Checks

`run_format_code`, then pylint / pytest / mypy.

## LLM prompt

> Implement Step 4 of `pr_info/steps/step_4.md`, with `pr_info/steps/summary.md` for context.
> Steps 1–3 must be complete first. Write the tests first, then the implementation.
> Add `_count_incomplete_tasks` to `task_processing.py`, snapshot the count next to the
> `get_next_task` call, and re-read it at the very end of `process_single_task` — replacing only
> the final `return TaskOutcome(True, "completed")`. Do not move, extract or reorder the mypy,
> formatter, commit or push blocks: a no-progress round must still be committed and pushed.
> Delete the blanket `except Exception` from `get_next_task` and re-home it at the call site:
> an `except TaskTrackerError` clause plus a broad `except Exception` clause, both returning
> reason `"error"` with a detail naming `pr_info/TASK_TRACKER.md`. The broad clause is required —
> `Path.read_text` raises `OSError` / `UnicodeDecodeError`, which are not `TaskTrackerError`, and
> without it they would escape `process_single_task` into `run_guarded` with no message.
> Any failure on the *after*-read counts as no progress, not a crash.
> Add the autouse fixture to **both** `test_task_processing.py` (so the existing ~24
> `process_single_task` tests keep passing) and `test_task_progress_gate.py` (so Step 3's
> prompt-assembly test, which patches only `prompt_llm` / `get_next_task`, does not hit the new
> real before-read and bail out with `"error"`). Rewrite the two tests that assert `get_next_task`
> returns None on a tracker error.
> Run `run_format_code`, then pylint, pytest and mypy; fix everything before finishing.
