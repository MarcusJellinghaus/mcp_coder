# Step 1 — Land the previous round's round-log write at the top of each round

Read [summary.md](./summary.md) first.

This is the fix for the reported failure: round 1 `tasks` (clean) leaves its round-log write
uncommitted, round 2 `dismiss` attempts a rebase, git refuses with "You have unstaged changes".

One step, one commit: the `_flush_round_log` changes and the one-line shim re-export exist only to
serve the new top-of-loop call, so they are not worth a commit of their own
(`planning_principles.md`, "merge tiny or intertwined steps").

## WHERE

- Source: `src/mcp_coder/mcp_workspace_git.py` — the
  `mcp_workspace.git_operations.staging` import (currently `stage_all_changes` alone) and
  `__all__`.
- Source: `src/mcp_coder/workflows/review/handoff.py` — `_flush_round_log` (signature at line
  123, docstring 124-141, body 142-153).
- Source: `src/mcp_coder/workflows/review/core.py` — inside `run_review_workflow.body`: the
  round loop opening at line 127 and the non-terminal `write_round_log(...)` at line 575.
- Test: `tests/workflows/review/test_handoff.py` — the `# --- _flush_round_log ---` section,
  after `test_flush_swallows_push_raise` (the last of the **five** existing tests in that
  section: lines 26, 42, 58, 74, 90).
- Test: `tests/workflows/review/test_core_after_steps.py` — appended at the end of the file.
- Fixture: `tests/workflows/review/conftest.py` — the `env` fixture gains two mocks (see HOW).

## WHAT

One line in the shim, so the staging primitive is importable the way this repo requires:

```python
from mcp_workspace.git_operations.staging import stage_all_changes, stage_specific_files
```

plus `"stage_specific_files"` in `__all__`.

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

New imports in `handoff.py`, extending the existing shim import:

```python
from mcp_coder.mcp_workspace_git import (
    commit_all_changes,
    commit_staged_files,
    stage_specific_files,
)
```

Three new tests:

```python
# tests/workflows/review/test_handoff.py
def test_flush_no_commit_skips_push(...) -> None:
def test_flush_only_commits_just_the_log(...) -> None:   # parametrised on the staging result
# tests/workflows/review/test_core_after_steps.py
def test_tasks_round_flushes_log_before_next_round_rebase(...) -> None:
```

## HOW

### `only=` — stage that one path and commit the index, nothing else

`commit_all_changes` stages and commits **everything**. Calling it unconditionally at the top of
every round would auto-commit any unrelated dirt under the message "Add review round log" —
precisely the behaviour rejected in summary.md's *Decided against* list. `only=` therefore does
not call it: it stages exactly that one path and commits the index.

- `stage_specific_files([only], project_dir)` is the primitive (mcp_workspace's staging module,
  re-exported through the shim by this step). It accepts **absolute or relative** paths,
  validates the path is inside `project_dir`, and uses `repo.index.add`, so a first-run
  **untracked** log file stages exactly like a modified one. It returns `bool` and never raises;
  `False` (not a repository, path outside the project, file missing) is warned and the flush
  returns without committing.
- `commit_staged_files(message, project_dir)` then commits. It returns the same `CommitResult`
  `TypedDict` as `commit_all_changes`, so the existing success/push tail is shared unchanged.
- No status read, no pending-set comparison, no ignore list: the commit is narrow **by
  construction** rather than by a guard that has to enumerate what counts as "dirt". Unrelated
  dirt is never swept in, and it never stops the round log from landing — it simply stays in the
  working tree, where step 2's rebase tripwire names it.
- `commit_staged_files` commits the **whole index**, so anything a previous step left staged
  would ride along. That cannot arise inside the loop — the round's own commit steps leave an
  empty index — and it is no broader than the terminal paths' existing `commit_all_changes`.
- `commit_staged_files` reports `success: False` ("No staged files to commit") when the staged
  path turns out to hold no change; the existing falsy-commit branch already warns on that. The
  state is unreachable from the loop: `pending_log` is set only by the immediately preceding
  `write_round_log`, and nothing between it and the next iteration commits.

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

- Declare `pending_log: Path | None = None` as a local of `body`, immediately before the round
  loop at `core.py:127`. It is assigned inside the same function scope, so no `nonlocal` is
  needed.
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

(Independently, landing the previous round's write also *fixes* that label for rounds 2+: today
the uncommitted log makes `is_working_directory_clean` at `core.py:574` report dirty, so every
round after the first reads "applied". The label is informational only — no control flow depends
on it — but expect the log wording to change on no-op rounds.)

### Docstring rewrite (`handoff.py:124-141`)

