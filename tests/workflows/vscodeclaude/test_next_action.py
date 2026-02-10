"""Tests for get_next_action with blocked_label parameter."""

from mcp_coder.workflows.vscodeclaude.status import get_next_action


class TestGetNextActionBlocked:
    """Tests for get_next_action with blocked_label parameter."""

    def test_blocked_clean_returns_blocked_message(self) -> None:
        """Blocked + clean folder shows Blocked message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "Blocked (blocked)"

    def test_blocked_with_wait_label(self) -> None:
        """Blocked with wait label shows correct message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="wait",
        )
        assert result == "Blocked (wait)"

    def test_blocked_dirty_returns_manual(self) -> None:
        """Blocked + dirty folder shows Manual message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=True,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "!! Manual"

    def test_blocked_but_running_returns_active(self) -> None:
        """Running VSCode takes priority over blocked."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=True,
            blocked_label="blocked",
        )
        assert result == "(active)"

    def test_blocked_and_stale_blocked_takes_priority(self) -> None:
        """Blocked takes priority over stale when both true."""
        result = get_next_action(
            is_stale=True,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "Blocked (blocked)"

    def test_none_blocked_label_normal_behavior(self) -> None:
        """None blocked_label maintains normal behavior."""
        # Not stale, not dirty, not running -> Restart
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label=None,
        )
        assert "Restart" in result

    def test_default_parameter_backward_compatible(self) -> None:
        """Function works without blocked_label parameter."""
        # Call without the new parameter
        result = get_next_action(
            is_stale=False, is_dirty=False, is_vscode_running=False
        )
        assert "Restart" in result

    def test_preserves_label_case_in_output(self) -> None:
        """Output preserves the case of the label passed in."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="Blocked",  # Capital B
        )
        assert result == "Blocked (Blocked)"

    def test_blocked_dirty_and_stale_returns_manual(self) -> None:
        """Blocked + dirty + stale still shows Manual message."""
        result = get_next_action(
            is_stale=True,
            is_dirty=True,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "!! Manual"
