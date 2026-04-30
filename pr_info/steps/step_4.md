# Step 4 — App integration: timers, workers, button handlers

## LLM Prompt

> Implement Step 4 of issue #844. Read `pr_info/steps/summary.md` and Steps
> 1–3 (already merged). This step wires the widget into `ICoderApp`: composes
> it below the status bar, runs tiered timers, dispatches button-press
> messages to worker threads, and bridges results back via `call_from_thread`.
> **TDD**: write the integration tests first. End with one commit; all
> checks green.

## WHERE

```
src/mcp_coder/icoder/ui/app.py                       (modify)
src/mcp_coder/icoder/services/branch_info_service.py (modify — add pr-fetch generation token)
tests/icoder/ui/test_app.py                          (modify — add new tests)
tests/icoder/test_branch_info_service.py             (modify — add race-token test)
docs/icoder/icoder.md                                (modify — Branch Info section)
```

> Note: Step 5 (docs-only) was folded into this step per
> `planning_principles.md` ("merge tiny or intertwined steps"). The doc
> update ships in the same commit as the app integration. See the
> "Documentation" sub-section at the end.

## WHAT

```python
# additions in ICoderApp
def __init__(self, app_core, *, format_tools=True, **kwargs):
    ...
    self._project_dir: Path = (
        Path(app_core.runtime_info.project_dir)
        if app_core.runtime_info
        else Path.cwd()
    )
    self._branch_service = BranchInfoService(self._project_dir)
    self._branch_failed: set[str] = set()
    self._branch_loading: set[str] = set()
    self._last_branch_info: BranchInfo | None = None
    self._last_pr_number: int | None = None

def compose(self) -> ComposeResult:
    ...
    # The new BranchInfoBar is yielded as a SIBLING of (NOT inside) the
    # existing `with Horizontal(id="status-bar")` block — i.e. it is the
    # next yield after that with-block closes. Concretely, replace the
    # tail of compose() with:
    yield OutputLog()
    yield Static(id="streaming-tail")
    yield CommandAutocomplete()
    yield BusyIndicator()
    yield InputArea(
        command_history=self._core.command_history,
        registry=self._core.registry,
        event_log=self._core.event_log,
    )
    version = self._get_version()
    with Horizontal(id="status-bar"):
        yield Static("↓0 ↑0 | total: ↓0 ↑0", id="status-tokens")
        yield Static(f"v{version}", id="status-version")
        yield Static(r"\ + Enter = newline", id="status-hint")
    # ↓ NEW: yielded AFTER the status-bar with-block closes.
    # Uses `self._project_dir` set in __init__ — there is no local
    # `project_dir` in compose() scope.
    yield BranchInfoBar(self._project_dir)

def on_mount(self) -> None:
    ...                                # existing logic
    self.query_one(BranchInfoBar).update_state(None)
    self.run_worker(self._tick_branch_full, thread=True)   # async first populate
    self.set_interval(2.0, self._tick_branch_quick)
    self.set_interval(30.0, self._tick_branch_full)

def _tick_branch_quick(self) -> None: ...
def _tick_branch_full(self) -> None: ...
def on_branch_info_bar_refresh_issue(self, _: BranchInfoBar.RefreshIssue) -> None: ...
def on_branch_info_bar_refresh_pr(self, _: BranchInfoBar.RefreshPR) -> None: ...
def on_branch_info_bar_toggle_pr(self, _: BranchInfoBar.TogglePR) -> None: ...
```

## HOW

- **2s tick (`_tick_branch_quick`)**: spawn worker that calls
  `service.fetch_info()`. On result, if `service.branch_changed(...)` and
  `service.pr_enabled`, kick a PR fetch worker. Update widget via
  `call_from_thread`.
- **30s tick (`_tick_branch_full`)**: same as quick but also marks
  `loading.add("issue")` before kickoff and removes it after; clears/sets
  `failed`. (Cache call in `get_all_cached_issues` will re-hit the API past
  its 50s window — issue requirement.)
- **Refresh-issue button handler**: if `service.begin_issue_fetch()` is False,
  ignore. Else: add `"issue"` to `loading`, render, spawn worker calling
  `service.fetch_info()`, in `finally` call `service.end_issue_fetch()`,
  remove `"issue"` from loading, on exception add to `failed` (drop from
  failed on success).
- **Refresh-PR button handler**: same pattern, but **independent of
  `pr_enabled`** (issue: "Refresh-PR fires regardless of the toggle state").
  Needs `issue_number` from last `BranchInfo`; if None, no-op.
- **Toggle-PR handler**: flip `service.set_pr_enabled(not service.pr_enabled)`,
  re-render. If now enabled and we have an issue number, kick a PR fetch.
