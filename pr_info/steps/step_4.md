# Step 4 — Render-diff guard in `_render_branch_state`

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement `pr_info/steps/step_4.md`.
> This step adds a render-diff guard so identical consecutive
> `BranchInfoView` snapshots no longer trigger a `BranchInfoBar.update_state`
> call. It builds on Step 3's tick split but is fully independent — both
> tick paths (and all manual-refresh paths) flow through
> `_render_branch_state`, so the optimisation lands in one place.
>
> After the change, run all three quality checks (pylint, pytest, mypy)
> and confirm they pass before producing the single commit for this step.

## WHERE

| Path | Action |
|------|--------|
| `src/mcp_coder/icoder/ui/app.py` | Add `_last_view` attribute and short-circuit logic in `_render_branch_state` |
| `tests/icoder/ui/test_app.py` | Tests for unchanged-state skip and `None ↔ view` transitions |

## WHAT

A new instance attribute on `ICoderApp`, initialised in `__init__`:

```python
self._last_view: Optional[BranchInfoView] = None
```

`_render_branch_state` is restructured to compute the new view, compare,
and skip the `bar.update_state(...)` call when nothing has changed.

## HOW

- The previous-view tracker must accept both `None` (initial state, and
  whenever `_last_branch_info is None`) and `BranchInfoView` instances.
- `BranchInfoView` is `@dataclass(frozen=True)`, so `__eq__` is provided
  by the dataclass machinery — no custom equality needed.
- Build the new view exactly as today; the only structural change is the
  comparison + early-return before calling `update_state`.
- Update `self._last_view` only when emitting a real `update_state` call.
- The early-return on `NoMatches` (when `BranchInfoBar` is not yet
  mounted) stays untouched; do not cache `_last_view` in that path.
- Narrow the existing `except Exception` at `app.py:464` (current line;
  verify exact location) to `except NoMatches`. This is the deliberate
  narrowing — do not retain the broader catch.
- Add `from textual.css.query import NoMatches` to the existing imports
  in `app.py` (other modules in the codebase already import it from this
  path).

## ALGORITHM

```
try:
    bar = self.query_one(BranchInfoBar)
except NoMatches:
    return

if self._last_branch_info is None:
    new_view = None
else:
    new_view = BranchInfoView(
        info=self._last_branch_info,
        pr_number=self._last_pr_number,
        pr_enabled=self._branch_service.pr_enabled,
        loading=frozenset(self._branch_loading),
        failed=frozenset(self._branch_failed),
    )

if new_view == self._last_view:
    return
self._last_view = new_view
bar.update_state(new_view)
```

## DATA

- One new attribute: `_last_view: Optional[BranchInfoView]`.
- Comparison uses dataclass-generated `__eq__` over: `info` (also a
  frozen dataclass), `pr_number`, `pr_enabled`, `loading` (frozenset),
  `failed` (frozenset). All hashable and value-comparable.
- No change to the `BranchInfoView` shape or `BranchInfoBar.update_state`
  signature.

## Tests

In `tests/icoder/ui/test_app.py`, use `unittest.mock.patch.object` on
`BranchInfoBar.update_state` to count and inspect calls.

1. **Identical consecutive ticks → single `update_state`** —
   `test_render_diff_skips_unchanged_view`:
   - patch `fetch_info` to return the same `BranchInfo` twice;
   - drive `_tick_branch_full()` twice (or `_render_branch_state()`
     directly twice with the same `_last_branch_info`);
   - assert `update_state` called exactly **once** in total (initial
     mount may add one prior `None` call — assert the second tick does
     not add another call).
2. **`None → view` transition emits an update** —
   `test_render_diff_emits_first_real_view`:
   `_last_branch_info` starts `None`, then is set to a real
   `BranchInfo`; `_render_branch_state()` is called and `update_state`
   is invoked with the new `BranchInfoView`.
3. **`view → None` transition emits an update** —
   `test_render_diff_emits_when_returning_to_none`:
   prime `_last_view` with a real view, set `_last_branch_info = None`,
   call `_render_branch_state`; assert `update_state(None)` is called.
4. **Differing view triggers update** —
   `test_render_diff_emits_when_field_changes`:
   prime with one view (e.g. `pr_number=None`), then set
   `_last_pr_number = 99` and re-render; assert a fresh `update_state`
   call with the new `pr_number=99`.

Behavioural anchors: existing tests like
`test_refresh_issue_button_triggers_state_update` and
`test_toggle_pr_enables_lookup` must still pass — they assert *rendered
output*, not call counts, so the diff guard does not regress them.

## Acceptance

- All three quality checks green.
- No change to any existing call-site signature.
- Single commit, e.g.
  `perf(icoder): skip BranchInfoBar.update_state when view is unchanged`.
