"""OutputLog widget — scrollable output area for conversation display.

Two parallel line stores back this widget:

- ``recorded_lines`` — **append history**. Every ``append_text`` /
  ``append_unit`` / ``extend_open_unit`` call grows it and it is NEVER
  rewound. It survives tier toggles and ``rebuild()``. Emission-semantics
  assertions ("was this text appended?") belong here.
- ``rendered_lines`` — **current screen state**. Reflects what is visible
  right now and is recomputed wholesale on every ``rebuild()`` (e.g. after a
  tier toggle in step 6). Screen-state assertions ("what is visible after a
  re-render?") belong here.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Literal

from rich.console import ConsoleRenderable, RichCast
from rich.text import Text
from textual.widgets import RichLog

from mcp_coder.llm.formatting.render_actions import ToolStart
from mcp_coder.llm.formatting.stream_renderer import (
    format_tool_compressed,
    format_tool_oneline,
    format_tool_start,
)


@dataclass(frozen=True)
class ContentUnit:
    """A clickable unit of output (one tool, user input, or assistant turn).

    Frozen: fields are set at creation and never mutated. Mutations go
    through :meth:`OutputLog.update_unit_and_rerender`, which builds a
    replacement via :func:`dataclasses.replace`.
    """

    id: str
    kind: Literal["tool", "user_input", "assistant_turn"]
    timestamp: datetime
    full_text: str = ""
    # tool-only (None / empty defaults for non-tool kinds):
    tool_name: str | None = None
    args: dict[str, object] | None = None
    output: str | None = None  # FULL untruncated output (modal / tier 3)
    output_lines: tuple[str, ...] = ()  # pre-rendered, truncated body (tier 2)
    total_lines: int = 0  # total line count (drives footer)
    truncated: bool = False  # whether head/tail truncation kicked in
    duration_ms: int | None = None
    is_error: bool = False
    # always None in v1 — reserved for v2 nesting per issue #629 Decision
    parent_id: str | None = None


class OutputLog(RichLog):
    """Scrollable output area for conversation display.

    See the module docstring for the ``recorded_lines`` (append history)
    vs ``rendered_lines`` (current screen state) distinction.
    """

    def __init__(
        self,
        *,
        mirror: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with internal line buffer for testability.

        Args:
            mirror: Optional one-arg callback invoked with the string that
                was written to the widget; used to mirror visible output to
                an external sink (e.g. a plain-text chat log).
            **kwargs: Keyword args passed through to RichLog.
        """
        # NOTE: ``max_lines`` MUST remain None. RichLog eviction would shift
        # buffer indices and invalidate the ``_ranges`` registry below.
        super().__init__(wrap=True, **kwargs)
        self._recorded: list[str] = []
        self._mirror = mirror
        # Registry data layer (sidecar to the RichLog buffer).
        self._units: dict[str, ContentUnit] = {}  # insertion-ordered
        self._script: list[tuple[str, str | None]] = []  # (unit_id, line|None)
        self._ranges: list[tuple[int, int, str]] = []  # (start, end, unit_id)
        self._screen_lines: list[str] = []  # current screen state
        # Global default tier and per-unit overrides. ``set_tool_display_default``
        # (the /display hard reset) updates the default AND wipes the overrides;
        # ``toggle_unit_tier`` populates the overrides. clear_state() wipes them.
        self._tool_display_default: Literal["oneline", "compressed"] = "compressed"
        self._tool_tier_overrides: dict[str, Literal["oneline", "compressed"]] = {}

    def clear_state(self) -> None:
        """Wipe all registry state and the recorded-line history.

        Clears ``_recorded``, ``_units``, ``_script``, ``_ranges``,
        ``_screen_lines`` and ``_tool_tier_overrides``. RichLog's own buffer
        wipe (``clear()``) is separate and is called first by the app.
        """
        self._recorded.clear()
        self._units.clear()
        self._script.clear()
        self._ranges.clear()
        self._screen_lines.clear()
        self._tool_tier_overrides.clear()

    @property
    def recorded_lines(self) -> list[str]:
        """Return recorded output lines (append history; survives rebuilds).

        Returns:
            Copy of all appended lines.
        """
        return list(self._recorded)

    @property
    def rendered_lines(self) -> list[str]:
        """Return the current screen state (reflects toggles/rebuilds).

        Returns:
            Copy of the logical lines currently displayed (one entry per
            written line, no wrap expansion).
        """
        return list(self._screen_lines)

    def write(  # type: ignore[override]  # pylint: disable=arguments-differ
        self,
        content: RichCast | ConsoleRenderable | str | object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Write content and record a text representation for testability.

        Overrides RichLog.write() to also track non-string renderables
        (e.g. Markdown objects) in _recorded.

        Args:
            content: Rich renderable, string, or other object to display.
            *args: Positional args passed through to RichLog.write().
            **kwargs: Keyword args passed through to RichLog.write().
        """
        if isinstance(content, str):
            # Plain strings are NOT recorded by write(); use append_text() for recorded text.
            if self._mirror is not None:
                self._mirror(content)
        elif isinstance(content, Text):
            # Text objects are recorded via append_text, skip here
            pass
        else:
            # Rich renderables (e.g. Markdown): record the markup text
            markup = getattr(content, "markup", None)
            recorded = markup if markup is not None else str(content)
            self._recorded.append(recorded)
            if self._mirror is not None:
                self._mirror(recorded)
        super().write(content, *args, **kwargs)

    def append_text(self, text: str, style: str | None = None) -> None:
        """Write text to the output log, optionally styled.

        Untouched by the registry layer: writes only to ``_recorded`` and
        the RichLog buffer. Banners, spacers, dividers and markers use this.

        Args:
            text: Content to display.
            style: Optional Rich style string.
        """
        self._recorded.append(text)
        if self._mirror is not None:
            self._mirror(text)
        if style:
            super().write(Text(text, style=style))
        else:
            super().write(text)

    def append_unit(
        self, unit: ContentUnit, lines: list[str], style: str | None = None
    ) -> None:
        """Register a clickable content unit and write its lines.

        Tools and user inputs are atomic: their lines are written now and a
        single ``(unit.id, None)`` script entry lets ``rebuild()`` re-derive
        them. Assistant turns register the unit only — their lines arrive
        later via :meth:`extend_open_unit`.

        Args:
            unit: The content unit to register.
            lines: Pre-rendered logical lines to write (ignored for
                ``assistant_turn`` kind).
            style: Optional Rich style applied to each written line.
        """
        self._units[unit.id] = unit
        if unit.kind == "assistant_turn":
            return
        self._write_unit_atomic(unit, lines, style)

    def _write_unit_atomic(
        self, unit: ContentUnit, lines: list[str], style: str | None
    ) -> None:
        """Write ``lines`` as one atomic unit, tracking buffer span.

        Measures the RichLog buffer (``self.lines``) before and after the
        writes so the stored ``(start, end)`` range spans wrapped buffer
        lines, not logical lines.
        """
        buffer_start = len(self.lines)
        for line in lines:
            self._recorded.append(line)
            self._screen_lines.append(line)
            if style:
                super().write(Text(line, style=style))
            else:
                super().write(line)
        buffer_end = len(self.lines)
        self._script.append((unit.id, None))
        self._ranges.append((buffer_start, buffer_end, unit.id))

    def extend_open_unit(
        self, unit_id: str, lines: list[str], style: str | None = None
    ) -> None:
        """Append streamed lines to an open (non-tool) unit.

        Each line gets its own script entry and its own buffer range so
        interleaving with atomic tool units is preserved.

        Args:
            unit_id: The id of a previously registered unit.
            lines: Logical lines to append.
            style: Optional Rich style applied to each written line.

        Raises:
            ValueError: If the target unit is a tool — tools never extend;
                mutations land via :meth:`update_unit_and_rerender`.
        """
        if self._units[unit_id].kind == "tool":
            raise ValueError(
                "tool units cannot be extended; use update_unit_and_rerender"
            )
        for line in lines:
            buffer_start = len(self.lines)
            self._recorded.append(line)
            self._screen_lines.append(line)
            if style:
                super().write(Text(line, style=style))
            else:
                super().write(line)
            buffer_end = len(self.lines)
            self._script.append((unit_id, line))
            self._ranges.append((buffer_start, buffer_end, unit_id))

    def finalize_open_unit(self, unit_id: str) -> None:
        """Mark an open unit as finished.

        No-op in this step. A unit's "openness" is implicit; this exists as
        a clarity marker and a hook for future state.

        Args:
            unit_id: The id of the unit to finalize.
        """

    def update_unit_and_rerender(self, unit_id: str, **fields: object) -> ContentUnit:
        """Replace fields on a unit and rebuild the screen.

        Args:
            unit_id: The id of the unit to update.
            **fields: Field overrides forwarded to :func:`dataclasses.replace`.

        Returns:
            The new (replaced) unit.
        """
        # mypy cannot narrow **dict[str, object] to the typed dataclass fields.
        new_unit = dataclasses.replace(self._units[unit_id], **fields)  # type: ignore[arg-type]
        self._units[unit_id] = new_unit
        self.rebuild()
        return new_unit

    def unit_at_line(self, line: int) -> ContentUnit | None:
        """Return the unit whose buffer range contains ``line``.

        Ranges are disjoint by construction, so the first containing range
        wins.

        Args:
            line: A buffer-line index (over ``RichLog.lines``).

        Returns:
            The matching unit, or ``None`` when no range contains ``line``.
        """
        for start, end, uid in self._ranges:
            if start <= line < end:
                return self._units[uid]
        return None

    def last_unit(self) -> ContentUnit | None:
        """Return the most recently registered unit (insertion order).

        Returns:
            The last unit, or ``None`` when no units are registered.
        """
        if not self._units:
            return None
        return next(reversed(self._units.values()))

    def effective_tier(self, unit_id: str) -> Literal["oneline", "compressed"]:
        """Return the tier in effect for ``unit_id``.

        An explicit per-unit override (set by :meth:`toggle_unit_tier`) wins;
        otherwise the global ``_tool_display_default`` applies.

        Args:
            unit_id: The id of the unit to resolve.

        Returns:
            The effective tier (``"oneline"`` or ``"compressed"``).
        """
        return self._tool_tier_overrides.get(unit_id, self._tool_display_default)

    def toggle_unit_tier(self, unit_id: str) -> Literal["oneline", "compressed"]:
        """Flip a tool unit's tier and re-render.

        Args:
            unit_id: The id of the tool unit to toggle.

        Returns:
            The new effective tier after the flip.

        Raises:
            ValueError: If the unit is not a tool — only tools toggle.
        """
        unit = self._units[unit_id]
        if unit.kind != "tool":
            raise ValueError(f"only tool units can toggle tier; got {unit.kind!r}")
        new_tier: Literal["oneline", "compressed"] = (
            "oneline" if self.effective_tier(unit_id) == "compressed" else "compressed"
        )
        self._tool_tier_overrides[unit_id] = new_tier
        self.rebuild()
        return new_tier

    def set_tool_display_default(self, tier: Literal["oneline", "compressed"]) -> None:
        """Set the global default tier and wipe all per-unit overrides.

        This is the ``/display`` hard reset: every tool reverts to the new
        default, discarding any individual toggles.

        Args:
            tier: The new global default tier.
        """
        self._tool_display_default = tier
        self._tool_tier_overrides.clear()
        self.rebuild()

    def on_resize(self, event: object) -> None:
        """Re-render on resize so wrap-derived ranges stay valid.

        Idempotent: the script and units are unchanged, so running it twice
        is safe.

        Args:
            event: The Textual ``Resize`` event (unused).
        """
        self.rebuild()

    def rebuild(self) -> None:
        """Re-render the screen from the registry script.

        Walks ``_script`` and rewrites the RichLog buffer, recomputing
        ``_screen_lines`` and ``_ranges``. ``_recorded`` is untouched.
        """
        super().clear()
        self._screen_lines = []
        self._ranges = []
        for unit_id, line in self._script:
            start_idx = len(self.lines)
            if line is None:
                unit = self._units[unit_id]
                for rln in self._render_unit_atomic(unit):
                    super().write(rln)
                    self._screen_lines.append(rln)
            else:
                super().write(line)
                self._screen_lines.append(line)
            end_idx = len(self.lines)
            if end_idx > start_idx:
                self._ranges.append((start_idx, end_idx, unit_id))

    def _render_unit_atomic(self, unit: ContentUnit) -> list[str]:
        """Render an atomic unit (tool / user_input) to logical lines.

        Tools dispatch on their effective tier: ``oneline`` collapses the
        invocation to a single tier-1 summary; ``compressed`` renders the
        tier-2 start header always, plus the body + footer only once a
        result has arrived (``output_lines`` non-empty).

        Args:
            unit: The unit to render.

        Returns:
            The logical lines for the unit (empty for ``assistant_turn``,
            which is never reached via an atomic script entry).
        """
        if unit.kind == "tool":
            if self.effective_tier(unit.id) == "oneline":
                return [
                    format_tool_oneline(
                        name=unit.tool_name or "",
                        args=unit.args or {},
                        duration_ms=unit.duration_ms,
                        is_error=unit.is_error,
                    )
                ]
            lines = format_tool_start(
                ToolStart(
                    display_name=unit.tool_name or "",
                    raw_name="",
                    args=unit.args or {},
                )
            )
            if unit.output_lines:
                lines = lines + format_tool_compressed(
                    name=unit.tool_name or "",
                    args=unit.args or {},
                    output_lines=unit.output_lines,
                    total_lines=unit.total_lines,
                    truncated=unit.truncated,
                    duration_ms=unit.duration_ms,
                    is_error=unit.is_error,
                )
            return lines
        if unit.kind == "user_input":
            return [f"> {unit.full_text}"]
        return []
