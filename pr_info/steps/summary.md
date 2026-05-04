# Issue #950 — Tone down branch-info polling, prefix version label

## Goal

Two coordinated fixes for iCoder following PR #940:

1. **Responsiveness** — the 2 s `BranchInfoBar` poll runs the full data-layer
   fetch (multiple git subprocess calls + cache reads) every tick. Move the
   expensive work to the existing 30 s tick, slow the cheap tick to 10 s, and
   add in-flight guards plus a render-diff guard so identical state stops
   triggering re-renders.
2. **Version label** — `v0.1.2` → `mcp-coder v0.1.2`.

## Architectural / Design Changes

- **Two-tier data fetch.** The data layer (`mcp_coder.services.branch_info`)
  gets a second entry point, `get_branch_only`, that returns a `BranchInfo`
  populated only with the cheap fields: `is_git_repo`, `branch_name`,
  `is_dirty`, `issue_number` (regex on the branch name). Issue/label/cache-age
  fields stay `None`. The heavy `get_branch_info` is unchanged.
- **Adapter additions, no class redesign.** `BranchInfoService` gains one new
  fetch method (`fetch_branch_only`) and **two new pairwise-independent guard
  flag pairs** — `begin_quick_tick`/`end_quick_tick` and
  `begin_full_tick`/`end_full_tick`. These are deliberately distinct from the
  existing `begin_issue_fetch` / `begin_pr_fetch` so periodic ticks and manual
  buttons never block each other, and a slow full tick never starves a quick
  tick.
- **Quick-tick merge semantics.** `BranchInfo` is a 7-field frozen dataclass;
  the quick path knows only 4 of them. `_apply_branch_state` gains a
  `merge_with_prior: bool` keyword that, when `True`, uses
  `dataclasses.replace` to copy `issue_title` / `issue_status_label` /
  `cache_last_checked` from the prior `_last_branch_info`. Without this the
  bar would lose the title/label/age stamp every 10 s.
- **Render-diff guard.** `ICoderApp` gains a `_last_view: Optional[BranchInfoView]`
  attribute. `_render_branch_state` builds the new view, compares it to the
  previous one (free `__eq__` from the frozen dataclass), and short-circuits
  `bar.update_state(...)` when nothing has changed. The tracker accepts
  `None` for the initial state and the no-git-repo case.
- **Instrumentation.** A small `_timed_fetch(label, fn)` helper wraps the
  data-layer call with `time.perf_counter()` and emits a debug-level
  `branch_quick: Nms` / `branch_full: Nms` line. Scoped around the fetch
  only — not the `call_from_thread` plumbing — so the number reflects the
  actual cost.
- **Version label.** Single-character compose change from `f"v{version}"` to
  `f"mcp-coder v{version}"`. `#status-version` is `width: auto` so the layout
  is unaffected.

What is NOT changing: the data-layer signature of `get_branch_info`, the
`BranchInfo` shape, the `BranchInfoBar` widget, the existing manual-refresh
button handlers, the PR-fetch generation token, or any of the existing
guard methods.

## Files Created or Modified

### Created (planning only)

- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md` … `pr_info/steps/step_5.md`

### Modified by implementation

| File | Steps | Reason |
|------|-------|--------|
| `src/mcp_coder/services/branch_info.py` | 1 | Add `get_branch_only` |
| `tests/services/test_branch_info.py` | 1 | Cover `get_branch_only` |
| `src/mcp_coder/icoder/services/branch_info_service.py` | 2 | Add `fetch_branch_only` and two tick-guard flag pairs |
| `tests/icoder/test_branch_info_service.py` | 2 | Cover delegation + guard independence |
| `src/mcp_coder/icoder/ui/app.py` | 3, 4, 5 | Tick split + merge + timing (3); render-diff guard (4); version label (5) |
| `tests/icoder/ui/test_app.py` | 3, 4, 5 | Tick guard / merge / render-diff / label coverage |
| `docs/icoder/icoder.md` | 3, 5 | Reflect 10 s cadence (3) and `mcp-coder v…` label (5) |

## Steps

1. **Step 1** — Data-layer `get_branch_only` (cheap branch-only snapshot).
2. **Step 2** — `BranchInfoService.fetch_branch_only` + tick-busy guard pairs.
3. **Step 3** — App tick split: 10 s quick tick → `fetch_branch_only` with
   merge, full tick guarded, `_timed_fetch` helper, doc cadence update.
4. **Step 4** — Render-diff guard in `_render_branch_state`.
5. **Step 5** — Version label `mcp-coder v…` + matching doc string.

Each step is one commit: tests + implementation + all three checks (pylint,
pytest, mypy) green before moving on.

## Constraints

- KISS: do not generalize the guard pairs into a `dict[str, bool]` — the
  issue spec explicitly mandates two named flags. Type safety + spec
  compliance over mild deduplication.
- KISS: do not introduce a context-manager guard helper, a separate
  `_apply_branch_state_quick` method, or a timing decorator. A keyword arg
  + `dataclasses.replace` + a 4-line helper covers it.
- TDD: every step writes its tests first (or alongside) and lands red→green
  in the same commit.
