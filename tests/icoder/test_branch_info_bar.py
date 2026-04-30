"""Render-only tests for the BranchInfoBar widget."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from mcp_coder.icoder.ui.widgets.branch_info_bar import (
    BranchInfoBar,
    BranchInfoView,
    format_cache_age,
)
from mcp_coder.services.branch_info import BranchInfo

pytestmark = pytest.mark.textual_integration


def _make_info(
    *,
    is_git_repo: bool = True,
    branch: str | None = "main",
    is_dirty: bool = False,
    issue_number: int | None = None,
    issue_title: str | None = None,
    status_label: str | None = None,
    cache_last_checked: datetime | None = None,
) -> BranchInfo:
    return BranchInfo(
        is_git_repo=is_git_repo,
        branch_name=branch,
        is_dirty=is_dirty,
        issue_number=issue_number,
        issue_title=issue_title,
        issue_status_label=status_label,
        cache_last_checked=cache_last_checked,
    )


class _BarApp(App[None]):
    """Minimal host app for BranchInfoBar."""

    def __init__(self, project_dir: Path) -> None:
        super().__init__()
        self._project_dir = project_dir

    def compose(self) -> ComposeResult:
        """Yield the bar.

        Yields:
            BranchInfoBar instance.
        """
        yield BranchInfoBar(self._project_dir)


def _zone_texts(bar: BranchInfoBar) -> dict[str, str]:
    """Read current rendered text of all four zones."""
    out: dict[str, str] = {}
    for zone_id in ("branch", "issue", "pr", "age"):
        widget = bar.query_one(f"#branch-info-{zone_id}", Static)
        rendered = widget.render()
        out[zone_id] = str(rendered)
    return out


# ---------------------------------------------------------------------------
# Pure helper
# ---------------------------------------------------------------------------


def test_format_cache_age_minutes_only() -> None:
    """format_cache_age uses minute granularity only."""
    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    assert format_cache_age(None, now) == ""
    assert (
        format_cache_age(datetime(2026, 4, 30, 11, 59, 30, tzinfo=timezone.utc), now)
        == "(<1m ago)"
    )
    assert (
        format_cache_age(datetime(2026, 4, 30, 11, 58, tzinfo=timezone.utc), now)
        == "(2m ago)"
    )


# ---------------------------------------------------------------------------
# Render-state tests
# ---------------------------------------------------------------------------


async def test_renders_placeholder_when_view_none(tmp_path: Path) -> None:
    """update_state(None) renders an ellipsis placeholder."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        bar.update_state(None)
        await pilot.pause()
        zones = _zone_texts(bar)
        assert zones["branch"] == "…"
        assert zones["issue"] == "…"
        assert zones["pr"] == "…"
        assert zones["age"] == "…"


async def test_renders_no_git_state(tmp_path: Path) -> None:
    """A view whose info is_git_repo=False shows '(no git)' + dashes."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        view = BranchInfoView(
            info=_make_info(is_git_repo=False, branch=None),
            pr_number=None,
            pr_enabled=True,
        )
        bar.update_state(view)
        await pilot.pause()
        zones = _zone_texts(bar)
        assert zones["branch"] == "(no git)"
        assert zones["issue"] == "—"
        assert zones["pr"] == "—"
        assert zones["age"] == "—"


async def test_renders_no_issue_branch(tmp_path: Path) -> None:
    """Branch without an issue suffix renders '(no issue)'."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        view = BranchInfoView(
            info=_make_info(branch="main", is_dirty=False, issue_number=None),
            pr_number=None,
            pr_enabled=True,
        )
        bar.update_state(view)
        await pilot.pause()
        zones = _zone_texts(bar)
        assert zones["branch"] == "main · clean · (no issue)"
        assert zones["issue"] == "—"
        assert zones["pr"] == "—"


