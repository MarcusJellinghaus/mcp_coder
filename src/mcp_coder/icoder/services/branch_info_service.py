"""Adapter wrapping the data-layer branch info with toggle and in-flight state.

Thin passthrough to ``mcp_coder.services.branch_info``. Holds UI-facing
state (PR toggle, in-flight flags, last branch) so the app can short-circuit
duplicate clicks and detect branch changes between 2-second ticks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mcp_coder.services.branch_info import (
    BranchInfo,
    get_branch_info,
    get_pr_for_issue,
)


class BranchInfoService:
    """Adapter exposing branch-info data with simple state bookkeeping."""

    def __init__(self, project_dir: Path) -> None:
        """Initialize with the project directory used by the data layer.

        Args:
            project_dir: Project root passed through to ``get_branch_info``
                and ``get_pr_for_issue``.
        """
        self._project_dir = project_dir
        self._pr_enabled = False
        self._issue_in_flight = False
        self._pr_in_flight = False
        self._last_branch: Optional[str] = None

    @property
    def pr_enabled(self) -> bool:
        """Whether the PR toggle is currently on."""
        return self._pr_enabled

    def set_pr_enabled(self, value: bool) -> None:
        """Update the PR toggle state."""
        self._pr_enabled = value

    def fetch_info(self) -> BranchInfo:
        """Return the current ``BranchInfo`` snapshot from the data layer."""
        return get_branch_info(self._project_dir)

    def fetch_pr(self, issue_number: int) -> Optional[int]:
        """Resolve the PR number linked to ``issue_number`` via the data layer.

        Returns:
            The linked PR number, or ``None`` if no PR is linked.
        """
        return get_pr_for_issue(self._project_dir, issue_number)

    def begin_issue_fetch(self) -> bool:
        """Mark an issue fetch as in-flight; return False if already running.

        Returns:
            ``True`` if the flag was set, ``False`` if a fetch was already
            in-flight.
        """
        if self._issue_in_flight:
            return False
        self._issue_in_flight = True
        return True

    def end_issue_fetch(self) -> None:
        """Clear the issue in-flight flag."""
        self._issue_in_flight = False

    def begin_pr_fetch(self) -> bool:
        """Mark a PR fetch as in-flight; return False if already running.

        Returns:
            ``True`` if the flag was set, ``False`` if a fetch was already
            in-flight.
        """
        if self._pr_in_flight:
            return False
        self._pr_in_flight = True
        return True

    def end_pr_fetch(self) -> None:
        """Clear the PR in-flight flag."""
        self._pr_in_flight = False

    def branch_changed(self, branch_name: Optional[str]) -> bool:
        """Return True if ``branch_name`` differs from the last seen value."""
        changed = branch_name != self._last_branch
        self._last_branch = branch_name
        return changed
