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

    def update_state(
        self,
        info: BranchInfo | None,
        pr_number: int | None,
        pr_enabled: bool,
        loading: set[str],     # subset of {"issue", "pr"}
        failed: set[str],      # subset of {"issue", "pr"}
    ) -> None: ...

    def on_button_pressed(self, event: Button.Pressed) -> None: ...
```

Button IDs: `branch-refresh-issue`, `branch-refresh-pr`, `branch-toggle-pr`.

## HOW

- `compose()` yields:
  - `Horizontal(id="branch-info-row")` containing four `Static` zones
    (branch+dirty, issue, pr, age) — widget keeps refs by id for fast updates.
  - `Horizontal(id="branch-info-controls")` with three `Button`s.
- `on_mount`: call `get_labels_config_path(project_dir)` +
  `load_labels_config(...)`; build `dict[str, str]` mapping label name → 6-digit
  hex; store on `self._label_colors`. Wrap in try/except → empty dict on
  failure (widget renders raw labels with neutral colors).
- `update_state` rules (single source of truth):
  - `info is None` → all four zones show `…`.
  - `not info.is_git_repo` → row reads `(no git)`, all other zones `—`.
  - `info.issue_number is None` → `branch · clean|dirty · (no issue)`,
    issue/pr zones `—`.
  - Otherwise: `branch · clean|dirty   #N title   STATUSPILL   PR_ZONE   (Xm ago)`.
  - PR zone: `—` when `pr_enabled=False`, `…` when `"pr" in loading`,
    `?` when `"pr" in failed`, else `PR #M` or `PR —` if number is None.
  - Issue zone uses `…` for `"issue" in loading` and `?` for failed.
  - Status pill: build a Rich `Text` with `style=f"on #{hex}"` and foreground
    via `Color.parse(f"#{hex}").get_contrast_text()`. Unknown labels use
    neutral default (no background).
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
update_state(info, pr_number, pr_enabled, loading, failed):
    if info is None: render_placeholder("…"); return
    if not info.is_git_repo: render_no_git(); return
    branch_zone = f"{info.branch_name} · {'dirty' if info.is_dirty else 'clean'}"
    if info.issue_number is None: branch_zone += " · (no issue)"
    issue_zone = render_issue_field(info, "issue" in loading, "issue" in failed)
    pr_zone = render_pr_field(pr_number, pr_enabled, "pr" in loading, "pr" in failed)
    age_zone = format_cache_age(info.cache_last_checked, datetime.now(tz=...))
    update_static_widgets(branch_zone, issue_zone, pr_zone, age_zone)
```

## DATA

- Posted messages: `RefreshIssue`, `RefreshPR`, `TogglePR` — empty payload,
  app handles them.
- Internal: `self._label_colors: dict[str, str]`,
  `self._project_dir: Path`.

## Tests (TDD — write first)

`tests/icoder/test_branch_info_bar.py` (mark `pytestmark =
pytest.mark.textual_integration` since they need a running App):

1. `test_renders_placeholder_when_info_none` — pilot, send
   `update_state(None, None, False, set(), set())`, assert "…" in row text.
2. `test_renders_no_git_state` — `BranchInfo(is_git_repo=False, ...)`,
   assert `"(no git)"` and three `"—"` markers.
3. `test_renders_no_issue_branch` — branch=`"main"`, `issue_number=None`;
   assert `"main · clean · (no issue)"` + dashes for issue/pr.
4. `test_renders_full_state_with_status_pill` — branch=`"123-foo"`,
   issue 123 with status `"status-04:plan-review"`; assert `"#123"`, title,
   status pill text, `PR #45` (when `pr_number=45, pr_enabled=True`),
   age text.
5. `test_pr_zone_dash_when_toggle_off` — assert `"—"` regardless of
   `pr_number`.
6. `test_loading_field_shows_ellipsis` — `loading={"issue"}` → issue zone is
   `"…"`; `loading={"pr"}` → pr zone is `"…"`.
7. `test_failed_field_shows_question` — `failed={"pr"}` → pr zone is `"?"`.
8. `test_unknown_status_label_renders_with_default_color` — label not in
   `labels.json` → no crash, raw label text appears.
9. `test_button_press_posts_messages` — pilot, click each button by ID,
   assert correct message types appear in `app.message_queue` (or capture via
   `on_*` handler).
10. `test_format_cache_age_minutes_only` — unit-test the private helper:
    `<1m → "(<1m ago)"`, `2m → "(2m ago)"`, `None → ""`.

Run pytest with `-m "not ..."` exclusion + `pytest -m textual_integration`
for the pilot tests. Then pylint + mypy. One commit.
