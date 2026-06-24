"""Tests for tool-formatting helpers and the pending-tool FIFO.

Split out of ``test_stream_renderer.py`` to keep each module under the
file-size limit. Covers ``format_tool_oneline``/``format_tool_compressed``
and ``StreamEventRenderer`` FIFO pairing.
"""

import time

from mcp_coder.llm.formatting.render_actions import ToolResult
from mcp_coder.llm.formatting.stream_renderer import (
    StreamEventRenderer,
    format_tool_compressed,
    format_tool_oneline,
)


class TestFormatToolOneline:
    """Tests for format_tool_oneline()."""

    def test_format_tool_oneline_done_with_duration(self) -> None:
        """Completed tool shows '→ done' and the duration suffix."""
        result = format_tool_oneline(
            name="read_file",
            args={"path": "src/main.py"},
            duration_ms=120,
            is_error=False,
        )
        assert "→ done" in result
        assert "(120ms)" in result

    def test_format_tool_oneline_running(self) -> None:
        """Running tool shows 'running…' with no ms suffix."""
        result = format_tool_oneline(
            name="read_file",
            args={"path": "src/main.py"},
            duration_ms=None,
            is_error=False,
        )
        assert "running…" in result
        assert "ms" not in result

    def test_format_tool_oneline_error(self) -> None:
        """Errored tool with duration shows '→ error' and the duration suffix."""
        result = format_tool_oneline(
            name="Bash",
            args={"command": "git status"},
            duration_ms=50,
            is_error=True,
        )
        assert "→ error" in result
        assert "(50ms)" in result

    def test_format_tool_oneline_error_without_duration(self) -> None:
        """Errored tool cancelled before completion shows '→ error', no ms suffix."""
        result = format_tool_oneline(
            name="Bash",
            args={"command": "git status"},
            duration_ms=None,
            is_error=True,
        )
        assert "→ error" in result
        assert "ms" not in result

    def test_format_tool_oneline_no_args(self) -> None:
        """Empty args render as 'name()' with no inner content."""
        result = format_tool_oneline(
            name="Bash",
            args={},
            duration_ms=50,
            is_error=False,
        )
        assert result == "⚙ Bash() → done (50ms)"

    def test_format_tool_oneline_truncates_long_arg_value(self) -> None:
        """A long first-arg rendered value is capped at ~40 chars with ellipsis.

        ``_render_value_compact`` renders strings up to 80 chars verbatim
        (with quotes), so a 60-char value produces a rendering longer than the
        40-char oneline cap and triggers truncation.
        """
        long_value = "x" * 60
        result = format_tool_oneline(
            name="read_file",
            args={"path": long_value},
            duration_ms=10,
            is_error=False,
        )
        assert "…" in result
        # Full 60-char value must not appear verbatim.
        assert long_value not in result

    def test_format_tool_oneline_uses_first_arg_only(self) -> None:
        """Only the first arg value (insertion order) appears in the parentheses."""
        result = format_tool_oneline(
            name="some_tool",
            args={"first": "alpha", "second": "beta", "third": "gamma"},
            duration_ms=10,
            is_error=False,
        )
        assert "alpha" in result
        assert "beta" not in result
        assert "gamma" not in result


class TestFormatToolCompressed:
    """Tests for format_tool_compressed()."""

    def test_format_tool_compressed_done(self) -> None:
        """Successful tool renders body lines and a done footer with ms."""
        result = format_tool_compressed(
            name="read_file",
            args={"path": "src/main.py"},
            output_lines=("a", "b"),
            total_lines=2,
            truncated=False,
            duration_ms=120,
            is_error=False,
        )
        assert result[0].startswith("│  ")
        assert result[1].startswith("│  ")
        assert result[-1] == "└ done (2 lines, 120ms)"

    def test_format_tool_compressed_error(self) -> None:
        """Errored tool collapses the footer to a bare error marker."""
        result = format_tool_compressed(
            name="Bash",
            args={"command": "git status"},
            output_lines=("boom",),
            total_lines=1,
            truncated=False,
            duration_ms=50,
            is_error=True,
        )
        assert result[-1] == "└ error"

    def test_format_tool_compressed_empty_output(self) -> None:
        """Empty output yields only the footer line, no body lines."""
        result = format_tool_compressed(
            name="Bash",
            args={},
            output_lines=(),
            total_lines=0,
            truncated=False,
            duration_ms=None,
            is_error=False,
        )
        assert len(result) == 1
        assert result[0].startswith("└")


