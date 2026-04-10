"""Unit tests for _connection_status_suffix helper in app.py."""

from __future__ import annotations

from mcp_coder.icoder.ui.app import _connection_status_suffix
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus


class TestConnectionStatusSuffix:
    """Tests for _connection_status_suffix()."""

    def test_connected(self) -> None:
        """Returns '✓ Connected' for a connected server."""
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        assert _connection_status_suffix("mcp-tools-py", statuses) == "✓ Connected"

    def test_failed(self) -> None:
        """Returns '✗ <text>' for a failed server."""
        statuses = [
            ClaudeMCPStatus(
                name="mcp-tools-py", status_text="Failed to start", ok=False
            ),
        ]
        result = _connection_status_suffix("mcp-tools-py", statuses)
        assert result == "✗ Failed to start"

    def test_not_found(self) -> None:
        """Returns '' when server name is not in statuses."""
        statuses = [
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ]
        assert _connection_status_suffix("mcp-other", statuses) == ""

    def test_none_statuses(self) -> None:
        """Returns '' when statuses is None."""
        assert _connection_status_suffix("mcp-tools-py", None) == ""
