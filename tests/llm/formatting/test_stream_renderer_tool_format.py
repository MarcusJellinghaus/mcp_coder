"""Tests for tool-formatting helpers and the pending-tool FIFO.

Split out of ``test_stream_renderer.py`` to keep each module under the
file-size limit. Covers ``format_tool_oneline``/``format_tool_compressed``
and ``StreamEventRenderer`` FIFO pairing.
"""

import time
from collections import deque

import pytest

from mcp_coder.llm.formatting.render_actions import ToolResult
from mcp_coder.llm.formatting.stream_renderer import (
    StreamEventRenderer,
    format_tool_compressed,
    format_tool_oneline,
    pop_pending_tool,
)

_CLOCK_TARGET = "mcp_coder.llm.formatting.stream_renderer.time"


class _FakeClock:
    """Scripted stand-in for the ``time`` module used by the renderer.

    Only ``monotonic`` is needed; patching the module reference (rather than
    ``time.monotonic`` itself) keeps the fake clock local to the renderer.
    """

    def __init__(self, values: list[float]) -> None:
        self._values = list(values)

    def monotonic(self) -> float:
        """Return the next scripted timestamp.

        Returns:
            The next value from the script, in order.
        """
        return self._values.pop(0)


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


class TestPopPendingTool:
    """Tests for the shared ``pop_pending_tool`` helper."""

    def test_pops_by_run_id_ignoring_position(self) -> None:
        """A supplied run_id removes that entry, not the FIFO head."""
        pending: deque[tuple[str | None, str, str]] = deque(
            [("run-a", "Bash", "tool_1"), ("run-b", "Bash", "tool_2")]
        )
        entry = pop_pending_tool(pending, "run-b", "Bash")
        assert entry == ("run-b", "Bash", "tool_2")
        assert list(pending) == [("run-a", "Bash", "tool_1")]

    def test_run_id_miss_returns_none_and_keeps_pending(self) -> None:
        """An unmatched run_id must not fall through to the name FIFO."""
        pending: deque[tuple[str | None, str, str]] = deque(
            [("run-a", "Bash", "tool_1")]
        )
        assert pop_pending_tool(pending, "run-zzz", "Bash") is None
        assert list(pending) == [("run-a", "Bash", "tool_1")]

    def test_missing_run_id_falls_back_to_name_fifo(self) -> None:
        """No run_id at all → first pending entry with a matching name."""
        pending: deque[tuple[str | None, str, str]] = deque(
            [(None, "A", "tool_1"), (None, "B", "tool_2"), (None, "A", "tool_3")]
        )
        entry = pop_pending_tool(pending, None, "A")
        assert entry == (None, "A", "tool_1")
        assert list(pending) == [(None, "B", "tool_2"), (None, "A", "tool_3")]

    def test_no_match_on_empty_pending(self) -> None:
        """An empty FIFO yields None on both branches."""
        empty: deque[tuple[str | None, str, str]] = deque()
        assert pop_pending_tool(empty, "run-a", "Bash") is None
        assert pop_pending_tool(empty, None, "Bash") is None


class TestRendererRunIdPairing:
    """Tests for id-keyed renderer pairing on ``tool_run_id`` (R18 / R1)."""

    def test_same_tool_out_of_order_results_pair_by_run_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two starts for the same name, results out of order → right durations."""
        monkeypatch.setattr(_CLOCK_TARGET, _FakeClock([0.0, 1.0, 3.0, 5.0]))
        renderer = StreamEventRenderer()
        renderer.render(
            {
                "type": "tool_use_start",
                "name": "Bash",
                "args": {},
                "tool_run_id": "run-a",
            }
        )
        renderer.render(
            {
                "type": "tool_use_start",
                "name": "Bash",
                "args": {},
                "tool_run_id": "run-b",
            }
        )
        result_b = renderer.render(
            {
                "type": "tool_result",
                "name": "Bash",
                "output": "ok",
                "tool_run_id": "run-b",
            }
        )
        result_a = renderer.render(
            {
                "type": "tool_result",
                "name": "Bash",
                "output": "ok",
                "tool_run_id": "run-a",
            }
        )
        assert isinstance(result_b, ToolResult)
        assert isinstance(result_a, ToolResult)
        # B started at 1.0 and ended at 3.0; A started at 0.0 and ended at 5.0.
        assert result_b.duration_ms == 2000
        assert result_a.duration_ms == 5000
        assert result_b.tool_run_id == "run-b"
        assert result_a.tool_run_id == "run-a"

    def test_tool_start_carries_run_id(self) -> None:
        """``ToolStart`` exposes the event's ``tool_run_id``."""
        renderer = StreamEventRenderer()
        action = renderer.render(
            {
                "type": "tool_use_start",
                "name": "Bash",
                "args": {},
                "tool_run_id": "run-a",
            }
        )
        assert getattr(action, "tool_run_id", "missing") == "run-a"

    def test_run_id_miss_does_not_mispair(self) -> None:
        """An unknown run_id leaves the pending same-name start untouched."""
        renderer = StreamEventRenderer()
        renderer.render(
            {
                "type": "tool_use_start",
                "name": "Bash",
                "args": {},
                "tool_run_id": "run-a",
            }
        )
        miss = renderer.render(
            {
                "type": "tool_result",
                "name": "Bash",
                "output": "ok",
                "tool_run_id": "run-zzz",
            }
        )
        assert isinstance(miss, ToolResult)
        assert miss.duration_ms is None

        # The real result still pairs with the still-pending start.
        matched = renderer.render(
            {
                "type": "tool_result",
                "name": "Bash",
                "output": "ok",
                "tool_run_id": "run-a",
            }
        )
        assert isinstance(matched, ToolResult)
        assert matched.duration_ms is not None

    def test_id_less_result_falls_back_to_name_fifo(self) -> None:
        """A result with no ``tool_run_id`` still pairs by name (CLI/replay shape)."""
        renderer = StreamEventRenderer()
        renderer.render(
            {
                "type": "tool_use_start",
                "name": "Bash",
                "args": {},
                "tool_run_id": "run-a",
            }
        )
        action = renderer.render(
            {"type": "tool_result", "name": "Bash", "output": "ok"}
        )
        assert isinstance(action, ToolResult)
        assert action.duration_ms is not None
        assert action.tool_run_id is None

    def test_cleanup_pending_carries_run_id(self) -> None:
        """Synthesized cancelled results keep their originating ``tool_run_id``."""
        renderer = StreamEventRenderer()
        renderer.render(
            {
                "type": "tool_use_start",
                "name": "Bash",
                "args": {},
                "tool_run_id": "run-a",
            }
        )
        renderer.render({"type": "tool_use_start", "name": "Bash", "args": {}})
        cancelled = renderer.cleanup_pending()
        assert [c.tool_run_id for c in cancelled] == ["run-a", None]
        assert all(c.is_error for c in cancelled)