class TestRendererPendingFifo:
    """Tests for pending-tool FIFO pairing and cleanup_pending()."""

    def test_pairs_start_and_result_computes_duration(self) -> None:
        """Start then result for the same name yields a positive duration_ms."""
        renderer = StreamEventRenderer()
        renderer.render({"type": "tool_use_start", "name": "Bash", "args": {}})
        time.sleep(0.001)
        action = renderer.render(
            {"type": "tool_result", "name": "Bash", "output": "ok"}
        )
        assert isinstance(action, ToolResult)
        assert action.duration_ms is not None
        assert action.duration_ms >= 0

    def test_unmatched_result_has_none_duration(self) -> None:
        """A tool_result with no matching start has duration_ms is None."""
        renderer = StreamEventRenderer()
        action = renderer.render(
            {"type": "tool_result", "name": "Bash", "output": "ok"}
        )
        assert isinstance(action, ToolResult)
        assert action.duration_ms is None

    def test_interleaved_pairing_by_name(self) -> None:
        """start_A, start_B, result_B, result_A → both paired by name."""
        renderer = StreamEventRenderer()
        renderer.render({"type": "tool_use_start", "name": "A", "args": {}})
        renderer.render({"type": "tool_use_start", "name": "B", "args": {}})
        result_b = renderer.render({"type": "tool_result", "name": "B", "output": "ok"})
        result_a = renderer.render({"type": "tool_result", "name": "A", "output": "ok"})
        assert isinstance(result_b, ToolResult)
        assert isinstance(result_a, ToolResult)
        assert result_b.duration_ms is not None
        assert result_a.duration_ms is not None

    def test_cleanup_pending_synthesizes_cancelled_results(self) -> None:
        """Orphaned start → cleanup_pending returns one cancelled ToolResult."""
        renderer = StreamEventRenderer()
        renderer.render({"type": "tool_use_start", "name": "Bash", "args": {}})
        cancelled = renderer.cleanup_pending()
        assert len(cancelled) == 1
        result = cancelled[0]
        assert result.is_error is True
        assert result.output_lines == ["(cancelled)"]
        assert result.total_lines == 1
        assert result.truncated is False
        assert result.duration_ms is None
        # Second call returns empty — FIFO was cleared.
        assert renderer.cleanup_pending() == []

    def test_stream_done_does_not_auto_clean(self) -> None:
        """render({'type': 'done'}) does NOT clear the pending FIFO."""
        renderer = StreamEventRenderer()
        renderer.render({"type": "tool_use_start", "name": "Bash", "args": {}})
        renderer.render({"type": "done"})
        # FIFO still holds the orphan — app must call cleanup_pending explicitly.
        cancelled = renderer.cleanup_pending()
        assert len(cancelled) == 1

    def test_renderer_state_survives_across_turns(self) -> None:
        """A start in one turn pairs with a result in a later turn."""
        renderer = StreamEventRenderer()
        renderer.render({"type": "tool_use_start", "name": "Bash", "args": {}})
        renderer.render({"type": "done"})  # turn 1 ends, no cleanup
        action = renderer.render(
            {"type": "tool_result", "name": "Bash", "output": "ok"}
        )
        assert isinstance(action, ToolResult)
        assert action.duration_ms is not None

    def test_tool_result_carries_raw_name(self) -> None:
        """raw_name is the event's raw name for both live and cancelled paths."""
        # Live path
        renderer = StreamEventRenderer()
        renderer.render({"type": "tool_use_start", "name": "Bash", "args": {}})
        live = renderer.render({"type": "tool_result", "name": "Bash", "output": "ok"})
        assert isinstance(live, ToolResult)
        assert live.raw_name == "Bash"

        # Cancelled path
        renderer2 = StreamEventRenderer()
        renderer2.render({"type": "tool_use_start", "name": "Bash", "args": {}})
        cancelled = renderer2.cleanup_pending()
        assert cancelled[0].raw_name == "Bash"
