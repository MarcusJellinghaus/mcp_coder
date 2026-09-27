# Step 2 — Top-of-loop `_flush_round_log` in the review round loop

Read [summary.md](./summary.md) first. **Depends on step 1** — without the `commit_hash`
guard this step adds a no-op `git push` to every round.

This is the fix for the reported failure: round 1 `tasks` (clean) leaves its round-log write
uncommitted, round 2 `dismiss` attempts a rebase, git refuses with "You have unstaged changes".

## WHERE

- Source: `src/mcp_coder/workflows/review/core.py` — inside `run_review_workflow.body`, the
  round loop opening at line 127.
- Test: `tests/workflows/review/test_core_after_steps.py` — new test in the
  `# --- dismiss final gate: rebase + CI ---` area or appended at the end of the file.

## WHAT

One statement, no signature changes:

```python
for round_number in range(1, REVIEW_MAX_ROUNDS + 1):
    _flush_round_log(project_dir)          # NEW — must precede sha_before
    sha_before = get_latest_commit_sha(project_dir)
```

New test:

```python
def test_tasks_round_flushes_log_before_next_round_rebase(
    env: SimpleNamespace, tmp_path: Path
) -> None:
```

## HOW

- `_flush_round_log` is **already imported** in `core.py` (line 46,
  `from .handoff import _fail, _flush_round_log, _route_to_human, _set_label`). No import
  change.
- Leave every existing terminal `_flush_round_log` call in place: those paths `return` before
  reaching the next loop iteration, so there is no top-of-loop flush for them to rely on.
- The `env` fixture in `tests/workflows/review/conftest.py` already mocks everything needed —
  `handoff.commit_all_changes` (returns `commit_hash="FLUSHSHA"`), `handoff.push_changes`,
  `steps._attempt_rebase_and_push`, and `core.get_latest_commit_sha` (constant `"SHA0"`, so
  the new flush cannot perturb the `sha_before` comparison). **Do not modify `conftest.py`.**
- Import the existing helpers the sibling tests use:
  `from tests.workflows.review.conftest import _DISMISS, _TASKS, _resp, _reviewer, _run`.

## ALGORITHM

Comment the call to record why it exists and why the position is fixed:

```
for each round:
    flush whatever the PREVIOUS round left pending   # self-healing checkpoint
    capture sha_before                               # AFTER the flush, never before
    ... reviewer -> supervisor -> verdict -> after-steps ...
    write_round_log(...)                             # left uncommitted on purpose
```

The ordering relative to `sha_before` is load-bearing: a flush that commits something advances
HEAD, so capturing `sha_before` first would make the round's "applied vs no-op" label
(`core.py:578-583`) always read "applied" even when the round's own fix did nothing.

## DATA

- `_flush_round_log` returns `None` and never raises; no new failure path, no new return value,
  no change to any exit code.
- On round 1 of a clean tree the call is a no-op after step 1's guard: `commit_all_changes`
  reports `commit_hash=None`, the push is skipped, one debug line is logged.

## TDD

1. Write `test_tasks_round_flushes_log_before_next_round_rebase`. Drive a two-round run —
   round 1 `tasks` (three `prompt_llm` responses: reviewer, `_TASKS`, reviewer resume), round 2
   `dismiss` (two responses: reviewer, `_DISMISS`) — and record how many flushes had happened
   at each rebase attempt:

   ```python
   flushes_at_rebase: list[int] = []

   def _rebase(_project_dir: Path) -> bool:
       flushes_at_rebase.append(env.commit_all_changes.call_count)
       return True

   env.attempt_rebase_and_push.side_effect = _rebase
   env.prompt_llm.side_effect = [
       _reviewer(), _resp(_TASKS), _reviewer(session_id="rev-1"),  # round 1
       _reviewer(), _resp(_DISMISS),                               # round 2
   ]

   assert _run(tmp_path) == 0
   # Round 1's rebase sees only its own top-of-loop flush; round 2's also sees
   # the flush that committed round 1's round-log write. That is the bug.
   assert flushes_at_rebase == [1, 2]
   ```

   Confirm it fails before the source change (it records `[0, 0]` today — no flush runs on
   either round's rebase path).
2. Add the one-line call plus its comment. Confirm the test passes and the whole
   `tests/workflows/review/` suite still passes.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/workflows/review/"])
mcp__mcp-tools-py__run_mypy_check
```

Existing review tests are expected to pass unchanged: every assertion on the flush uses
`assert_called()`, not `assert_called_once()`. If any turns out to assert an exact count,
report it rather than silently loosening the assertion.

Then the full unit suite, then **one commit** for this step.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Step 1 must already be
> committed.
>
> Implement step 2 only, test-first. Add a single `_flush_round_log(project_dir)` call as the
> first statement inside the round loop in `src/mcp_coder/workflows/review/core.py` (line 127),
> **above** `sha_before = get_latest_commit_sha(project_dir)` — the ordering is load-bearing,
> explain it in a short comment. `_flush_round_log` is already imported. Leave all existing
> terminal flush calls in place.
>
> Write the test in `tests/workflows/review/test_core_after_steps.py` first, using the existing
> `env` fixture and the `_run` / `_reviewer` / `_resp` / `_TASKS` / `_DISMISS` helpers from
> `tests/workflows/review/conftest.py`; drive round 1 `tasks` then round 2 `dismiss` and assert
> that round 2's rebase attempt happens after round 1's round-log flush. Do not modify
> `conftest.py` or any existing test. Run `run_format_code`, then pylint / pytest (`-n auto`) /
> mypy, and produce a single commit.
