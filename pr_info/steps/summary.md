# Summary — Issue #1158

**Title:** review-implementation: successful tasks round leaves round-log write uncommitted, breaks next round's rebase

## Problem

In `workflows/review/core.py`, every terminal `write_round_log(...)` call site is paired with
`_flush_round_log(project_dir)` (directly, or inside `_route_to_human`) — **except one**: the
successful-`tasks` path at the bottom of the round loop (`core.py:569-583`). That round's log
entry is appended to `pr_info/{log_stem}_review_log_{n}.md` and then left uncommitted in the
working tree while the loop starts the next round.

If that next round's verdict is `dismiss`, the `dismiss` branch calls `_after_steps(...,
is_dismiss=True)`, which goes straight into `_attempt_rebase_and_push` with no working-tree
check. The leftover uncommitted log edit makes `git rebase` refuse with
`error: cannot rebase: You have unstaged changes`, and the run bounces to human handoff.

The bug is silent whenever the following round is *also* `tasks`, because that round's own
`commit_changes` step sweeps up the previous round's stray log edit.

## Fix — two independent changes

1. **Land the previous round's log write at the top of each round** (`core.py` + `handoff.py`).
   The non-terminal `write_round_log` result is kept in a `pending_log` local (the function
   already returns the path), and the first statement inside the round loop — **above**
   `sha_before = get_latest_commit_sha(...)` — flushes it. A single self-healing checkpoint at
   the loop entry lands whatever the previous round left pending before any new-round work
   (including a rebase attempt) can be affected by it. This is chosen over pairing every
   `write_round_log` call site with its own flush — that is the pattern that produced this bug.

   The flush is **scoped and push-free**, via two new keyword-only flags on `_flush_round_log`
   (`only=`, `push=False`) that both default to today's behaviour so no terminal call site
   changes. See *Architectural / design changes* for why each matters.

2. **Dirty-tree tripwire in `_attempt_rebase_and_push`** (`workflow_steps/rebase.py`, shared by
   the `review` and `implement` workflows). Before attempting a rebase, check for uncommitted
   changes git would actually refuse on; when present, log a clear warning naming the *cause*
   and return `False` rather than letting git fail first with only raw stderr. A backstop for
   any future stray write, including the unrelated-dirt case item 1 deliberately declines to
   commit.

## Architectural / design changes

**A new loop invariant, not a new mechanism.** No module or class is added; one private helper
gains two defaulted keyword-only flags. The change to `core.py` establishes an invariant that
did not previously exist:

> *A review round never begins on a working tree carrying a previous round's pending write.*

Responsibility for landing a round-log entry moves from "each `write_round_log` call site must
remember to pair itself with a flush" to "the loop entry point flushes what is pending". The
terminal call sites keep their own flushes (they return before reaching the next loop iteration,
so there is no top-of-loop flush to rely on), but the *non-terminal* site no longer needs one.
This converts a per-call-site correctness obligation — violated once, and liable to be violated
again — into a single structural guarantee.

**Ordering is load-bearing.** The flush must precede `sha_before = get_latest_commit_sha(...)`.
If it ran after, a flush that actually commits something would advance HEAD past the captured
SHA, and the round's "applied vs no-op" log label (`core.py:578-583`) would always read
"applied" even when the round's own fix changed nothing.

**The top-of-loop commit is scoped to the round-log file (`only=`).** `commit_all_changes` stages
and commits *everything*. Calling it unconditionally every round would auto-commit any unrelated
dirt under the message "Add review round log" — the behaviour rejected below. `only=` makes the
helper compare `get_full_status`'s pending set (staged + modified + untracked, since a first-run
log file is untracked) against that one path and refuse otherwise, with a warning. Unrelated
dirt is therefore *not* silently repaired: the round proceeds and item 2's tripwire turns it into
a loud, diagnosable handoff.

**The top-of-loop commit does not push (`push=False`).** The commit is what unblocks the rebase;
the round's own push carries it moments later (`core.py:484` on the `tasks` path,
`_attempt_rebase_and_push`'s force-with-lease push on `dismiss`, or a terminal flush on a failing
path). Accepted residual cost: on a `dismiss` round whose rebase is a no-op, that push now
carries a log-only commit to the remote *before* the CI gate, so `check_and_fix_ci` waits for a
CI run triggered by it — about one extra CI cycle on such a round. It is not avoidable while
fixing this bug (the log write must be committed before the rebase, and any commit reaching the
remote re-triggers CI), and it is strictly more correct than today's behaviour, which declares
the round green on a CI run for a commit that is not the branch head and then pushes the log
commit afterwards untested. Covered in step 1's verification.

**`_flush_round_log` becomes idempotent-on-clean.** Skipping the push when `commit_hash is None`
separates two outcomes `commit_all_changes` collapses into one truthy `success`: "committed
something" and "there was nothing to commit". Its docstring is rewritten, not extended: it is no
longer only the terminal paths that call it, and the push is no longer skipped only when the
commit failed.

**`workflow_steps/rebase.py` gains a precondition guard.** The guard is additive: both callers
already treat a `False` return exactly as they do today (`implement/core.py:104` ignores it and
proceeds; `review/steps.py:105` maps it to the `"rebase"` needs-human reason), so no behaviour or
signature change reaches either caller. Failure diagnosis moves one layer up — the workflow layer
names the cause it can recognise, instead of surfacing git's generic stderr.

It models git's *actual* precondition rather than `is_working_directory_clean`'s stricter one:
that function counts untracked files as dirty, while `git rebase` tolerates them, so a raw
verdict would skip rebases that would have succeeded and turn green runs into handoffs. The guard
therefore skips only on staged/modified entries, and passes
`ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS` to match every other control-flow call site
(`prerequisites.py:34`, `create_plan/core.py:492`, `create_pr/core.py:566`,
`set_status.py:264`). It swallows the `ValueError` that `is_working_directory_clean` raises on a
non-git-repo path and proceeds with the rebase attempt, preserving the function's documented
"never fails workflow" contract.

## Decided against

- Auto-committing whatever is dirty before a rebase attempt — masks the cause if a similar gap
  reappears; the tripwire should fail loudly rather than repair silently. This is why the
  top-of-loop commit is scoped with `only=` instead of being a bare `commit_all_changes`.
- Merging `write_round_log` and `_flush_round_log` into one function — touches ~10 call sites
  for no benefit once the top-of-loop flush exists.
- A separate step for the `_flush_round_log` changes — they exist only to serve the new
  top-of-loop call, so they land in the same commit (`planning_principles.md`, "merge tiny or
  intertwined steps").
- A path helper in `review_log.py` — `write_round_log` already returns the log path, so the loop
  stores it rather than recomputing it.
- Surfacing the dirty-file list into the human-handoff issue comment — logs are enough.
- Enumerating the specific dirty files in the new rebase warning — file-level detail is left to
  `mcp-workspace#295`'s hardening of `rebase_onto_branch`, so the two fixes do not duplicate the
  same logic at two layers.
