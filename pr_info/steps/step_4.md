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
tests/icoder/ui/test_app.py                          (modify — add new tests)
```

## WHAT

```python
# additions in ICoderApp
def __init__(self, app_core, *, format_tools=True, **kwargs):
    ...
    project_dir = Path(app_core.runtime_info.project_dir) if app_core.runtime_info else Path.cwd()
    self._branch_service = BranchInfoService(project_dir)
    self._branch_failed: set[str] = set()
    self._branch_loading: set[str] = set()
    self._last_pr_number: int | None = None

def compose(self) -> ComposeResult:
    ...
    yield BranchInfoBar(project_dir)   # AFTER status-bar Horizontal

def on_mount(self) -> None:
    ...                                # existing logic
    self.query_one(BranchInfoBar).update_state(None, None, False, set(), set())
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
- **Drop-on-toggle-off**: in PR worker thread, after `fetch_pr` returns,
  before applying via `call_from_thread`, check
  `if not self._branch_service.pr_enabled: return`. Result silently dropped.
- **Worker pattern**: use `self.run_worker(callable, thread=True)`. Inside
  the callable, do I/O on the worker thread, then
  `self.call_from_thread(self._apply_branch_state, ...)` to update widget.
- Helper `_apply_branch_state(info, pr_number=...)`: stores `info` on `self`,
  recomputes `loading`/`failed` sets based on call site, calls
  `widget.update_state(info, self._last_pr_number, service.pr_enabled,
  loading, failed)`.

## ALGORITHM

```
_tick_branch_quick():
    def work():
        try: info = service.fetch_info()
        except Exception: failed.add("issue"); info = None
        else: failed.discard("issue")
        call_from_thread(apply, info)
        if info and service.branch_changed(info.branch_name) and service.pr_enabled:
            run_pr_fetch(info.issue_number)
    run_worker(work, thread=True)

_on_refresh_pr():
    if not service.begin_pr_fetch(): return
    loading.add("pr"); render()
    def work():
        try: pr = service.fetch_pr(info.issue_number)
        except Exception: failed.add("pr"); pr = None
        finally: service.end_pr_fetch()
        if not service.pr_enabled: return       # drop silently
        loading.discard("pr"); call_from_thread(apply_pr, pr)
    run_worker(work, thread=True)
```

## DATA

- New app instance state:
  `_branch_service: BranchInfoService`,
  `_branch_loading: set[str]`,
  `_branch_failed: set[str]`,
  `_last_branch_info: BranchInfo | None`,
  `_last_pr_number: int | None`.

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
6. `test_pr_result_dropped_when_toggle_flipped_off_during_fetch` — patch
   `fetch_pr` to set toggle off mid-call; assert widget zone stays `"—"`.
7. `test_branch_change_kicks_pr_fetch` — patch service so first `fetch_info`
   returns branch `"main"`, second returns `"123-foo"`; toggle on; advance
   timer; assert `fetch_pr` invoked once with `123`.
8. `test_failed_fetch_shows_question_mark` — patch `fetch_info` to raise;
   trigger refresh; assert widget renders `"?"`.

Use Textual's `app.run_test()` pattern (existing tests in this file are a
template). For timer tests, call `_tick_branch_quick` directly rather than
waiting 2 seconds.

Run textual_integration marker tests + unit tests + pylint + mypy. One commit.