async def test_renders_full_state_with_status_pill(tmp_path: Path) -> None:
    """A complete view renders branch, issue, PR, and age zones."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        view = BranchInfoView(
            info=_make_info(
                branch="123-foo",
                is_dirty=True,
                issue_number=123,
                issue_title="Fix things",
                status_label="status-04:plan-review",
                cache_last_checked=datetime.now(tz=timezone.utc),
            ),
            pr_number=45,
            pr_enabled=True,
        )
        bar.update_state(view)
        await pilot.pause()
        zones = _zone_texts(bar)
        assert zones["branch"] == "123-foo · dirty"
        assert "#123" in zones["issue"]
        assert "Fix things" in zones["issue"]
        assert "status-04:plan-review" in zones["issue"]
        assert zones["pr"] == "PR #45"
        assert "ago)" in zones["age"]


async def test_pr_zone_dash_when_toggle_off(tmp_path: Path) -> None:
    """pr_enabled=False renders '—' regardless of pr_number."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        view = BranchInfoView(
            info=_make_info(branch="42-x", issue_number=42, issue_title="t"),
            pr_number=999,
            pr_enabled=False,
        )
        bar.update_state(view)
        await pilot.pause()
        assert _zone_texts(bar)["pr"] == "—"


async def test_loading_field_shows_ellipsis(tmp_path: Path) -> None:
    """loading={'issue'|'pr'} renders the matching zone as '…'."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        info = _make_info(branch="42-x", issue_number=42, issue_title="t")

        bar.update_state(
            BranchInfoView(
                info=info,
                pr_number=None,
                pr_enabled=True,
                loading=frozenset({"issue"}),
            )
        )
        await pilot.pause()
        assert _zone_texts(bar)["issue"] == "…"

        bar.update_state(
            BranchInfoView(
                info=info,
                pr_number=None,
                pr_enabled=True,
                loading=frozenset({"pr"}),
            )
        )
        await pilot.pause()
        assert _zone_texts(bar)["pr"] == "…"


async def test_failed_field_shows_question(tmp_path: Path) -> None:
    """failed={'pr'} renders the PR zone as '?'."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        view = BranchInfoView(
            info=_make_info(branch="42-x", issue_number=42, issue_title="t"),
            pr_number=None,
            pr_enabled=True,
            failed=frozenset({"pr"}),
        )
        bar.update_state(view)
        await pilot.pause()
        assert _zone_texts(bar)["pr"] == "?"


async def test_unknown_status_label_renders_with_default_color(tmp_path: Path) -> None:
    """A status label not present in labels.json renders without crashing."""
    app = _BarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.query_one(BranchInfoBar)
        view = BranchInfoView(
            info=_make_info(
                branch="42-x",
                issue_number=42,
                issue_title="t",
                status_label="status-99:unknown-label",
            ),
            pr_number=None,
            pr_enabled=True,
        )
        bar.update_state(view)
        await pilot.pause()
        assert "status-99:unknown-label" in _zone_texts(bar)["issue"]


async def test_button_press_posts_messages(tmp_path: Path) -> None:
    """Each control button posts the matching widget message."""
    captured: list[type] = []

    class _CapturingBarApp(_BarApp):
        def on_branch_info_bar_refresh_issue(
            self, _: BranchInfoBar.RefreshIssue
        ) -> None:
            captured.append(BranchInfoBar.RefreshIssue)

        def on_branch_info_bar_refresh_pr(self, _: BranchInfoBar.RefreshPR) -> None:
            captured.append(BranchInfoBar.RefreshPR)

        def on_branch_info_bar_toggle_pr(self, _: BranchInfoBar.TogglePR) -> None:
            captured.append(BranchInfoBar.TogglePR)

    app = _CapturingBarApp(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#branch-refresh-issue")
        await pilot.pause()
        await pilot.click("#branch-refresh-pr")
        await pilot.pause()
        await pilot.click("#branch-toggle-pr")
        await pilot.pause()

    assert BranchInfoBar.RefreshIssue in captured
    assert BranchInfoBar.RefreshPR in captured
    assert BranchInfoBar.TogglePR in captured