- A documentation change. The flush invariant is a fact about one loop; it lives in the code
  comment at the flush site and in `_flush_round_log`'s rewritten docstring.
  `docs/architecture/architecture.md`'s `workflows/review/` bullet is a module inventory and
  gains nothing from it.

## Deviation from the issue text

Issue #1158's *Fix* item 1 prescribes a bare `_flush_round_log(project_dir)` at the top of the
loop. That is an unconditional `commit_all_changes`, which contradicts the issue's own
"decided against auto-committing whatever is dirty" and would commit unrelated dirt under the
round-log commit message. The plan keeps the issue's placement and rationale but scopes the
commit (`only=`) and drops its push (`push=False`). The issue may want updating to match.

## Related (not blocking)

`mcp-workspace#295` — hardening `rebase_onto_branch` to log the specific dirty files at the
library layer. Log-message-only, no interface change; the two fixes are independent.

## Files created / modified

### Modified — source

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/review/handoff.py` | `_flush_round_log`: `only=` scope guard, `push=` flag, `commit_hash is None` push skip, docstring rewrite (step 1) |
| `src/mcp_coder/workflows/review/core.py` | `pending_log` local; scoped push-free flush at the top of the round loop, above `sha_before` (step 1) |
| `src/mcp_coder/workflow_steps/rebase.py` | `_attempt_rebase_and_push`: dirty-working-tree guard + `_has_uncommitted_tracked_changes` helper (step 2) |

### Modified — tests

| File | Change |
|------|--------|
| `tests/workflows/review/conftest.py` | `env` fixture: add a `handoff.get_full_status` mock (step 1) |
| `tests/workflows/review/test_handoff.py` | Two tests: `commit_hash is None` skips the push; `only=` refuses unrelated dirt (step 1) |
| `tests/workflows/review/test_core_after_steps.py` | Two tests: round 1 `tasks` flushes before round 2's rebase; a round starting dirty for another reason is not committed (step 1) |
| `tests/workflow_steps/test_rebase.py` | Four tests: dirty tree skips the rebase; untracked-only still rebases; clean tree rebases; non-git-repo path exercises the real `ValueError` swallow (step 2) |

### Not modified

- No new modules, packages or `__init__.py` files.
- No documentation changes (see *Decided against*).
- No existing test is edited. In `tests/workflow_steps/test_rebase.py` the `ValueError` swallow
  keeps all **8** existing tests passing untouched — the 5 in `TestRebaseIntegration` run
  against `Path("/test")`, which is not a git repository, and the 3 in
  `TestGetRebaseTargetBranch` never reach the guard.
- `tests/workflows/review/test_core.py`, which defines its own duplicate `env` fixture and
  `_run` (plan lane), needs no change: with `get_full_status` unpatched there the scoped flush
  simply refuses, and every flush assertion in that file is `assert_called()`, satisfied by its
  terminal flush.

## Step order

The two steps are independent and may land in either order.

| Step | Scope |
|------|-------|
| [step_1.md](./step_1.md) | Scoped, push-free `_flush_round_log` at the top of the review round loop |
| [step_2.md](./step_2.md) | Dirty-working-tree guard in `_attempt_rebase_and_push` |

## Checks (every step)

`run_format_code`, then `run_pylint_check`, `run_pytest_check` (`-n auto`, unit markers
excluded), `run_mypy_check`. All must pass before the step's single commit.
