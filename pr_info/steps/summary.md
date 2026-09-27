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

1. **Flush at the top of each round** (`core.py`). Call `_flush_round_log(project_dir)` as the
   first statement inside the round loop, **above** `sha_before = get_latest_commit_sha(...)`.
   A single self-healing checkpoint at the loop entry commits+pushes whatever the previous
   round left pending, whichever branch caused it, before any new-round work (including a
   rebase attempt) can be affected by it. This is chosen over pairing every `write_round_log`
   call site with its own flush — that is the pattern that produced this bug.

   Prerequisite: `_flush_round_log` must skip its push when nothing was actually committed
   (`commit_all_changes` reports `commit_hash is None`), otherwise the new per-round call
   fires a redundant no-op `git push` on every round.

2. **Dirty-tree tripwire in `_attempt_rebase_and_push`** (`workflow_steps/rebase.py`, shared by
   the `review` and `implement` workflows). Check `is_working_directory_clean(project_dir)`
   before attempting a rebase; when dirty, log a clear warning naming the *cause* and return
   `False` rather than letting git fail first with only raw stderr. A backstop for any future
   stray write, not just the round-log path fixed by item 1.

## Architectural / design changes

**A new loop invariant, not a new mechanism.** No module, class, or function signature is added
or changed. The change to `core.py` establishes an invariant that did not previously exist:

> *A review round never begins on a working tree carrying a previous round's pending write.*

Responsibility for landing a round-log entry moves from "each `write_round_log` call site must
remember to pair itself with a flush" to "the loop entry point flushes whatever is pending".
The terminal call sites keep their own flushes (they return before reaching the next loop
iteration, so there is no top-of-loop flush to rely on), but the *non-terminal* site no longer
needs one. This converts a per-call-site correctness obligation — which was violated once and
would be violated again — into a single structural guarantee.

**Ordering is load-bearing.** The flush must precede `sha_before = get_latest_commit_sha(...)`.
If it ran after, a flush that actually commits something would advance HEAD past the captured
SHA, and the round's "applied vs no-op" log label (`core.py:578-583`) would always read
"applied" even when the round's own fix changed nothing.

**`_flush_round_log` becomes idempotent-on-clean.** Skipping the push when
`commit_hash is None` is what makes the helper safe to call unconditionally on every round
rather than only on terminal paths. Semantically it separates two outcomes that
`commit_all_changes` currently collapses into one truthy `success`: "committed something" and
"there was nothing to commit".

**`workflow_steps/rebase.py` gains a precondition guard.** The guard is additive: both callers
already treat a `False` return exactly as they do today (`implement/core.py:104` ignores it and
proceeds; `review/steps.py:105` maps it to the `"rebase"` needs-human reason), so no behavior
or signature change reaches either caller. Failure diagnosis moves one layer up — the workflow
layer now names the cause it can recognise, instead of surfacing git's generic stderr.

The guard swallows the `ValueError` that `is_working_directory_clean` raises on a non-git-repo
path and proceeds with the rebase attempt, preserving the function's documented "never fails
workflow" contract.

## Decided against

- Auto-committing whatever is dirty before a rebase attempt — masks the cause if a similar gap
  reappears; the tripwire should fail loudly rather than repair silently.
- Merging `write_round_log` and `_flush_round_log` into one function — touches ~10 call sites
  for no benefit once the top-of-loop flush exists.
- Surfacing the dirty-file list into the human-handoff issue comment — logs are enough.
- Enumerating the specific dirty files in the new warning — file-level detail is left to
  `mcp-workspace#295`'s hardening of `rebase_onto_branch`, so the two fixes do not duplicate
  the same logic at two layers.
- A documentation change. The flush invariant is a two-line fact about one loop; it lives in
  the code comment at the flush site. `docs/architecture/architecture.md`'s `workflows/review/`
  bullet is a module inventory and gains nothing from it.

## Related (not blocking)

`mcp-workspace#295` — hardening `rebase_onto_branch` to log the specific dirty files at the
library layer. Log-message-only, no interface change; the two fixes are independent.

## Files created / modified

### Modified — source

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/review/handoff.py` | `_flush_round_log`: skip the push when `commit_hash is None` (step 1) |
| `src/mcp_coder/workflows/review/core.py` | `_flush_round_log(project_dir)` at the top of the round loop, above `sha_before` (step 2) |
| `src/mcp_coder/workflow_steps/rebase.py` | `_attempt_rebase_and_push`: dirty-working-tree guard clause (step 3) |

### Modified — tests

| File | Change |
|------|--------|
| `tests/workflows/review/test_handoff.py` | One test: `commit_hash is None` skips the push (step 1) |
| `tests/workflows/review/test_core_after_steps.py` | One test: round 1 `tasks` flushes before round 2's rebase (step 2) |
| `tests/workflow_steps/test_rebase.py` | Two tests: dirty tree skips the rebase; clean tree is unaffected (step 3) |

### Not modified

- No new modules, packages or `__init__.py` files.
- No documentation changes (see *Decided against*).
- No existing test is edited. The `ValueError` swallow in step 3 keeps the five existing tests
  in `tests/workflow_steps/test_rebase.py` passing untouched — they run against
  `Path("/test")`, which is not a git repository.
- `tests/workflows/review/conftest.py` needs no change: its `env` fixture already mocks
  `handoff.commit_all_changes` (returning a non-`None` `commit_hash`), `handoff.push_changes`,
  `steps._attempt_rebase_and_push` and `core.get_latest_commit_sha` (a constant, so the new
  flush cannot perturb the `sha_before` comparison).

## Step order

Steps 1 → 2 are ordered: the `commit_hash` guard must land before the flush becomes a
per-round call, or step 2 introduces a no-op push on every round. Step 3 is independent of
both and may land in any position.

| Step | Scope |
|------|-------|
| [step_1.md](./step_1.md) | `_flush_round_log` skips the push when nothing was committed |
| [step_2.md](./step_2.md) | Top-of-loop `_flush_round_log` call in the review round loop |
| [step_3.md](./step_3.md) | Dirty-working-tree guard in `_attempt_rebase_and_push` |

## Checks (every step)

`run_format_code`, then `run_pylint_check`, `run_pytest_check` (`-n auto`, unit markers
excluded), `run_mypy_check`. All must pass before the step's single commit.