The current docstring is wrong on two counts once this step lands and must be rewritten, not
extended:

- "the *terminal paths* call this" — the round loop's entry point now calls it too, for the
  *previous* round's write. Describe both callers.
- "the push is skipped when the commit did not succeed" — the push is now also skipped when the
  commit succeeded but committed nothing (`commit_hash is None`), when `only=` could not stage
  the path, and whenever `push=False`.

Document the two new flags under `Args:` — including that `only=` commits *only* that path, via
`stage_specific_files` + `commit_staged_files`, rather than the whole tree — and keep the existing
"best-effort, never raises" statement: both new calls report failure by return value, and the
whole body stays inside the existing broad `try/except`.

### Test fixture

`tests/workflows/review/conftest.py`'s `env` fixture must gain `handoff.stage_specific_files`
and `handoff.commit_staged_files` mocks — without them the scoped flush runs against the real
(non-repo) `tmp_path`, `stage_specific_files` returns `False`, and the top-of-loop flush would
silently never commit in any test:

```python
mocks.stage_specific_files = MagicMock(return_value=True)
monkeypatch.setattr(handoff, "stage_specific_files", mocks.stage_specific_files)
mocks.commit_staged_files = MagicMock(
    return_value={
        "success": True,
        "commit_hash": "LOGSHA",
        "error": None,
        "error_category": None,
    }
)
monkeypatch.setattr(handoff, "commit_staged_files", mocks.commit_staged_files)
```

Unlike a status mock, neither has to agree with the log path the lane happens to allocate, so the
fixture carries no coupling to `REVIEW_IMPLEMENTATION.log_stem` or `next_run_number`.

`tests/workflows/review/test_core.py` defines its **own** duplicate `env` fixture and `_run`
(plan lane) and is left untouched: with `stage_specific_files` unpatched there it returns `False`
on the non-repo `tmp_path`, so the scoped flush warns and commits nothing, which changes none of
its assertions (every flush assertion there is `assert_called()` on `commit_all_changes`,
satisfied by the terminal flush). If an assertion there turns out to be sensitive to the extra
warning, add the same two mocks to that fixture and report it rather than loosening the
assertion.

## ALGORITHM

`handoff._flush_round_log`, inside the existing `try:`:

```
if only is not None:
    if not stage_specific_files([only], project_dir):
        warn("could not stage the round log - not committing"); return
    result = commit_staged_files(message, project_dir)
else:
    result = commit_all_changes(message, project_dir)
if not result["success"]:          warn; return          # unchanged
if result["commit_hash"] is None:  debug("nothing to commit"); return   # NEW
if not push:                       return                # NEW
if not push_changes(project_dir):  warn                  # unchanged
```

- Index `result["commit_hash"]` directly, not `.get(...)`: `CommitResult` is a `TypedDict` that
  declares the key, so mypy resolves it as `Optional[str]`. The `success: False` branch returns
  first, so the existing test mock that omits the key is unaffected.
- Only the `commit_all_changes` branch can return `success: True` with `commit_hash: None` (it
  treats an empty tree as a successful no-op); `commit_staged_files` reports an empty index as
  `success: False`. Both land in the shared tail, so neither needs its own branch.

`core.py` loop:

```
pending_log = None
for each round:
    if pending_log: flush it, scoped to that path, without pushing   # self-healing checkpoint
    pending_log = None
    capture sha_before                                  # AFTER the flush, never before
    ... reviewer -> supervisor -> verdict -> after-steps ...
    pending_log = write_round_log(...)                  # left uncommitted on purpose
```

## DATA

- `_flush_round_log` still returns `None` and never raises; no new failure path, no new return
  value, no change to any exit code, no change to any existing call site.
- Round 1 never flushes: `pending_log` is `None`.
- Unrelated dirt neither blocks the round log from landing nor gets swept into its commit: only
  `pending_log` is staged. The dirt stays in the working tree and step 2's guard refuses that
  round's rebase with a warning naming the cause.
- No ignore-list question arises on this side: a regenerated `uv.lock` is simply not staged.

## TDD

1. `test_flush_no_commit_skips_push` — patch `commit_all_changes` to return
   `{"success": True, "commit_hash": None, "error": None, "error_category": None}` and
   `push_changes` to a `MagicMock`. Call with no `only=`. Assert `push.assert_not_called()` and
   that no `logging.WARNING` record was emitted (this is what distinguishes the new quiet path
   from the existing `success: False` path, which does warn).
