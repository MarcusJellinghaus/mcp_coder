# Step 3 — Adapter: `BranchInfoService`

## LLM Prompt

> Implement Step 3 of issue #844. Read `pr_info/steps/summary.md` and Steps 1
> and 2 (already merged) for context. This step adds the thin iCoder adapter
> wrapping the Step 1 data layer with toggle state, in-flight flags, and
> branch-change detection. **TDD**: write the tests first. End with one
> commit; all checks green.

## WHERE

```
src/mcp_coder/icoder/services/branch_info_service.py   (new)
tests/icoder/test_branch_info_service.py               (new)
```

## WHAT

```python
# src/mcp_coder/icoder/services/branch_info_service.py
from pathlib import Path

from mcp_coder.services.branch_info import BranchInfo, get_branch_info, get_pr_for_issue

class BranchInfoService:
    def __init__(self, project_dir: Path) -> None: ...

    @property
    def pr_enabled(self) -> bool: ...
    def set_pr_enabled(self, value: bool) -> None: ...

    def fetch_info(self) -> BranchInfo: ...
    def fetch_pr(self, issue_number: int) -> int | None: ...

    def begin_issue_fetch(self) -> bool: ...   # False if already in flight
    def end_issue_fetch(self) -> None: ...
    def begin_pr_fetch(self) -> bool: ...
    def end_pr_fetch(self) -> None: ...

    def branch_changed(self, branch_name: str | None) -> bool: ...
```

## HOW

- `__init__` stores `project_dir`. Initial state: `pr_enabled=False`,
  `issue_in_flight=False`, `pr_in_flight=False`, `last_branch=None`.
- Note: race-protection state (`pr_fetch_generation`) is added in Step 4
  on top of this adapter; it is intentionally absent here so Step 3 stays
  a thin passthrough.
- `fetch_info()` — passthrough to `get_branch_info(self.project_dir)`. Pure
  delegation, no state mutation. (App calls this from a worker thread.)
- `fetch_pr(issue_number)` — passthrough to
  `get_pr_for_issue(self.project_dir, issue_number)`. Lets exceptions
  propagate to the caller; the worker (in Step 4's app integration) is
  responsible for catching and surfacing failures (adding `"pr"` to the
  failed set). Keeps the adapter a trivial passthrough.
- `set_pr_enabled(value)` updates the toggle. **Important**: when going from
  on→off, the next `fetch_pr` result that arrives must be ignored by the app
  (per issue: "drop in-flight result silently"). The adapter doesn't gate
  this — the app checks `service.pr_enabled` after `fetch_pr` returns and
  drops the value if False. Keeps adapter trivial.
- `begin_*_fetch()` — atomic check-and-set: returns `True` and sets flag if
  not already in flight; returns `False` (no state change) if already
  in flight. Used by app handlers to short-circuit duplicate clicks.
- `end_*_fetch()` — clears the flag. Always called in a `finally:` block by
  the app after a worker completes (success or failure).
- `branch_changed(branch_name)` — compares against `last_branch`, updates it,
  returns `True` if different. Called once per 2s tick from the app.

## ALGORITHM

```
class BranchInfoService:
    def __init__(self, project_dir):
        self._project_dir = project_dir
        self._pr_enabled = False
        self._issue_in_flight = False
        self._pr_in_flight = False
        self._last_branch = None

    def begin_issue_fetch(self):
        if self._issue_in_flight: return False
        self._issue_in_flight = True; return True

    def branch_changed(self, name):
        changed = name != self._last_branch
        self._last_branch = name
        return changed
```

## DATA

- All public methods return primitives or `BranchInfo` from the data layer.
- No new dataclasses introduced in this layer.

## Tests (TDD — write first)

`tests/icoder/test_branch_info_service.py` — pure unit tests, no Textual:

1. `test_initial_state_pr_disabled_and_no_branch` — assert `pr_enabled is
   False`, `branch_changed(None)` returns False on first call.
2. `test_set_pr_enabled_toggles` — set True, get True; set False, get False.
3. `test_begin_issue_fetch_returns_false_when_in_flight` — first call True,
   second call False without `end_issue_fetch`.
4. `test_end_issue_fetch_resets_flag` — begin, end, begin again returns True.
5. `test_begin_pr_fetch_independent_of_issue_fetch` — issue in flight does
   not block pr begin.
6. `test_branch_changed_detects_first_real_branch` — start with
   `last_branch=None`; first call with `"main"` returns True; second call
   with `"main"` returns False.
7. `test_branch_changed_detects_switch` — `"main"` → `"123-feature"`
   returns True.
8. `test_fetch_info_delegates_to_data_layer` — patch
   `mcp_coder.services.branch_info.get_branch_info` (where the adapter
   imports it from); assert it was called once with `project_dir`.
9. `test_fetch_pr_delegates_to_data_layer` — patch `get_pr_for_issue`
   (where the adapter imports it from); assert called with
   `(project_dir, issue_number)`.

Run unit tests + pylint + mypy. One commit.
