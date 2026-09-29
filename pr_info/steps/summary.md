# Summary — #1147: progress-based task completion

## Problem

The implement workflow scores a round as successful when *any* file changed. A genuinely
blocked task therefore loops forever: the agent appends a "still blocked" paragraph, the
gate sees a file change, the round is scored as success, and `get_next_task` hands back the
same task next round. Observed on #1146: 45 rounds, 45 commits, 1h31m, zero progress.

Two secondary holes made it worse: the `while True:` loop in `core.py` has no round cap,
and `get_next_task` swallows every exception — a missing tracker reads as "no tasks",
which the loop treats as clean completion and exits 0 with the work unfinished.

## Design change

**The success predicate becomes a quantity that must decrease.** A round counts as progress
only if the number of incomplete non-meta tasks went down:

```
before = len(get_incomplete_tasks(pr_info, exclude_meta_tasks=True))   # before the LLM call
after  = same read, after the LLM call
progress  <=>  after < before
```

Counting, not name matching: `is_task_done()` returns on the first normalized name match, and
the tracker prompt prescribes the *same three sub-task names for every step*, so a name-based
check would return True for every later step once Step 1's names are ticked — degenerating
back to "any file change = success".

The happy path is safe by construction: ticking a checkbox both lowers the count and is a file
change, so the new gate can only reject rounds the old one wrongly accepted. This is strictly
a tightening.

**A no-progress round is still committed and pushed**, exactly as today, and only then returns
a failure reason. Leaving the tree dirty would make the next run fail its own `check_git_clean`
prerequisite, blocking its own retry. The reason feeds the existing 3-strike retry budget, so
the cost ceiling is 3 noise commits instead of 45.

**Two backstops behind the predicate.** The count is agent-written — deleting task lines also
lowers it — so a round cap of `max(progress.total + 10, 20)` bounds the loop regardless, and a
tracker that cannot be read now fails loudly instead of reading as completion.

**The prompt gets the same fix at the source.** The blocked channel (`pr_info/.blocked.txt`)
already exists and works; it lost to a generated step instruction saying "stop and report",
which the agent satisfied by writing prose into the step file. Both the implementation prompt
and the plan-creation prompt are reworded so that prose is never a report.

## Failure taxonomy

| Reason | Where | Label |
|--------|-------|-------|
| `no_progress` | per-attempt, internal to `process_task_with_retry` | — (never reaches `core.py`) |
| `no_progress_after_retries` | retry budget exhausted, at least one attempt changed files | existing `no_changes_after_retries` |
| `no_changes_after_retries` | every attempt produced zero changes | unchanged |
| `error` | tracker unreadable for any reason — detail names `pr_info/TASK_TRACKER.md` | existing `implementing_failed` |
| `general` | round cap tripped | existing `implementing_failed` |

`no_progress_after_retries` is the only new reason string, and it reuses an existing label: the
operator action is identical either way (`set-status status-05:plan-ready`), so a new
`status-06f-*` label would cost `labels.json`, `define_labels.py`, the docs table and the
workflow matrix for no operational gain. The distinction between "the LLM did nothing" and
"the LLM did plenty and moved nothing" lives in the failure comment.

## Files

### Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/task_processing.py` | `_count_incomplete_tasks`, progress gate, tracker errors surfaced, `previous_reason` + two reminder variants, terminal-reason selection |
| `src/mcp_coder/workflows/implement/failure_reporting.py` | two dict entries for `no_progress_after_retries` |
| `src/mcp_coder/workflows/implement/core.py` | route the new reason, plumb `outcome.detail` through the `error` branch, round cap on the Step 4 loop |
| `src/mcp_coder/prompts/prompts.md` | reword the blocked rule; add precondition wording to Implementation Plan Creation |
| `tests/workflows/implement/test_task_processing.py` | autouse progress fixture; rewrite the two tests asserting a swallowed tracker error |
| `tests/workflows/implement/test_core_failure_routing.py` | routing for the new reason, the round cap and the tracker detail |
| `tests/workflows/implement/test_failure_reporting.py` | new label/display mapping |

### Created

| File | Purpose |
|------|---------|
| `tests/workflows/implement/test_task_progress_gate.py` | the retry-loop reason selection (Step 3) and the progress gate (Step 4) |

### Not touched

`labels.json`, `define_labels.py`, the label docs and the workflow matrix — no new label.
`finalisation.py`, `task_tracker_prep.py` and the post-loop mypy block sit after the loop and
are reached only on the `no_tasks` break, which this change does not alter.

## Test-cost note

~24 tests in `test_task_processing.py` call `process_single_task` with only `get_next_task`
patched. Every one of them now hits the new tracker read. A single function-scoped autouse
fixture patching `_count_incomplete_tasks` with `side_effect=itertools.count(5, -1)` — a
strictly decreasing sequence, so any number of reads in any order reads as progress — keeps
all of them meaning exactly what they mean today, with no per-test edit.

## Accepted risks

- **The count is agent-written.** Deleting task lines or regenerating the tracker lowers it and
  reads as progress. Nothing compares the two trackers structurally. The round cap is the bound
  that no tracker edit can evade.
- **False negative: tasks added while completing one.** If the agent appends sub-tasks in the
  same round it ticks others, the count can stay flat and real work scores a strike. It partly
  self-heals — the work is committed, and the next attempt re-selects the now-first incomplete
  task — but three such rounds fail the run.
- **Meta-task filter mismatch, out of scope.** `_get_incomplete_tasks` excludes
  `prepare git commit message` and `all … tasks completed`, but the prompt prescribes
  "Commit message prepared", which matches none of them. That sub-task counts as a normal task
  in the snapshot. Not fixed here.
- **`Progress: X/Y` in the failure comment already mixes units** (`completed` counts rounds,
  `total` counts sub-tasks). The new comment shows the same pre-existing skew.

## Steps

1. **Round cap** — bound the `while True:` loop in `core.py` Step 4.
2. **Failure surface** — new reason in the two dicts, routed in `core.py`, tracker detail plumbed.
3. **Retry loop** — retry on `no_progress`, pick the terminal reason, second reminder variant.
4. **Progress gate** — `_count_incomplete_tasks`, before/after snapshot, `no_progress` reason,
   tracker errors surfaced as `error`.
5. **Prompt wording** — one reword, one addition in `prompts.md`.

**The order is the safety property, not a preference.** `core.py`'s failure chain has no `else`:
an unrouted reason falls through to `progress.completed += 1` and the loop goes round again — so
every consumer lands before the thing that produces what it consumes. The cap lands first, before
any new reason exists, as the backstop for the one risk the predicate cannot cover. Then the route
(2), then the retry loop that keeps `no_progress` off `core.py` entirely (3), and only then the
gate that emits it (4).

Sequencing: no other step depends on Step 4. Step 3 keys off the `"no_progress"` *string* and needs no
emitter — exactly as Step 2 routes a reason nothing emits yet — and both are testable by
constructing outcomes directly. Landing the consumer and its route before the emitter closes the
window in which a no-progress round would reach `core.py` unrouted, increment
`progress.completed` and loop on until the full round cap was burned. Step 2 needs only Step 1's
backstop; Step 3 needs Step 2; Step 4 needs Steps 2 and 3. Step 5 is independent of all of them.
Each step produces one commit.
