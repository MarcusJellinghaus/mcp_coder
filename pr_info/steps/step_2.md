# Step 2 — Render-only widget: `BranchInfoBar`

## LLM Prompt

> Implement Step 2 of issue #844. Read `pr_info/steps/summary.md` and
> `pr_info/steps/step_1.md` for context (Step 1 is already merged).
> This step builds the pure-render Textual widget plus its CSS, with no I/O.
> Tests construct `BranchInfo` instances directly and assert on rendered
> content. **TDD**: write the tests first. End with one commit; all checks
> green.

## WHERE

```
src/mcp_coder/icoder/ui/widgets/branch_info_bar.py   (new)
src/mcp_coder/icoder/ui/styles.py                    (modify — add CSS rules)
tests/icoder/test_branch_info_bar.py                 (new)
```

## WHAT

```python
# src/mcp_coder/icoder/ui/widgets/branch_info_bar.py
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static

from mcp_coder.services.branch_info import BranchInfo

class BranchInfoBar(Vertical):
    class RefreshIssue(Message): pass
    class RefreshPR(Message): pass
    class TogglePR(Message): pass

    def __init__(self, project_dir: Path) -> None: ...
    def on_mount(self) -> None: ...        # load labels.json once

    def update_state(self, view: BranchInfoView | None) -> None: ...

    def on_button_pressed(self, event: Button.Pressed) -> None: ...
```

Render-state consolidation (decision: **option (b) — `BranchInfoView`
dataclass**):

```python
# Same module as BranchInfoBar (or in branch_info.py if shared)
from dataclasses import dataclass, field

@dataclass(frozen=True)
class BranchInfoView:
    info: BranchInfo                    # never None — placeholder uses sentinel
    pr_number: int | None
    pr_enabled: bool
    loading: frozenset[str] = frozenset()  # subset of {"issue", "pr"}
    failed: frozenset[str] = frozenset()   # subset of {"issue", "pr"}
```

