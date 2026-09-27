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

1. **Land the previous round's log write at the top of each round** (`core.py`, `handoff.py`, plus
   one re-export line in `mcp_workspace_git.py`).
   The non-terminal `write_round_log` result is kept in a `pending_log` local (the function
   already returns the path), and the first statement inside the round loop — **above**
   `sha_before = get_latest_commit_sha(...)` — flushes it. A single self-healing checkpoint at
   the loop entry lands whatever the previous round left pending before any new-round work
   (including a rebase attempt) can be affected by it. This is chosen over pairing every
   `write_round_log` call site with its own flush — that is the pattern that produced this bug.

   The flush is **scoped and push-free**, via two new keyword-only flags on `_flush_round_log`
   (`only=`, `push=False`) that both default to today's behaviour so no terminal call site
   changes. `only=` stages and commits exactly that one path (`stage_specific_files` +
   `commit_staged_files`) instead of `commit_all_changes`. See *Architectural / design changes*
   for why each matters.

2. **Dirty-tree tripwire in `_attempt_rebase_and_push`** (`workflow_steps/rebase.py`, shared by
   the `review` and `implement` workflows). Before attempting a rebase, check for uncommitted
   changes git would actually refuse on; when present, log a clear warning naming the *cause*
   and return `False` rather than letting git fail first with only raw stderr. A backstop for
   any future stray write, including the unrelated dirt item 1 deliberately leaves in the working
   tree.

## Architectural / design changes

**A new loop invariant, not a new mechanism.** No module or class is added; one private helper
gains two defaulted keyword-only flags and the git shim re-exports one more staging function. The
change to `core.py` establishes an invariant that did not previously exist:

> *A review round never begins with a previous round's round-log write still uncommitted.*

That holds for every *dirt class*, but not for every *failure*. `only=` (below) stages exactly the
round-log path, so whatever else is dirty neither blocks that write from landing nor is swept into
its commit; unrelated dirt stays in the working tree, where item 2's tripwire turns it into a loud,
diagnosable handoff rather than an opaque git error. The flush itself stays **best-effort**,
though: a `False` from `stage_specific_files` (not a repository, file missing) or a
`success: False` from `commit_staged_files` (signing or pre-commit-hook failure) warns and returns,
and the round then *does* begin with the previous round's write still uncommitted — the reported
failure mode, rarer than today and backstopped by item 2, which names it instead of letting git
fail on raw stderr.

Responsibility for landing a round-log entry moves from "each `write_round_log` call site must
remember to pair itself with a flush" to "the loop entry point flushes what the previous round
handed it". The terminal call sites keep their own flushes (they return before reaching the next
loop iteration, so there is no top-of-loop flush to rely on), but the *non-terminal* site no longer
needs one. This **narrows** the per-call-site obligation rather than removing it — see *Deviation
from the issue text* — and item 2 backstops whatever slips through.

**Ordering is load-bearing.** The flush must precede `sha_before = get_latest_commit_sha(...)`.
If it ran after, a flush that actually commits something would advance HEAD past the captured
SHA, and the round's "applied vs no-op" log label (`core.py:578-583`) would always read
"applied" even when the round's own fix changed nothing.

**The top-of-loop commit is scoped to the round-log file (`only=`).** `commit_all_changes` stages
and commits *everything*. Calling it unconditionally every round would auto-commit any unrelated
dirt under the message "Add review round log" — the behaviour rejected below. `only=` therefore
does not call it: it calls `stage_specific_files([only], project_dir)` and then
`commit_staged_files`, so the commit contains exactly that one path. `stage_specific_files` accepts
an absolute path and uses `repo.index.add`, so a first-run *untracked* log file stages exactly like
a modified one; `commit_staged_files` returns the same `CommitResult` as `commit_all_changes`, so
the existing success/push tail is shared. `mcp_workspace_git.py` gains the one re-export line that
makes `stage_specific_files` importable through the shim.

Committing the path directly removes the question the alternative had to answer — which pending
changes count as "dirt" — and with it any `DEFAULT_IGNORED_BUILD_ARTIFACTS` filtering on this side:
a regenerated `uv.lock` is simply not staged. Item 2's guard still does **not** filter that list,
because it answers a different question — *what will git refuse* — and git has no notion of the
list: a modified `uv.lock` blocks a rebase like any other tracked modification.

