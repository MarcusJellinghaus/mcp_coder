# Step 4 — Retry loop: consume `no_progress`

See [summary.md](./summary.md). Depends on Step 2, which introduced the `"no_progress"` reason,
and on Step 3, which already routes the `no_progress_after_retries` this step starts emitting.
Feeds the new reason into the existing 3-strike budget and gives attempt 2+ a reminder that
matches what actually went wrong. This is the commit that closes the loop: after it,
`no_progress` no longer reaches `core.py` at all.

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py`
- `tests/workflows/implement/test_task_progress_gate.py` (extend)

## WHAT

```python
RETRY_REMINDER: str                      # kept — existing tests import this name
NO_PROGRESS_REMINDER: str                # new
RETRY_REMINDERS: dict[str, str] = {
    "no_changes": RETRY_REMINDER,
    "no_progress": NO_PROGRESS_REMINDER,
}

def process_single_task(
    ...,
    attempt: int = 1,
    previous_reason: str | None = None,   # new, last parameter
    ...
) -> TaskOutcome: ...

def process_task_with_retry(...) -> TaskOutcome:   # signature unchanged
```

## HOW

- `previous_reason` is added as the last parameter with a `None` default, so no existing call
  site or test needs updating.
- Reminder selection is a dict lookup, not a branch:
  `full_prompt += RETRY_REMINDERS.get(previous_reason or "no_changes", RETRY_REMINDER)`,
  still guarded by `if attempt > 1`.
- `RETRY_REMINDER` keeps its current name and text — `test_retry_reminder_offers_blocked_exit`
  (`test_task_processing.py:198`) imports it directly.

## ALGORITHM

`NO_PROGRESS_REMINDER` text, worded so it asserts nothing about *which* task the previous
attempt was working on — once a no-progress attempt commits a ticked checkbox, attempt 2 may
legitimately be handed a different task:

```
⚠️ The previous attempt changed files but did not complete any task in
pr_info/TASK_TRACKER.md — no checkbox went from [ ] to [x]. Writing notes, logs or prose
into a step or plan file is NOT progress and is NOT a way to report a problem. Either do the
work and tick the box, or — if something blocks you — write one line to pr_info/.blocked.txt
saying what blocks you, and stop.
```

`process_task_with_retry`:

```
terminal = "no_changes_after_retries"
last_detail = ""
for attempt in 1..MAX_NO_CHANGE_RETRIES:
    outcome = process_single_task(..., attempt=attempt, previous_reason=previous_reason)
    if outcome.reason not in ("no_changes", "no_progress"):
        return outcome
    if outcome.reason == "no_progress":
        terminal = "no_progress_after_retries"     # sticky: the more informative reason wins
    last_detail = outcome.detail
    previous_reason = outcome.reason
    log warning naming attempt, MAX_NO_CHANGE_RETRIES and outcome.reason
return TaskOutcome(False, terminal, last_detail)
```

`terminal` is sticky by construction: once set to `no_progress_after_retries` it is never reset,
so a mixed sequence (one changed-but-flat attempt, two zero-change attempts) reports
`no_progress_after_retries`. `no_changes_after_retries` survives only when every attempt
produced zero changes.

## DATA

| Attempt sequence | Return reason |
|------------------|---------------|
| all `no_changes` | `no_changes_after_retries` (unchanged) |
| any `no_progress` | `no_progress_after_retries` |
| anything else | that outcome, returned unchanged and immediately |

`detail` on the terminal outcome carries the last attempt's task name, for the failure message
Step 3 builds.

## Cost

Both terminal reasons now cost up to 3 full LLM rounds with formatters, commit and push. Per-task
mypy is *not* in that cost: `RUN_MYPY_AFTER_EACH_TASK = False` in `constants.py`, so
`task_processing.py` skips it by default. The "at most 3 noise commits" ceiling holds only while
`MAX_NO_CHANGE_RETRIES` stays at 3.

## Tests (write first)

Extend `test_task_progress_gate.py`, patching `process_single_task`:

1. Three `no_progress` outcomes → `no_progress_after_retries`, detail preserved.
2. Three `no_changes` outcomes → `no_changes_after_retries` (regression:
   `test_retry_exhausted_returns_no_changes_after_retries` must keep passing too).
3. Mixed `no_changes`, `no_progress`, `no_changes` → `no_progress_after_retries`.
4. `no_progress` then `completed` → the success outcome, returned as-is.
5. `previous_reason` forwarding: attempt 2 after `no_progress` receives
   `previous_reason="no_progress"`; attempt 2 after `no_changes` receives `"no_changes"`.
6. Prompt-assembly test (patching `prompt_llm`): `previous_reason="no_progress"` with
   `attempt=2` puts `NO_PROGRESS_REMINDER` in the prompt and `RETRY_REMINDER` not in it;
   `previous_reason=None` with `attempt=2` puts `RETRY_REMINDER` in it.
7. `NO_PROGRESS_REMINDER` mentions `pr_info/.blocked.txt` (mirrors the existing
   `TestBlockedExitInPrompts` assertion) and does **not** name a specific task or step.

## Checks

`run_format_code`, then pylint / pytest / mypy.

## LLM prompt

> Implement Step 4 of `pr_info/steps/step_4.md`, with `pr_info/steps/summary.md` for context.
> Steps 1–3 must be complete first. Write the tests first, then the implementation.
> Add `NO_PROGRESS_REMINDER` and the `RETRY_REMINDERS` dict to `task_processing.py`, keeping the
> existing `RETRY_REMINDER` name and text because a test imports it. Add `previous_reason` as the
> last parameter of `process_single_task` with a `None` default so no existing call site changes.
> In `process_task_with_retry`, retry on both `no_changes` and `no_progress`, track the terminal
> reason in a variable instead of hardcoding it at the return, and make
> `no_progress_after_retries` sticky so a mixed sequence reports the more informative reason.
> Word `NO_PROGRESS_REMINDER` so it does not assert which task the previous attempt was about —
> a retry may legitimately target a different task.
> Run `run_format_code`, then pylint, pytest and mypy; fix everything before finishing.
