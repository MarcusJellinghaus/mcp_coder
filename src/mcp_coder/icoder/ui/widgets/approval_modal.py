"""ApprovalModal — the human decision behind an ``ask``-gated tool call.

A :class:`textual.screen.ModalScreen` showing one pending tool call and its
full arguments, dismissed with the user's typed :class:`ApprovalDecision`
(choices ``1``–``4``, ``Esc`` = deny once) or ``None`` when the user cancels
the whole turn (choice ``5``). The screen only *collects* the choice; the
caller (``ui/stream_view.py``) applies the scope side-effects and resolves
the engine.

Args are rendered by :func:`format_args_full`, not by
``detail_modal._format_args``: that one truncates a single-line value over
120 characters, which is fine for an after-the-fact inspection modal and wrong
for a security decision — the tail of a long command or URL is exactly what
the user must see. Values here are verbatim; long lines wrap and scroll
inside the read-only :class:`textual.widgets.TextArea`, which also makes them
selectable and copyable (``Ctrl+C``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea

from mcp_coder.icoder.permissions.approval import ApprovalDecision

#: Shown above the choices: a "remember" grant is whole-tool, never arg-scoped.
DISCLAIMER_TEMPLATE = (
    "⚠ Remembering allows every future call to {tool} — "
    "with any arguments, not just these."
)


def build_prompt_text(tool_name: str, source: str, persist_target: Path) -> str:
    """Build the fixed prompt block: header, disclaimer and the five choices.

    Args:
        tool_name: The tool awaiting approval.
        source: The layer whose ``ask`` policy parked the call (bare string).
        persist_target: The file choice ``3`` would write the grant to. It is
            shown inline so the write is confirmed before the user commits.

    Returns:
        The multi-line prompt text.
    """
    lines = [
        "Approve tool call?",
        "",
        f"Tool:   {tool_name}",
        f"Source: {source}",
        "",
        DISCLAIMER_TEMPLATE.format(tool=tool_name),
        "",
        "  1  allow once",
        "  2  allow + remember (session)",
        "  3  allow + remember (persist)",
        f'       will add "allow": "{tool_name}" to {persist_target}',
        "  4  deny once",
        "  5  cancel this turn        (Esc = deny once · Ctrl+C = copy)",
    ]
    return "\n".join(lines)


def format_args_full(args: dict[str, object]) -> str:
    """Render a tool's args block with every value verbatim.

    Same block shape as ``detail_modal._format_args`` (``Args:`` header, one
    ``key: value`` entry per argument, multi-line values indented under their
    key) but with no length test and no ellipsis.

    Args:
        args: The tool arguments, possibly empty.

    Returns:
        ``Args: (none)`` when there are no args, else the ``Args:`` block.
    """
    if not args:
        return "Args: (none)"
    lines = ["Args:"]
    for key, value in args.items():
        text = (
            value
            if isinstance(value, str)
            else json.dumps(value, indent=2, default=repr)
        )
        rendered = text.splitlines() or [""]
        if len(rendered) == 1:
            lines.append(f"  {key}: {rendered[0]}")
        else:
            lines.append(f"  {key}:")
            lines.extend(f"    {sub}" for sub in rendered)
    return "\n".join(lines)


class ApprovalModal(ModalScreen[Optional[ApprovalDecision]]):
    """Modal for one pending approval. Dismisses with a decision, or ``None``.

    ``None`` means "cancel this turn": there is no cancel outcome on
    :class:`ApprovalDecision`, so the caller must treat it as a turn abort,
    never as a resolve.
    """

    # #262626 is the hex equivalent of Rich's neutral "grey15".
    DEFAULT_CSS = """
    ApprovalModal {
        align: center middle;
    }
    ApprovalModal .approval-modal-container {
        width: 80%;
        height: 80%;
        background: #262626;
    }
    ApprovalModal #approval-prompt {
        width: 100%;
        height: auto;
        background: #262626;
    }
    ApprovalModal #approval-args {
        width: 100%;
        height: 1fr;
        background: #262626;
    }
    """

    # Digits carry ``priority=True`` so the focused TextArea cannot swallow
    # them. ``ctrl+c`` shadows ICoderApp's ``ctrl+c -> action_noop``. ``escape``
    # needs no priority: screen bindings already win over app bindings — which
    # is why choice ``5`` exists, since Esc here can no longer cancel the turn.
    BINDINGS = [
        Binding("1", "allow_once", "Allow once", priority=True),
        Binding("2", "allow_session", "Session", priority=True),
        Binding("3", "allow_persist", "Persist", priority=True),
        Binding("4", "deny_once", "Deny", priority=True),
        Binding("5", "cancel_turn", "Cancel turn", priority=True),
        Binding("escape", "deny_once", "Deny", show=False),
        Binding("ctrl+c", "copy_selection", "Copy", priority=True),
    ]

    def __init__(
        self,
        *,
        tool_name: str,
        args: dict[str, object],
        source: str,
        persist_target: Path,
    ) -> None:
        """Snapshot the pending call; the body is rendered once in ``compose``.

        Args:
            tool_name: The tool awaiting approval.
            args: The call's arguments, shown verbatim.
            source: The layer whose ``ask`` policy parked the call.
            persist_target: The file choice ``3`` would write the grant to.
        """
        super().__init__()
        self._tool_name = tool_name
        self._args = args
        self._source = source
        self._persist_target = persist_target

    def compose(self) -> ComposeResult:
        """Compose the modal layout.

        Yields:
            A container holding the prompt ``Static`` and the args ``TextArea``.
            ``Static`` cannot scroll or be selected; the ``TextArea`` is what
            makes the full args reachable and copyable.
        """
        yield Container(
            Static(
                build_prompt_text(self._tool_name, self._source, self._persist_target),
                id="approval-prompt",
            ),
            TextArea(format_args_full(self._args), read_only=True, id="approval-args"),
            classes="approval-modal-container",
        )

    def action_allow_once(self) -> None:
        """Choice ``1``: allow this call, remember nothing."""
        self.dismiss(ApprovalDecision("allow", "once"))

    def action_allow_session(self) -> None:
        """Choice ``2``: allow and add a runtime rule for this session."""
        self.dismiss(ApprovalDecision("allow", "session"))

    def action_allow_persist(self) -> None:
        """Choice ``3``: allow and write the grant to ``persist_target``."""
        self.dismiss(ApprovalDecision("allow", "persist"))

    def action_deny_once(self) -> None:
        """Choice ``4`` / ``Esc``: deny this call. ``reason`` stays ``None``."""
        self.dismiss(ApprovalDecision("deny", "once"))

    def action_cancel_turn(self) -> None:
        """Choice ``5``: abandon the turn; the caller cancels, never resolves."""
        self.dismiss(None)

    def action_copy_selection(self) -> None:
        """Copy the args selection to the clipboard (Ctrl+C binding).

        Copies the current selection when non-empty, otherwise the full args
        text. Never dismisses.
        """
        try:
            text_area = self.query_one(TextArea)
        except NoMatches:
            return
        selected = text_area.selected_text
        self.app.copy_to_clipboard(selected if selected else text_area.text)
