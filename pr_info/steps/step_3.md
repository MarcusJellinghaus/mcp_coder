# Step 3 — App tick split: 10 s quick tick, merge semantics, timing helper

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement `pr_info/steps/step_3.md`.
> This step rewires the periodic ticks in `ICoderApp` to use the building
> blocks added in Steps 1 and 2: the cheap quick fetch, the two new tick
> guards, and a small timing helper. It also adds the merge semantics on
> quick-tick application so issue/label/cache-age fields are not lost
> between full ticks.
>
> Do **not** add the render-diff guard yet — that is Step 4. Do **not**
> change the version label — that is Step 5.
>
> After the change, run all three quality checks (pylint, pytest, mypy)
> and confirm they pass before producing the single commit for this step.

## WHERE

| Path | Action |
|------|--------|
| `src/mcp_coder/icoder/ui/app.py` | Tick interval, quick/full worker bodies, `_apply_branch_state` merge, `_timed_fetch` helper |
| `tests/icoder/ui/test_app.py` | Tick-guard / merge / timing coverage |
| `docs/icoder/icoder.md` | Update the cadence row from `2s` to `10s` |

## WHAT

Modified or added members of `ICoderApp`:

```python
def _timed_fetch(self, label: str, fn: Callable[[], BranchInfo]) -> BranchInfo: ...

def _branch_quick_work(self) -> None: ...           # rewritten
def _branch_full_work(self) -> None: ...            # rewritten
def _apply_branch_state(
    self,
    info: Optional[BranchInfo],
    *,
    merge_with_prior: bool = False,                 # NEW kw-only flag
) -> None: ...
```

In `on_mount`, change the existing line:

```python
self.set_interval(2.0, self._tick_branch_quick)   # before
self.set_interval(10.0, self._tick_branch_quick)  # after
```

Imports added at the top of `app.py`: `time` and
`from dataclasses import replace`. `Callable` already imported via the
existing `typing` block (or add it if absent).

## HOW

- `_apply_branch_state` is the single sink for branch state on the UI
  thread. The merge happens here; do not move it into the worker.
- The merge uses `dataclasses.replace` to copy three fields from the
  prior `_last_branch_info`: `issue_title`, `issue_status_label`,
  `cache_last_checked`. All other fields come from the fresh quick-tick
  `info`.
- Both worker bodies use `_timed_fetch` to wrap the data-layer call only
  — not the `call_from_thread` dispatch.
- Quick worker calls `fetch_branch_only`; full worker still calls
  `fetch_info` (which delegates to `get_branch_info`).
- Each worker bails out early if its `begin_*_tick()` returns `False`;
  the matching `end_*_tick()` runs in the `finally` block of the
  surrounding `try`.
- The full worker continues to set/clear `_branch_loading.add("issue")` /
  `_branch_failed` exactly as today. The quick worker does **not**
  manipulate `_branch_loading` (the spinner is a full-tick concern).
- Doc: in `docs/icoder/icoder.md`, change the `2s` cell in the cadence
  table to `10s`, and align the surrounding sentence ("2-second ticks"
  if present in the line about the quick tick).
- The startup invocation in `on_mount` continues to call
  `self.run_worker(self._branch_full_work, thread=True)` directly —
  unchanged from current code. The `begin_full_tick()` guard inside
  `_branch_full_work` ensures a racing periodic tick is dropped harmlessly.
- `_timed_fetch` is implemented as a method on `ICoderApp` (not a free
  function) for cohesion with the workers that call it.

## ALGORITHM

`_timed_fetch`:

```
start = time.perf_counter()
try:
    return fn()
finally:
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.debug("%s: %dms", label, elapsed_ms)
```

`_branch_quick_work`:

```
if not self._branch_service.begin_quick_tick(): return
info: Optional[BranchInfo] = None
try:
    info = self._timed_fetch("branch_quick",
                             self._branch_service.fetch_branch_only)
    self._branch_failed.discard("issue")
except Exception as exc:
    logger.debug("branch_quick fetch failed: %s", exc)
    self._branch_failed.add("issue")
finally:
    self._branch_service.end_quick_tick()
self.call_from_thread(self._apply_branch_state, info, merge_with_prior=True)
```

`_branch_full_work`:

```
if not self._branch_service.begin_full_tick(): return
self._branch_loading.add("issue")
self.call_from_thread(self._render_branch_state)
info: Optional[BranchInfo] = None
try:
    info = self._timed_fetch("branch_full", self._branch_service.fetch_info)
    self._branch_failed.discard("issue")
except Exception as exc:
    logger.debug("branch_full fetch failed: %s", exc)
    self._branch_failed.add("issue")
finally:
    self._branch_loading.discard("issue")
    self._branch_service.end_full_tick()
self.call_from_thread(self._apply_branch_state, info)
```

`_apply_branch_state` — merge prepended, rest unchanged:

```
if (info is not None and merge_with_prior
        and self._last_branch_info is not None):
    info = replace(info,
        issue_title=self._last_branch_info.issue_title,
        issue_status_label=self._last_branch_info.issue_status_label,
        cache_last_checked=self._last_branch_info.cache_last_checked,
    )
# … existing body unchanged …
```

## DATA

- `_apply_branch_state` accepts a new keyword `merge_with_prior: bool`.
  Default `False` preserves all existing call-site behaviour
  (`_refresh_issue_work`, `_branch_full_work`, `_apply_pr_result` indirectly).
- `_timed_fetch` returns whatever `fn()` returns; for our two call
  sites that is a `BranchInfo`.
- No new instance attributes in this step.

## Tests

In `tests/icoder/ui/test_app.py`:

1. **Quick-tick merge preserves prior fields** —
   `test_quick_tick_merges_into_prior_branch_info`:
   - prime `app._last_branch_info` with a full `BranchInfo` (issue_title="T",
     status_label="status-04:plan-review", cache_last_checked=now);
   - patch `BranchInfoService.fetch_branch_only` to return a quick
     `BranchInfo` with `issue_title=None`, `status_label=None`,
     `cache_last_checked=None`;
   - drive `_tick_branch_quick()`; await pilot;
   - assert `app._last_branch_info.issue_title == "T"`,
     `app._last_branch_info.issue_status_label == "status-04:plan-review"`,
     `app._last_branch_info.cache_last_checked` is preserved.
2. **Quick-tick guard skips overlapping work** —
   `test_quick_tick_skipped_while_busy`:
   force `_quick_tick_busy = True` on the service, drive
   `_tick_branch_quick()`, assert `fetch_branch_only` was not called.
3. **Full-tick guard skips overlapping work** — symmetric.
4. **Quick and full ticks do not block each other** —
   `test_quick_and_full_ticks_run_in_parallel`:
   set `_quick_tick_busy = True`, drive `_tick_branch_full()`, assert
   the full worker still ran (`fetch_info` called).

The doc-update assertion is not unit-tested; it is a textual change in
the markdown file.

## Acceptance

- pylint, pytest (with `-n auto` + standard exclusions), mypy all green.
- Existing `BranchInfoBar` integration tests in `test_app.py` still pass.
- Regression anchor: existing test `test_branch_change_kicks_pr_fetch`
  continues to pass — no behavioural change to the branch-change → PR-fetch
  path.
- Single commit, e.g.
  `refactor(icoder): split branch-info ticks into quick (10s) and full (30s)`.