**The top-of-loop commit does not push (`push=False`).** The commit is what unblocks the rebase;
on every converging path the round's own push carries it moments later (`core.py:484` on the
`tasks` path, `_attempt_rebase_and_push`'s force-with-lease push on `dismiss`, `_route_to_human`'s
flush on `escalate`/rebase/rounds-cap, or one of the terminal flushes that do push). On the four
`_fail` sites that neither write nor flush a round log (`core.py:186`, `201`, `235`, `246`) the
commit stays local and unpushed — accepted; see step_1.md. Accepted residual cost: on a `dismiss`
round whose rebase is a no-op, that push now
carries a log-only commit to the remote *before* the CI gate, so `check_and_fix_ci` waits for a
CI run triggered by it — about one extra CI cycle on such a round. It is not avoidable while
fixing this bug (the log write must be committed before the rebase, and any commit reaching the
remote re-triggers CI), and it is strictly more correct than today's behaviour, which declares
the round green on a CI run for a commit that is not the branch head and then pushes the log
commit afterwards untested. Covered in step 1's verification.

**`_flush_round_log` becomes idempotent-on-clean.** Skipping the push when `commit_hash is None`
separates two outcomes `commit_all_changes` collapses into one truthy `success`: "committed
something" and "there was nothing to commit". (`commit_staged_files`, the `only=` branch, instead
reports an empty index as `success: False`, which the existing falsy-commit branch already warns
on.) Its docstring is rewritten, not extended: it is no longer only the terminal paths that call
it, and the push is no longer skipped only when the commit failed.

**`workflow_steps/rebase.py` gains a precondition guard.** The guard is additive: both callers
already treat a `False` return exactly as they do today (`implement/core.py:104` ignores it and
proceeds; `review/steps.py:105` maps it to the `"rebase"` needs-human reason), so no behaviour or
signature change reaches either caller. Failure diagnosis moves one layer up — the workflow layer
names the cause it can recognise, instead of surfacing git's generic stderr.

It models git's precondition exactly: it skips on **staged or modified** entries and nothing else.
Untracked files are not blocking, because `git rebase` tolerates them and treating them as dirty
would skip rebases that would have succeeded, turning green runs into handoffs.
`DEFAULT_IGNORED_BUILD_ARTIFACTS` is not filtered, because git ignores no such list: filtering it
would leave the tripwire silent on a tree git rejects, and the run would still end on git's raw
stderr. Naming that case is not a regression — `_attempt_rebase_and_push` already returns `False`
for it today; only the log message improves.

`is_working_directory_clean` is deliberately unused. It calls `get_full_status` internally, so as a
pre-filter it costs a second status read on the dirty path rather than saving one, and any tree
with a blocking staged/modified entry is unclean by definition, so it could never veto the refined
verdict. A single `_has_uncommitted_tracked_changes(project_dir)` over `get_full_status` is
therefore both cheaper and sufficient — and since `get_full_status` never raises (it returns
`{"staged": [], "modified": [], "untracked": []}` for a non-git-repo), the guard needs no
`try/except` to keep the function's documented "never fails workflow" contract.

## Decided against

- Auto-committing whatever is dirty before a rebase attempt — masks the cause if a similar gap
  reappears; the tripwire should fail loudly rather than repair silently. This is why the
  top-of-loop commit is scoped with `only=` instead of being a bare `commit_all_changes`.
- Merging `write_round_log` and `_flush_round_log` into one function — touches ~10 call sites
  for no benefit once the top-of-loop flush exists.
- A pending-set guard around `commit_all_changes` for `only=` (compare `get_full_status`'s
  staged + modified + untracked set against the log path, minus
  `DEFAULT_IGNORED_BUILD_ARTIFACTS`, and refuse otherwise) — `stage_specific_files` commits
  exactly that one path with no status read, no ignore-list question and no refusal branch, and
  it lands the round log even when the tree is dirty for another reason.
- `is_working_directory_clean` as a pre-filter in item 2's guard — it calls `get_full_status`
  internally, so it adds a second status read on the dirty path instead of saving one, and it
  cannot veto a blocking staged/modified entry anyway. Dropping it also drops a `try/except
  ValueError` the single-call form does not need.