- **PR-fetch race protection (generation token)**: a fast
  toggle-off / refresh-PR sequence could otherwise spawn two concurrent PR
  workers and the wrong one might win. **Decision: monotonic
  `pr_fetch_generation: int` on `BranchInfoService`**. Mechanism:
  - `BranchInfoService` gains `self._pr_fetch_generation: int = 0` and a
    method `start_pr_fetch() -> int` that increments and returns the new
    generation. `current_pr_fetch_generation` is exposed as a read-only
    property.
  - When the app starts a PR worker, it calls
    `gen = service.start_pr_fetch()` and the worker captures `gen` locally.
  - Before applying the result via `call_from_thread`, the worker checks
    `if gen != service.current_pr_fetch_generation: return` — silently
    discards stale results.
  - Toggling PR off **also** increments the generation
    (`service.set_pr_enabled(False)` calls `_pr_fetch_generation += 1`
    internally, invalidating any in-flight worker). This subsumes the old
    "drop-on-toggle-off" check.
  - This replaces the `pr_in_flight` boolean's role for race-protection;
    the boolean (and `begin_pr_fetch`/`end_pr_fetch` from Step 3) can stay
    for duplicate-click suppression but is no longer the race gate.
  - **Why generation token over the early-cancel sentinel `current_pr_token:
    object | None`**: an `int` is trivial to read, log, and assert in
    tests; an opaque object identity has no equivalent advantage here. The
    generation also gives a natural "how many PR fetches have started" metric
    for future debugging.
- **Worker pattern**: use `self.run_worker(callable, thread=True)`. Inside
  the callable, do I/O on the worker thread, then
  `self.call_from_thread(self._apply_branch_state, ...)` to update widget.
- Helper `_apply_branch_state(info, pr_number=...)`: stores `info` on `self`,
  recomputes `loading`/`failed` sets based on call site, builds a
  `BranchInfoView(info=info, pr_number=self._last_pr_number,
  pr_enabled=service.pr_enabled, loading=frozenset(self._branch_loading),
  failed=frozenset(self._branch_failed))`, calls
  `widget.update_state(view)`.

## ALGORITHM

```
_tick_branch_quick():
    def work():
        try: info = service.fetch_info()
        except Exception: failed.add("issue"); info = None
        else: failed.discard("issue")
        call_from_thread(_apply_branch_state, info)
        if info and service.branch_changed(info.branch_name) and service.pr_enabled:
            run_pr_fetch(info.issue_number)
    run_worker(work, thread=True)

_on_refresh_pr():
    if not service.begin_pr_fetch(): return
    loading.add("pr"); render()
    gen = service.start_pr_fetch()              # capture generation
    def work():
        try: pr = service.fetch_pr(info.issue_number)
        except Exception: failed.add("pr"); pr = None
        finally: service.end_pr_fetch()
        if gen != service.current_pr_fetch_generation: return   # stale → drop
        loading.discard("pr")
        call_from_thread(_apply_branch_state, info, pr_number=pr)
    run_worker(work, thread=True)
```

## DATA

- New app instance state:
  `_branch_service: BranchInfoService`,
  `_branch_loading: set[str]`,
  `_branch_failed: set[str]`,
  `_last_branch_info: BranchInfo | None`,
  `_last_pr_number: int | None`.
- New service state (added in this step on top of Step 3):
  `_pr_fetch_generation: int` (incremented by `start_pr_fetch()` and by
  `set_pr_enabled(False)`). Public read-only property
  `current_pr_fetch_generation`.

## Tests (TDD — write first)

Add to `tests/icoder/ui/test_app.py` (already
`pytestmark = pytest.mark.textual_integration`):

1. `test_branch_info_bar_present_in_compose` — pilot, query
   `BranchInfoBar`; assert exists, no error.
