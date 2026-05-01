"""BranchInfoBar — render-only widget for the branch + issue info area.

The widget owns no I/O. It receives a fully-formed ``BranchInfoView`` from an
external adapter and renders it into four ``Static`` zones plus three control
buttons. ``labels.json`` is loaded once at mount time so workflow status
labels render with their configured colors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static

from mcp_coder.config.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.services.branch_info import BranchInfo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BranchInfoView:
    """Snapshot consumed by ``BranchInfoBar.update_state``."""

    info: BranchInfo
    pr_number: Optional[int]
    pr_enabled: bool
    loading: frozenset[str] = field(default_factory=frozenset)
    failed: frozenset[str] = field(default_factory=frozenset)


def _color_to_rich_hex(color: Color) -> str:
    """Render a textual ``Color`` as a 6-digit hex string (no alpha).

    Rich's style parser rejects 8-digit hex colors, so we strip the alpha
    channel that ``Color.hex`` includes for non-opaque colors.

    Returns:
        A 6-digit ``#rrggbb`` hex string accepted by Rich's style parser.
    """
    return f"#{color.r:02x}{color.g:02x}{color.b:02x}"


def format_cache_age(last_checked: Optional[datetime], now: datetime) -> str:
    """Render a cache-age stamp at minute granularity.

    Args:
        last_checked: Timestamp of the last cache refresh, or ``None``.
        now: Reference "now" timestamp for the diff.

    Returns:
        ``""`` when ``last_checked is None``; ``"(<1m ago)"`` for sub-minute
        deltas; ``"(Xm ago)"`` otherwise.
    """
    if last_checked is None:
        return ""
    delta_min = int((now - last_checked).total_seconds() // 60)
    if delta_min < 1:
        return "(<1m ago)"
    return f"({delta_min}m ago)"


class BranchInfoBar(Vertical):
    """Two-row info area: branch/issue/PR/age + three controls."""

    class RefreshIssue(Message):
        """Posted when the user clicks the refresh-issue button."""

    class RefreshPR(Message):
        """Posted when the user clicks the refresh-PR button."""

    class TogglePR(Message):
        """Posted when the user clicks the PR toggle button."""

    def __init__(self, project_dir: Path) -> None:
        """Initialize with the project directory used to locate ``labels.json``.

        Args:
            project_dir: Project root, forwarded to ``get_labels_config_path``.
        """
        super().__init__()
        self._project_dir = project_dir
        self._label_colors: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """Compose the info row and the controls row.

        Yields:
            Horizontal containers for the info zones and the control buttons.
        """
        with Horizontal(id="branch-info-row"):
            yield Static("…", id="branch-info-branch")
            yield Static("…", id="branch-info-issue")
            yield Static("…", id="branch-info-pr")
            yield Static("…", id="branch-info-age")
        with Horizontal(id="branch-info-controls"):
            yield Button("↻ issue", id="branch-refresh-issue")
            yield Button("↻ PR", id="branch-refresh-pr")
            yield Button("PR:on|off", id="branch-toggle-pr")

    def on_mount(self) -> None:
        """Load workflow label colors from ``labels.json`` once."""
        try:
            cfg = load_labels_config(get_labels_config_path(self._project_dir))
            self._label_colors = {
                lbl["name"]: lbl["color"]
                for lbl in cfg.get("workflow_labels", [])
                if "name" in lbl and "color" in lbl
            }
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Failed to load label colors: %s", exc)
            self._label_colors = {}

    def update_state(self, view: Optional[BranchInfoView]) -> None:
        """Refresh the four zones from a single immutable view object.

        Args:
            view: The render snapshot, or ``None`` for the initial placeholder.
        """
        if view is None:
            self._set_zones("…", "…", "…", "…")
            return

        info = view.info
        if not info.is_git_repo:
            self._set_zones("(no git)", "—", "—", "—")
            return

        branch_text = self._render_branch_zone(info)
        issue_text = self._render_issue_zone(view)
        pr_text = self._render_pr_zone(view)
        age_text = self._render_age_zone(info)
        self._set_zones(branch_text, issue_text, pr_text, age_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Translate button presses into widget messages.

        Args:
            event: The Textual ``Button.Pressed`` event.
        """
        button_id = event.button.id
        if button_id == "branch-refresh-issue":
            self.post_message(self.RefreshIssue())
        elif button_id == "branch-refresh-pr":
            self.post_message(self.RefreshPR())
        elif button_id == "branch-toggle-pr":
            self.post_message(self.TogglePR())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_zones(
        self,
        branch: str | Text,
        issue: str | Text,
        pr: str | Text,
        age: str | Text,
    ) -> None:
        self.query_one("#branch-info-branch", Static).update(branch)
        self.query_one("#branch-info-issue", Static).update(issue)
        self.query_one("#branch-info-pr", Static).update(pr)
        self.query_one("#branch-info-age", Static).update(age)

    @staticmethod
    def _render_branch_zone(info: BranchInfo) -> str:
        branch = info.branch_name or "?"
        state = "dirty" if info.is_dirty else "clean"
        text = f"{branch} · {state}"
        if info.issue_number is None:
            text += " · (no issue)"
        return text

    def _render_issue_zone(self, view: BranchInfoView) -> str | Text:
        info = view.info
        if info.issue_number is None:
            return "—"
        if "issue" in view.loading:
            return "…"
        if "issue" in view.failed:
            return "?"

        text = Text()
        text.append(f"#{info.issue_number}")
        if info.issue_title:
            text.append(f" {info.issue_title}")
        if info.issue_status_label:
            text.append("  ")
            text.append(self._render_status_pill(info.issue_status_label))
        return text

    def _render_status_pill(self, label_name: str) -> Text:
        color_hex = self._label_colors.get(label_name)
        if not color_hex:
            return Text(label_name)
        try:
            bg = Color.parse(f"#{color_hex}")
            fg = bg.get_contrast_text()
            style = f"{_color_to_rich_hex(fg)} on {_color_to_rich_hex(bg)}"
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Failed to resolve contrast for %s: %s", label_name, exc)
            return Text(label_name)
        return Text(label_name, style=style)

    @staticmethod
    def _render_pr_zone(view: BranchInfoView) -> str:
        if view.info.issue_number is None:
            return "—"
        if not view.pr_enabled:
            return "—"
        if "pr" in view.loading:
            return "…"
        if "pr" in view.failed:
            return "?"
        if view.pr_number is None:
            return "PR —"
        return f"PR #{view.pr_number}"

    @staticmethod
    def _render_age_zone(info: BranchInfo) -> str:
        if info.cache_last_checked is None:
            return ""
        now = datetime.now(tz=info.cache_last_checked.tzinfo)
        return format_cache_age(info.cache_last_checked, now)