- Filtering `DEFAULT_IGNORED_BUILD_ARTIFACTS` in item 2's guard, to match the other control-flow
  `is_working_directory_clean` call sites (`prerequisites.py:34`, `create_plan/core.py:492`,
  `create_pr/core.py:566`, `set_status.py:264`) — those ask "may we start work", which tolerates a
  regenerated `uv.lock`. The rebase guard asks "will git start", which does not.
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
commit (`only=` — a staged commit of the round-log path alone) and drops its push (`push=False`).

Issue #1158's *Fix* item 2 prescribes `is_working_directory_clean(project_dir)` as the rebase
precondition check. The plan keeps the issue's intent — a workflow-layer tripwire that names the
cause — but implements it over `get_full_status` instead, because
`is_working_directory_clean` counts untracked files as dirty (which `git rebase` tolerates) and
because it is a redundant second status read either way. The issue may want updating to match on
both counts.

Issue #1158's *Fix* item 1 also calls the top-of-loop flush "a single self-healing checkpoint at
the loop's entry point [that] removes the need to get every call site right". The plan does **not**
deliver that property. `pending_log` flushes only what a call site explicitly assigned to it, so a
*future* non-terminal `write_round_log` added without `pending_log = …` would regress exactly as
`core.py:575` did: the obligation is narrowed from "pair every call site with a flush" to "assign
`pending_log` at every non-terminal call site", not removed. Deriving the path inside the loop from
`config.log_stem` + `run_number` would be call-site-independent, but it reconstructs a path
`write_round_log` already returns and makes the flush fire on rounds with nothing pending, each
warning: `stage_specific_files` returns `False` for a not-yet-created log file, and
`commit_staged_files` reports an unchanged staged path as `success: False`. The narrower obligation
is accepted instead, backed by item 2's tripwire, which names any write that does slip through.
The issue may want updating on this count too.

## Related (not blocking)

`mcp-workspace#295` — hardening `rebase_onto_branch` to log the specific dirty files at the
library layer. Log-message-only, no interface change; the two fixes are independent.

## Files created / modified

### Modified — source

| File | Change |
|------|--------|
| `src/mcp_coder/mcp_workspace_git.py` | Re-export `stage_specific_files` (one import line + `__all__`) (step 1) |
| `src/mcp_coder/workflows/review/handoff.py` | `_flush_round_log`: `only=` staged commit of that one path (`stage_specific_files` + `commit_staged_files`), `push=` flag, `commit_hash is None` push skip, docstring rewrite (step 1) |
| `src/mcp_coder/workflows/review/core.py` | `pending_log` local; scoped push-free flush at the top of the round loop, above `sha_before` (step 1) |
| `src/mcp_coder/workflow_steps/rebase.py` | `_attempt_rebase_and_push`: dirty-working-tree guard + `_has_uncommitted_tracked_changes` helper (step 2) |

### Modified — tests

| File | Change |
|------|--------|
| `tests/workflows/review/conftest.py` | `env` fixture: add `handoff.stage_specific_files` + `handoff.commit_staged_files` mocks (step 1) |
| `tests/workflows/review/test_handoff.py` | Two tests: `commit_hash is None` skips the push; `only=` stages and commits just that path, and a failed staging commits nothing (parametrised) (step 1) |
| `tests/workflows/review/test_core_after_steps.py` | One test: round 1 `tasks` flushes before round 2's rebase, staging only the round-log path (step 1) |
| `tests/workflow_steps/test_rebase.py` | Four tests: dirty tree skips the rebase; a modified `uv.lock` alone also skips; untracked-only still rebases; clean tree rebases (step 2) |

### Not modified

- No new modules, packages or `__init__.py` files.
- No documentation changes (see *Decided against*).
- No existing test is edited. In `tests/workflow_steps/test_rebase.py` all **8** existing tests
  pass untouched — the 5 in `TestRebaseIntegration` run against `Path("/test")`, where the
  unpatched `get_full_status` reports a non-repo with nothing pending, and the 3 in
  `TestGetRebaseTargetBranch` never reach the guard.
- `tests/workflows/review/test_core.py`, which defines its own duplicate `env` fixture and
  `_run` (plan lane), needs no change: with `stage_specific_files` unpatched there it returns
  `False` on the non-repo `tmp_path`, so the scoped flush warns and commits nothing, and every
  flush assertion in that file is `assert_called()` on `commit_all_changes`, satisfied by its
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
