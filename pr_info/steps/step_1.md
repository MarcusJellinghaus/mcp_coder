# Step 1 — Land the previous round's round-log write at the top of each round

Read [summary.md](./summary.md) first.

This is the fix for the reported failure: round 1 `tasks` (clean) leaves its round-log write
uncommitted, round 2 `dismiss` attempts a rebase, git refuses with "You have unstaged changes".

One step, one commit: the `_flush_round_log` changes exist only to serve the new top-of-loop
call, so they are not worth a commit of their own (`planning_principles.md`, "merge tiny or
intertwined steps").

## WHERE

- Source: `src/mcp_coder/workflows/review/handoff.py` — `_flush_round_log` (signature at line
  123, docstring 124-141, body 142-153).
- Source: `src/mcp_coder/workflows/review/core.py` — inside `run_review_workflow.body`: the
  round loop opening at line 127 and the non-terminal `write_round_log(...)` at line 575.
- Test: `tests/workflows/review/test_handoff.py` — the `# --- _flush_round_log ---` section,
  after `test_flush_swallows_push_raise` (the last of the **five** existing tests in that
  section: lines 26, 42, 58, 74, 90).
- Test: `tests/workflows/review/test_core_after_steps.py` — appended at the end of the file.
- Fixture: `tests/workflows/review/conftest.py` — the `env` fixture gains one mock (see HOW).

## WHAT

`_flush_round_log` gains two keyword-only flags; both defaults preserve today's behaviour, so
every existing terminal call site is unchanged:

```python
def _flush_round_log(
    project_dir: Path,
    message: str = "Add review round log",
    *,
    only: Path | None = None,
    push: bool = True,
) -> None:
```

The one new call, as the first statement inside the round loop:

```python
for round_number in range(1, REVIEW_MAX_ROUNDS + 1):
    if pending_log is not None:
        _flush_round_log(project_dir, only=pending_log, push=False)
        pending_log = None
    sha_before = get_latest_commit_sha(project_dir)   # NEVER before the flush
```

New import in `handoff.py`, extending the existing shim import:

```python
from mcp_coder.mcp_workspace_git import commit_all_changes, get_full_status
```

Four new tests:

```python
# tests/workflows/review/test_handoff.py
def test_flush_no_commit_skips_push(...) -> None:
def test_flush_only_refuses_unrelated_dirt(...) -> None:
# tests/workflows/review/test_core_after_steps.py
def test_tasks_round_flushes_log_before_next_round_rebase(...) -> None:
def test_round_starting_dirty_for_another_reason_is_not_committed(...) -> None:
```

## HOW

### `only=` — the commit is scoped to the round log, never to an arbitrary dirty tree

`commit_all_changes` stages and commits **everything**. Calling it unconditionally at the top of
every round would auto-commit any unrelated dirt under the message "Add review round log" —
precisely the behaviour rejected in summary.md's *Decided against* list. `only=` turns it into a
guard: commit **only** when the pending change set is exactly that one file, otherwise refuse
and leave the tree alone for step 2's rebase precondition guard to report.

- Use `get_full_status(project_dir)` (already re-exported by `mcp_coder.mcp_workspace_git`); it
  returns `{"staged": [...], "modified": [...], "untracked": [...]}` with paths **relative to
  the project root**, and an empty dict for a non-repo.
- Compare the **union of all three lists** against `only`: the round log is a *modified*
  tracked file on a re-run but an *untracked* file the first time a run number is allocated, so
  both categories must count.
- Normalise with `only.relative_to(project_dir).as_posix()`.

### `push=False` — the top-of-loop commit does not push

The commit is what unblocks the rebase; pushing it separately buys nothing, because the round's
own push carries it a moment later (`core.py:484` on the `tasks` path, `_attempt_rebase_and_push`'s
force-with-lease push on the `dismiss` path, or a terminal `_flush_round_log` on a failing path).

Residual cost, accepted deliberately: on a `dismiss` round whose rebase is a no-op, that
force-with-lease push now carries a log-only commit to the remote *before* the CI gate, so
`check_and_fix_ci` waits for a CI run triggered by it — roughly one extra CI cycle on such a
round. This is not avoidable while fixing the reported bug: the log write has to be committed
before the rebase (that *is* the bug), and any commit reaching the remote re-triggers CI.
It is also strictly more correct than today's behaviour, which declares the round green on a CI
run for a commit that is not the branch head, then pushes the log commit afterwards untested.

### `pending_log`

- Declare `pending_log: Path | None = None` as a local of `body`, immediately before the loop
  (next to the existing `sha_before`/loop setup). It is assigned inside the same function scope,
  so no `nonlocal` is needed.
- `write_round_log` already **returns the log path**, so line 575 becomes
  `pending_log = write_round_log(...)`. No path recomputation, no new helper in `review_log.py`.
- Only the non-terminal site at line 575 is captured. Every terminal `write_round_log` is
  already followed by its own `_flush_round_log` (directly or inside `_route_to_human`) and
  returns before the next iteration, so those sites are left exactly as they are.
- Clear `pending_log` unconditionally after the attempt: one attempt per round: the round's own
  write reassigns it at line 575.

### Ordering is load-bearing

The flush must precede `sha_before = get_latest_commit_sha(...)`. If it ran after, a flush that
commits something would advance HEAD past the captured SHA and the round's "applied vs no-op"
label (`core.py:578-583`) would always read "applied" even when the round's own fix changed
nothing. Record that in a short comment at the call.

### Docstring rewrite (`handoff.py:124-141`)

The current docstring is wrong on two counts once this step lands and must be rewritten, not
extended:

- "the *terminal paths* call this" — the round loop's entry point now calls it too, for the
  *previous* round's write. Describe both callers.
- "the push is skipped when the commit did not succeed" — the push is now also skipped when the
  commit succeeded but committed nothing (`commit_hash is None`), when `only=` refuses because
  the pending set is not just that file, and whenever `push=False`.

Document the two new flags under `Args:` and keep the existing "best-effort, never raises"
statement: `get_full_status` returns `{}` rather than raising for a non-repo, and the whole body
stays inside the existing broad `try/except`.

### Test fixture

`tests/workflows/review/conftest.py`'s `env` fixture must gain a `handoff.get_full_status` mock
— without it the new `only=` check runs against the real (non-repo) `tmp_path`, `get_full_status`
returns `{}`, and the top-of-loop flush would silently never commit in any test:

```python
mocks.get_full_status = MagicMock(
    return_value={
        "staged": [],
        "modified": ["pr_info/implementation_review_log_1.md"],
        "untracked": [],
    }
)
monkeypatch.setattr(handoff, "get_full_status", mocks.get_full_status)
```

That path is what the lane actually writes: `REVIEW_IMPLEMENTATION.log_stem` is
`"implementation"` and `next_run_number` allocates `1` on a fresh `tmp_path`. Individual tests
override the return value.

`tests/workflows/review/test_core.py` defines its **own** duplicate `env` fixture and `_run`
(plan lane) and does not need the mock: with `get_full_status` unpatched the guard simply
refuses, which changes none of its assertions (every flush assertion there is
`assert_called()`, satisfied by the terminal flush). Leave that file untouched.

## ALGORITHM

`handoff._flush_round_log`, inside the existing `try:`:

```
if only is not None:
    pending = set(status["staged"] + status["modified"] + status["untracked"])
    rel = only.relative_to(project_dir).as_posix()
    if pending == set():        debug("nothing pending"); return
    if pending != {rel}:        warn("unexpected pending changes besides the round log - "
                                     "not committing"); return
result = commit_all_changes(message, project_dir)
if not result["success"]:          warn; return          # unchanged
if result["commit_hash"] is None:  debug("nothing to commit"); return   # NEW
if not push:                       return                # NEW
if not push_changes(project_dir):  warn                  # unchanged
```

- Index `result["commit_hash"]` directly, not `.get(...)`: `CommitResult` is a `TypedDict` that
  declares the key, so mypy resolves it as `Optional[str]`. The `success: False` branch returns
  first, so the existing test mock that omits the key is unaffected.
- The "nothing pending" and "unexpected dirt" branches are deliberately different levels: an
  empty set is a normal no-op (**debug**), unrelated dirt is the condition step 2's guard will
  turn into a handoff (**warning**).

`core.py` loop:

```
pending_log = None
for each round:
    if pending_log: flush it, scoped, without pushing   # self-healing checkpoint
    pending_log = None
    capture sha_before                                  # AFTER the flush, never before
    ... reviewer -> supervisor -> verdict -> after-steps ...
    pending_log = write_round_log(...)                  # left uncommitted on purpose
```

## DATA

- `_flush_round_log` still returns `None` and never raises; no new failure path, no new return
  value, no change to any exit code, no change to any existing call site.
- Round 1 never flushes: `pending_log` is `None`.
- A round whose tree carries unrelated dirt is *not* repaired: the round proceeds, and its
  rebase attempt is refused by step 2's guard with a warning naming the cause. That is the
  intended loud failure, not a regression.

## TDD

1. `test_flush_no_commit_skips_push` — patch `commit_all_changes` to return
   `{"success": True, "commit_hash": None, "error": None, "error_category": None}` and
   `push_changes` to a `MagicMock`. Call with no `only=`. Assert `push.assert_not_called()` and
   that no `logging.WARNING` record was emitted (this is what distinguishes the new quiet path
   from the existing `success: False` path, which does warn).
2. `test_flush_only_refuses_unrelated_dirt` — patch `handoff.get_full_status` to report the log
   file **and** `src/foo.py` as modified; call `_flush_round_log(tmp_path, only=log_path)`.
   Assert `commit_all_changes.assert_not_called()`, `push.assert_not_called()` and that a
   `logging.WARNING` was emitted. Add the mirror assertion in the same test or a parametrised
   case: with only the log file pending, the commit **is** made.
3. `test_tasks_round_flushes_log_before_next_round_rebase` — drive a two-round run, round 1
   `tasks` (three `prompt_llm` responses: reviewer, `_TASKS`, reviewer resume) then round 2
   `dismiss` (two: reviewer, `_DISMISS`), and record how many commits had happened at each
   rebase attempt:

   ```python
   at_rebase: list[tuple[int, int]] = []

   def _rebase(_project_dir: Path) -> bool:
       at_rebase.append(
           (env.commit_all_changes.call_count, env.flush_push.call_count)
       )
       return True

   env.attempt_rebase_and_push.side_effect = _rebase
   env.prompt_llm.side_effect = [
       _reviewer(), _resp(_TASKS), _reviewer(session_id="rev-1"),  # round 1
       _reviewer(), _resp(_DISMISS),                               # round 2
   ]

   assert _run(tmp_path) == 0
   # Round 1 has nothing pending; round 2's rebase sees round 1's round-log
   # write already committed - and never pushed by the flush itself.
   # Today both commit counts read 0 - that is the bug.
   assert at_rebase == [(0, 0), (1, 0)]
   ```

   Sampling both counters *inside* the rebase mock is what makes the push assertion meaningful:
   round 2's terminal flush (`core.py:337`) does push, but it runs after the last rebase, so a
   post-`_run` assertion on `flush_push` would say nothing about the top-of-loop call. Confirm
   the test fails before the source change (`[(0, 0), (0, 0)]`).
4. `test_round_starting_dirty_for_another_reason_is_not_committed` — same two-round drive, but
   override `env.get_full_status` to report `src/foo.py` modified alongside the log file.
   Assert `env.commit_all_changes` was **not** called by the top-of-loop flush (compare the
   count at round 2's rebase, which must stay `0`) and that a `logging.WARNING` naming the
   unexpected pending change was emitted. The run still returns `0` because the rebase mock
   returns `True`; step 2's guard is what turns that into a handoff in production.
5. Implement the source changes. Confirm all four new tests pass and the five existing
   `_flush_round_log` tests plus the whole `tests/workflows/review/` suite still pass unedited.

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

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 only, test-first, as a single commit.
>
> In `src/mcp_coder/workflows/review/handoff.py`, give `_flush_round_log` two keyword-only
> flags, `only: Path | None = None` and `push: bool = True`, both defaulting to today's
> behaviour. `only=` uses `get_full_status` (via the `mcp_coder.mcp_workspace_git` shim) to
> commit **only** when the sole pending change is that one file — refusing with a warning
> otherwise, so an arbitrarily dirty tree is never committed under "Add review round log".
> Also skip the push when `commit_all_changes` reports `commit_hash is None`, and when
> `push=False`. **Rewrite** the function's docstring: it is no longer only the terminal paths
> that call it, and the push is no longer skipped only when the commit failed.
>
> In `src/mcp_coder/workflows/review/core.py`, track the non-terminal round-log write in a
> `pending_log` local (`write_round_log` returns the path) and flush it as the first statement
> inside the round loop with `only=pending_log, push=False` — **above**
> `sha_before = get_latest_commit_sha(project_dir)`; the ordering is load-bearing, explain it in
> a short comment. `_flush_round_log` is already imported. Leave all existing terminal flush
> calls in place.
>
> Add two tests to the `_flush_round_log` section of `tests/workflows/review/test_handoff.py`
> and two to `tests/workflows/review/test_core_after_steps.py` (flush-before-next-round's-rebase,
> and a round starting dirty for an unrelated reason that must **not** be committed), written
> before the source changes. Add the `handoff.get_full_status` mock to the `env` fixture in
> `tests/workflows/review/conftest.py`; do not edit any existing test and do not touch
> `tests/workflows/review/test_core.py`. Run `run_format_code`, then pylint / pytest
> (`-n auto`) / mypy, and produce a single commit.
