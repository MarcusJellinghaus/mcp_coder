"""DetailModal — tier-3 inspection modal for a single ContentUnit.

A :class:`textual.screen.ModalScreen` wrapping a read-only
:class:`textual.widgets.TextArea`. It supports text selection, scrolling
and clipboard copy. Closes on ``Escape`` / ``Enter``; ``Ctrl+C`` overrides
the app-level no-op binding (``priority=True``) to copy the selection.

The modal snapshots its :class:`ContentUnit` at construction time —
:func:`build_detail_text` is rendered once and never live-updates if the
underlying unit changes (Decision: snapshot, not live).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import TextArea

from mcp_coder.llm.formatting.stream_renderer import (
    _render_tool_output,
    _render_value_full,
)

if TYPE_CHECKING:
    # Runtime import would form a cycle: output_log.on_click imports this
    # module to push the modal. ContentUnit is only used as an annotation.
    from mcp_coder.icoder.ui.widgets.output_log import ContentUnit

# A plain horizontal divider above the footer. No box-drawing characters
# (``│ ┌ └ ├``) appear anywhere in the modal body — only this ``─`` line.
_DIVIDER = "─" * 39
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def _format_args(args: dict[str, object] | None) -> str:
    """Render a tool's args block. Multi-line values are indented.

    Args:
        args: The tool arguments, or ``None``/empty.

    Returns:
        ``Args: (none)`` when there are no args, else an ``Args:`` header
        followed by one indented ``key: value`` entry per argument.
    """
    if not args:
        return "Args: (none)"
    lines = ["Args:"]
    for key, value in args.items():
        rendered = _render_value_full(value)
        if len(rendered) == 1:
            lines.append(f"  {key}: {rendered[0]}")
        else:
            lines.append(f"  {key}:")
            for sub in rendered:
                lines.append(f"    {sub}")
    return "\n".join(lines)


def _build_tool_text(unit: ContentUnit) -> str:
    """Build the modal body for a tool unit.

    Returns:
        Plain-text modal body for the tool unit.
    """
    header = f"Tool: {unit.tool_name or ''}"
    args_block = _format_args(unit.args)
    output_lines, total, _truncated = _render_tool_output(unit.output or "", full=True)
    if output_lines:
        output_block = "Output:\n" + "\n".join(output_lines)
    else:
        output_block = "Output: (none)"
    status = "error" if unit.is_error else "done"
    dur = f"{unit.duration_ms}ms" if unit.duration_ms is not None else "—"
    footer = (
        f"Status: {status} | Duration: {dur} | {total} lines | "
        f"{unit.timestamp:{_TIMESTAMP_FORMAT}}"
    )
    body = "\n\n".join([header, args_block, output_block])
    return f"{body}\n\n{_DIVIDER}\n{footer}"


def _build_simple_text(unit: ContentUnit, header: str, kind_label: str) -> str:
    """Build the modal body for a non-tool (user_input / assistant_turn) unit.

    Returns:
        Plain-text modal body for the non-tool unit.
    """
    line_count = len(unit.full_text.splitlines())
    footer = (
        f"Kind: {kind_label} | {line_count} lines | "
        f"{unit.timestamp:{_TIMESTAMP_FORMAT}}"
    )
    body = "\n\n".join([header, unit.full_text])
    return f"{body}\n\n{_DIVIDER}\n{footer}"


def build_detail_text(unit: ContentUnit) -> str:
    """Plain-text rendering for the modal body. No box characters.

    Args:
        unit: The content unit to render.

    Returns:
        A plain-text body switching on ``unit.kind``: tool units render a
        header / args / output / footer layout; user_input and
        assistant_turn units render a header / text / footer layout.
    """
    if unit.kind == "tool":
        return _build_tool_text(unit)
    if unit.kind == "user_input":
        return _build_simple_text(unit, "User input", "user_input")
    return _build_simple_text(unit, "Assistant turn", "assistant_turn")


class DetailModal(ModalScreen[None]):
    """Read-only modal for tier-3 inspection of any ``ContentUnit``."""

    # #262626 is the hex equivalent of Rich's neutral "grey15".
    DEFAULT_CSS = """
    DetailModal {
        align: center middle;
    }
    DetailModal .detail-modal-container {
        width: 80%;
        height: 80%;
        background: #262626;
    }
    DetailModal .detail-modal-textarea {
        width: 100%;
        height: 100%;
        background: #262626;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("enter", "dismiss", "Close", priority=True),
        Binding("ctrl+c", "copy_selection", "Copy", priority=True),
    ]

    def __init__(self, unit: ContentUnit) -> None:
        """Snapshot ``unit`` and pre-render its modal body.

        Args:
            unit: The content unit to display. Captured at construction;
                the modal does not live-update if the unit later changes.
        """
        super().__init__()
        self._unit = unit
        self._text = build_detail_text(unit)

    def compose(self) -> ComposeResult:
        """Compose the modal layout.

        Yields:
            A container holding a single read-only ``TextArea``.
        """
        yield Container(
            TextArea(
                self._text,
                read_only=True,
                classes="detail-modal-textarea",
            ),
            classes="detail-modal-container",
        )

    def action_copy_selection(self) -> None:
        """Copy the TextArea selection to the clipboard (Ctrl+C binding).

        Copies the current selection when non-empty, otherwise the full
        body text.
        """
        try:
            text_area = self.query_one(TextArea)
        except NoMatches:
            return
        selected = text_area.selected_text
        self.app.copy_to_clipboard(selected if selected else text_area.text)