2. `test_initial_state_renders_loading_placeholder` — pilot, immediately
   after mount; assert widget renders `…` (workers haven't completed).
3. `test_refresh_issue_button_triggers_loading_then_state` — pilot, monkey-patch
   `BranchInfoService.fetch_info` to return a fixed `BranchInfo`; click the
   refresh-issue button by ID; pause; assert widget shows the new branch.
4. `test_pr_button_disabled_off_dashes_pr_zone` — assert default state shows
   PR zone as `"—"`.
5. `test_toggle_pr_enables_lookup` — click toggle button; assert
   `service.pr_enabled` flips to True; assert PR zone updates from `"—"` to
   `"…"` or value.
6. `test_pr_result_dropped_when_toggle_flipped_off_during_refresh_pr_button_fetch`
   — covers the **refresh-PR button** launch path specifically (test #10
   covers the same race via the 2s-tick path; both launch paths are
   worth keeping).
   - Pilot, toggle PR on, then click the **refresh-PR button** — this
     calls `service.start_pr_fetch()` and the worker captures
     `gen = service.current_pr_fetch_generation` (e.g. 1).
   - Patch `fetch_pr` so that mid-call (before returning) it invokes
     `service.set_pr_enabled(False)` — which increments the generation
     to 2 — and then returns PR #42.
   - Assert: at the moment the worker would have applied its result, the
     captured `gen` (1) **no longer equals**
     `service.pr_fetch_generation` (2), so `_apply_branch_state` is
     never called with `pr_number=42`. Concretely, assert the widget's
     PR zone stays `"—"` (never shows `"PR #42"`).
   - The drop happens via the generation-token check, not via
     `pr_enabled` directly. Complementary to test #10, which exercises
     the same guard but via `_tick_branch_quick`.
7. `test_branch_change_kicks_pr_fetch` — patch service so first `fetch_info`
   returns branch `"main"`, second returns `"123-foo"`; toggle on; advance
   timer; assert `fetch_pr` invoked once with `123`.
8. `test_failed_fetch_shows_question_mark` — patch `fetch_info` to raise;
   trigger refresh; assert widget renders `"?"`.
9. `test_pr_fetch_race_stale_result_dropped` — exercise the race scenario
   directly:
   - Pilot, toggle PR on, click refresh-PR (worker A starts, captures
     `gen=1`).
   - Block worker A inside `fetch_pr` via a `threading.Event`.
   - Toggle PR off (gen → 2), then toggle on (gen → 3), then click
     refresh-PR (worker B starts, captures `gen=3`, returns PR #99).
   - Unblock worker A — it returns PR #42, but `gen=1 !=
     current_pr_fetch_generation=3`, so its result is dropped.
   - Assert widget shows `PR #99` (worker B's result), never `PR #42`.
10. `test_pr_fetch_race_via_2s_tick_dropped_on_toggle_off` — analogous to
    #6/#9 but the PR worker is launched by the 2s branch tick rather than
    by the refresh-PR button:
    - Toggle PR on (gen → 1) and seed `last_branch=None` so the next
      `_tick_branch_quick` triggers the auto PR fetch.
    - Patch `fetch_info` to return a `BranchInfo` with branch
      `"123-foo"` (so `branch_changed` returns True and the auto PR
      fetch is kicked).
    - Block the PR worker inside `fetch_pr` via a `threading.Event`.
    - Toggle PR off — `set_pr_enabled(False)` increments the generation
      to 2.
    - Unblock the worker — it returns PR #42, but its captured
      `gen=1 != current_pr_fetch_generation=2`, so the result is dropped
      via the same generation check.
    - Assert widget's PR zone stays `"—"` (never shows `PR #42`),
      confirming the generation-token guard covers the 2s-tick code path
      as well as the button path.

In `tests/icoder/test_branch_info_service.py`, also add:

- `test_start_pr_fetch_increments_generation` — first call returns 1, second
  returns 2, etc.
- `test_set_pr_enabled_false_increments_generation` — toggling off bumps the
  generation (so any in-flight worker is invalidated).
- `test_set_pr_enabled_true_does_not_increment` — toggling on does NOT bump
  the generation (only the next `start_pr_fetch()` does).

Use Textual's `app.run_test()` pattern (existing tests in this file are a
template). For timer tests, call `_tick_branch_quick` directly rather than
waiting 2 seconds.

Run textual_integration marker tests + unit tests + pylint + mypy. One commit.

## Documentation

This step also includes the user-facing doc edits previously planned as
Step 5 (folded in per `planning_principles.md` — "merge tiny or intertwined
steps"). Edit `docs/icoder/icoder.md`:

- Add a new section titled **"Branch Info"** between "Status Line" and
  "Slash Commands". Mirror the existing markdown style (tables, short
  paragraphs).
- **Field table** — four rows (Branch · State, Issue, PR, Cache age) with
  example values and placeholder semantics (`…` loading, `?` failed, `—`
  not applicable, `(no git)`, `(no issue)`).
- **Button table** — three rows (Refresh issue, Refresh PR, PR toggle) with
  their action.
- **Update cadence** subsection listing `2s` (branch+dirty), `30s` (issue
  cache refresh), branch-change (auto PR fetch when toggle on), on-click
  (manual refresh).
- **Note** that PR lookup is **off by default**, **not persisted** between
  sessions, and **gated behind the toggle** for the auto/2s path — but the
  refresh-PR button **fires regardless** of the toggle state (issue
  requirement).
- No screenshots required. Cross-link from `docs/iCoder.md` only if the
  existing structure already cross-links other sections.

The doc edits ship in the same commit as the app integration (no separate
docs-only commit). After all code edits, re-run pytest/pylint/mypy to
confirm nothing regressed; the doc change itself is markdown-only and has
no test impact.
