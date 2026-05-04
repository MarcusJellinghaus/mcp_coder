# Step 2 — `BranchInfoService.fetch_branch_only` + tick-busy guard pairs

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement `pr_info/steps/step_2.md`.
> This step adds adapter-level methods that the App will use in Step 3.
> The new methods are independently testable and must not change any
> existing method's behaviour or signature.
>
> After the change, run all three quality checks (pylint, pytest, mypy)
> and confirm they pass before producing the single commit for this step.

## WHERE

| Path | Action |
|------|--------|
| `src/mcp_coder/icoder/services/branch_info_service.py` | Add `fetch_branch_only`, two private bool flags, four guard methods |
| `tests/icoder/test_branch_info_service.py` | Add tests for delegation + guard semantics + 4-way independence |

- Boy Scout: while in `branch_info_service.py`, update the module docstring's
  stale `"2-second ticks"` phrase to align with the new 10s/30s cadence
  introduced in Step 3 — simplest fix is to drop the specific number
  (e.g. `"between periodic ticks"`).

## WHAT

```python
def fetch_branch_only(self) -> BranchInfo: ...

def begin_quick_tick(self) -> bool: ...
def end_quick_tick(self) -> None: ...

def begin_full_tick(self) -> bool: ...
def end_full_tick(self) -> None: ...
```

Two new instance attributes, both initialised to `False` in `__init__`:

- `self._quick_tick_busy: bool`
- `self._full_tick_busy: bool`

## HOW

- Import `get_branch_only` alongside the existing `get_branch_info` and
  `get_pr_for_issue` imports at the top of `branch_info_service.py`.
- `fetch_branch_only` is a one-liner: `return get_branch_only(self._project_dir)`.
- Each `begin_*` follows the existing `begin_issue_fetch` / `begin_pr_fetch`
  pattern: return `False` if already busy, otherwise set the flag and
  return `True`.
- Each `end_*` simply clears the corresponding flag.
- Do **not** modify the existing `begin_issue_fetch`, `end_issue_fetch`,
  `begin_pr_fetch`, `end_pr_fetch`, `set_pr_enabled`, `start_pr_fetch`, or
  `branch_changed` methods.

## ALGORITHM

```
def begin_quick_tick(self) -> bool:
    if self._quick_tick_busy:
        return False
    self._quick_tick_busy = True
    return True

def end_quick_tick(self) -> None:
    self._quick_tick_busy = False
```

Identical pattern for `begin_full_tick` / `end_full_tick`.

## DATA

- `fetch_branch_only` returns `BranchInfo` (existing frozen dataclass).
- Each guard method returns `bool` (begin) or `None` (end).
- No data structure changes; only two new bool fields on the service.

## Tests

In `tests/icoder/test_branch_info_service.py`, mirror the existing test
style (`patch(f"{ADAPTER_MODULE}.get_branch_info", …)`).

1. **Delegation** — `test_fetch_branch_only_delegates_to_data_layer`:
   patch `get_branch_only` under the adapter module, call
   `service.fetch_branch_only()`, assert the patch was called once with
   `PROJECT_DIR` and the return value flows through.
2. **Quick guard** — `test_begin_quick_tick_returns_false_when_in_flight`:
   first call `True`, second call `False`; after `end_quick_tick`, third
   call `True`.
3. **Full guard** — `test_begin_full_tick_returns_false_when_in_flight`:
   same pattern as the quick guard.
4. **Quick / full independence** —
   `test_quick_and_full_tick_guards_are_independent`:
   `begin_quick_tick()` does not block `begin_full_tick()` and vice versa.
5. **Periodic / manual independence** —
   `test_periodic_tick_guards_independent_of_manual_refresh`:
   `begin_quick_tick()` does not block `begin_issue_fetch()` /
   `begin_pr_fetch()`; `begin_full_tick()` likewise; symmetrically the
   manual refresh flags do not block the tick guards.

## Acceptance

- All three quality checks green.
- The existing 14 tests in `test_branch_info_service.py` are unchanged
  and still pass.
- Single commit, e.g. `feat(icoder): add quick-fetch + tick guards to BranchInfoService`.