2. `test_flush_only_commits_just_the_log` — patch `handoff.stage_specific_files`,
   `handoff.commit_staged_files`, `handoff.commit_all_changes` and `handoff.push_changes`, then
   call `_flush_round_log(tmp_path, only=log_path)`. Parametrise on the staging result:

   - staging `True` → `stage_specific_files` called once with `([log_path], tmp_path)`,
     `commit_staged_files` called with the message, `commit_all_changes.assert_not_called()`
     (an arbitrarily dirty tree can never be committed under "Add review round log"), and the
     push fired.
   - staging `False` → `commit_staged_files.assert_not_called()`, `push.assert_not_called()`,
     and a `logging.WARNING` was emitted.
3. `test_tasks_round_flushes_log_before_next_round_rebase` — drive a two-round run, round 1
   `tasks` (three `prompt_llm` responses: reviewer, `_TASKS`, reviewer resume) then round 2
   `dismiss` (two: reviewer, `_DISMISS`), and record how many round-log commits had happened at
   each rebase attempt:

   ```python
   at_rebase: list[tuple[int, int]] = []

   def _rebase(_project_dir: Path) -> bool:
       at_rebase.append(
           (env.commit_staged_files.call_count, env.flush_push.call_count)
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
   # Only the round log was staged - unrelated dirt could not ride along.
   assert env.stage_specific_files.call_args.args == (
       [tmp_path / "pr_info" / "implementation_review_log_1.md"],
       tmp_path,
   )
   ```

   Sampling both counters *inside* the rebase mock is what makes the push assertion meaningful:
   round 2's terminal flush (`core.py:337`) does push, but it runs after the last rebase, so a
   post-`_run` assertion on `flush_push` would say nothing about the top-of-loop call. The path
   assertion holds after the run because the top-of-loop flush is the only `only=` caller.
   Confirm the test fails before the source change (`[(0, 0), (0, 0)]`).
4. Implement the source changes. Confirm all three new tests pass and the five existing
   `_flush_round_log` tests plus the whole `tests/workflows/review/` suite still pass unedited.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/workflows/review/"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_lint_imports_check
```

`run_lint_imports_check` matters because this step touches the `mcp_workspace_git` shim: the new
staging primitive must be imported through it, never from `mcp_workspace` directly.

Existing review tests are expected to pass unchanged: every assertion on the flush uses
`assert_called()`, not `assert_called_once()`. If any turns out to assert an exact count,
report it rather than silently loosening the assertion.

Then the full unit suite, then **one commit** for this step.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 only, test-first, as a single commit.
>
> In `src/mcp_coder/mcp_workspace_git.py`, add `stage_specific_files` to the
> `mcp_workspace.git_operations.staging` import and to `__all__`.
>
> In `src/mcp_coder/workflows/review/handoff.py`, give `_flush_round_log` two keyword-only
> flags, `only: Path | None = None` and `push: bool = True`, both defaulting to today's
> behaviour. When `only=` is given, do **not** call `commit_all_changes`: call
> `stage_specific_files([only], project_dir)` and then `commit_staged_files(message,
> project_dir)`, so the commit contains exactly that one path and an arbitrarily dirty tree can
> never be committed under "Add review round log". A `False` staging result warns and returns
> without committing. Both functions come from the `mcp_coder.mcp_workspace_git` shim, and
> `commit_staged_files` returns the same `CommitResult` as `commit_all_changes`, so the existing
> success/push tail is shared. Also skip the push when the commit reports `commit_hash is None`,
> and when `push=False`. **Rewrite** the function's docstring: it is no longer only the terminal
> paths that call it, and the push is no longer skipped only when the commit failed.
>
> In `src/mcp_coder/workflows/review/core.py`, track the non-terminal round-log write in a
> `pending_log` local (`write_round_log` returns the path) and flush it as the first statement
> inside the round loop with `only=pending_log, push=False` — **above**
> `sha_before = get_latest_commit_sha(project_dir)`; the ordering is load-bearing, explain it in
> a short comment. `_flush_round_log` is already imported. Leave all existing terminal flush
> calls in place.
>
> Add two tests to the `_flush_round_log` section of `tests/workflows/review/test_handoff.py`
> (the `commit_hash is None` push skip; `only=` stages and commits just that path, and a failed
> staging commits nothing) and one to `tests/workflows/review/test_core_after_steps.py`
> (flush-before-next-round's-rebase, asserting only the round-log path was staged), written
> before the source changes. Add the `handoff.stage_specific_files` and
> `handoff.commit_staged_files` mocks to the `env` fixture in
> `tests/workflows/review/conftest.py`; do not edit any existing test and do not touch
> `tests/workflows/review/test_core.py`. Run `run_format_code`, then pylint / pytest
> (`-n auto`) / mypy / lint-imports, and produce a single commit.