`update_state(None)` keeps its meaning ("nothing fetched yet → render `…`
placeholder"). The widget API takes a single immutable argument; the adapter
(Step 3) constructs the `BranchInfoView` per render. **Why option (b) over
moving `loading`/`failed` into `BranchInfo`**: `BranchInfo` is a pure data-
layer dataclass (Step 1) describing the on-disk/git state — it should not
carry UI-only flags. The view dataclass keeps that boundary clean.

Button IDs: `branch-refresh-issue`, `branch-refresh-pr`, `branch-toggle-pr`.

## HOW

- `compose()` yields:
  - `Horizontal(id="branch-info-row")` containing four `Static` zones
    (branch+dirty, issue, pr, age) — widget keeps refs by id for fast updates.
  - `Horizontal(id="branch-info-controls")` with three `Button`s.
- `on_mount`: call `get_labels_config_path(self._project_dir)` +
  `load_labels_config(path)` from `mcp_coder.config.label_config`. Build the
  name→color mapping inline (no upstream `build_label_lookups` change
  required):

  ```python
  cfg = load_labels_config(get_labels_config_path(self._project_dir))
  self._label_colors: dict[str, str] = {
      lbl["name"]: lbl["color"] for lbl in cfg.get("workflow_labels", [])
  }
  ```

  Wrap the whole block in `try/except Exception` → empty dict on failure
  (widget renders raw labels with neutral colors). Do NOT introduce a new
  helper or modify `build_label_lookups` upstream.
- `update_state(view)` rules (single source of truth, single argument):
  - `view is None` → all four zones show `…`.
  - `not view.info.is_git_repo` → row reads `(no git)`, all other zones `—`.
  - `view.info.issue_number is None` → `branch · clean|dirty · (no issue)`,
    issue/pr zones `—`.
  - Otherwise: `branch · clean|dirty   #N title   STATUSPILL   PR_ZONE   (Xm ago)`.
  - PR zone: `—` when `view.pr_enabled is False`, `…` when `"pr" in view.loading`,
    `?` when `"pr" in view.failed`, else `PR #M` (using `view.pr_number`) or
    `PR —` if `view.pr_number is None`.
  - Issue zone uses `…` for `"issue" in view.loading` and `?` for failed.
  - Status pill: build a Rich `Text` with `style=f"on #{hex}"` and foreground
    via `Color.parse(f"#{hex}").get_contrast_text()`. Unknown labels (not in
    `self._label_colors`) use neutral default (no background).
- `on_button_pressed`: dispatch by button ID, post the corresponding `Message`.
  Don't disable buttons during in-flight; the adapter (Step 3) will ignore
  duplicate clicks.
- Cache-age helper (private function in this module):
  ```python
  def format_cache_age(last_checked: datetime | None, now: datetime) -> str:
      if last_checked is None: return ""
      delta_min = int((now - last_checked).total_seconds() // 60)
      return "(<1m ago)" if delta_min < 1 else f"({delta_min}m ago)"
  ```

CSS additions in `icoder/ui/styles.py`:

```css
BranchInfoBar { height: 2; background: #1e1e1e; color: #d4d4d4; }
#branch-info-row { height: 1; }
#branch-info-controls { height: 1; }
#branch-info-controls Button { height: 1; min-width: 3; border: none; padding: 0 1; }
```

## ALGORITHM

```
update_state(view):
    if view is None: render_placeholder("…"); return
    info = view.info
    if not info.is_git_repo: render_no_git(); return
    branch_zone = f"{info.branch_name} · {'dirty' if info.is_dirty else 'clean'}"
    if info.issue_number is None: branch_zone += " · (no issue)"
    issue_zone = render_issue_field(info, "issue" in view.loading, "issue" in view.failed)
    pr_zone = render_pr_field(view.pr_number, view.pr_enabled,
                              "pr" in view.loading, "pr" in view.failed)
    age_zone = format_cache_age(info.cache_last_checked, datetime.now(tz=...))
    update_static_widgets(branch_zone, issue_zone, pr_zone, age_zone)
```

## DATA

- Posted messages: `RefreshIssue`, `RefreshPR`, `TogglePR` — empty payload,
  app handles them.
- Public input: `BranchInfoView` (frozen dataclass) — see WHAT.
- Internal: `self._label_colors: dict[str, str]`,
  `self._project_dir: Path`.

## Tests (TDD — write first)

`tests/icoder/test_branch_info_bar.py` (mark `pytestmark =
pytest.mark.textual_integration` since they need a running App):

All tests construct `BranchInfoView` instances directly and pass them to
`widget.update_state(view)`. No mocked I/O — the widget is render-only.

1. `test_renders_placeholder_when_view_none` — pilot, call
   `update_state(None)`, assert "…" in row text.
2. `test_renders_no_git_state` — view with
   `info=BranchInfo(is_git_repo=False, ...)`; assert `"(no git)"` and three
   `"—"` markers.
3. `test_renders_no_issue_branch` — `branch="main"`, `issue_number=None`;
   assert `"main · clean · (no issue)"` + dashes for issue/pr.
4. `test_renders_full_state_with_status_pill` — `branch="123-foo"`, issue
   123 with status `"status-04:plan-review"`; view with `pr_number=45,
   pr_enabled=True`; assert `"#123"`, title, status pill text, `PR #45`,
   age text.
5. `test_pr_zone_dash_when_toggle_off` — `pr_enabled=False`; assert `"—"`
   regardless of `pr_number`.
6. `test_loading_field_shows_ellipsis` — `loading=frozenset({"issue"})` →
   issue zone is `"…"`; `loading=frozenset({"pr"})` → pr zone is `"…"`.
7. `test_failed_field_shows_question` — `failed=frozenset({"pr"})` → pr
   zone is `"?"`.
8. `test_unknown_status_label_renders_with_default_color` — label not in
   `labels.json` → no crash, raw label text appears.
9. `test_button_press_posts_messages` — use Textual's `Pilot` pattern:

   ```python
   async with app.run_test() as pilot:
       captured: list[type] = []

       def handler(message):
           captured.append(type(message))

       widget = app.query_one(BranchInfoBar)
       app.on(BranchInfoBar.RefreshIssue)(handler)
       app.on(BranchInfoBar.RefreshPR)(handler)
       app.on(BranchInfoBar.TogglePR)(handler)
       await pilot.click("#branch-refresh-issue")
       await pilot.pause()
       await pilot.click("#branch-refresh-pr")
       await pilot.pause()
       await pilot.click("#branch-toggle-pr")
       await pilot.pause()
       assert BranchInfoBar.RefreshIssue in captured
       assert BranchInfoBar.RefreshPR in captured
       assert BranchInfoBar.TogglePR in captured
   ```

   The exact handler-registration API may differ — use whatever pattern the
   existing `tests/icoder/ui/test_app.py` already uses for message capture.
   **Do not** reference `app.message_queue` (private API; observe state via
   `pilot.click(...)` + assertions on app/widget state instead).
10. `test_format_cache_age_minutes_only` — unit-test the private helper:
    `<1m → "(<1m ago)"`, `2m → "(2m ago)"`, `None → ""`.

Run pytest with `-m "not ..."` exclusion + `pytest -m textual_integration`
for the pilot tests. Then pylint + mypy. One commit.
