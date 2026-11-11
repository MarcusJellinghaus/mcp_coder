"""Per-section renderer and section builder for the verify command.

Imports from verify_formatting only; verify_formatting never imports this module.
"""

import logging
import textwrap
from collections.abc import Iterable, Sequence

from .verify_formatting import (
    Line,
    Row,
    _format_row,
    _format_row_prefix,
    _pad,
    _section_label_width,
)

logger = logging.getLogger(__name__)


def _render_rows(lines: Sequence[Line]) -> list[str]:
    """Render one section's lines with a single, section-wide label width.

    Args:
        lines: The section's lines; ``str`` items pass through unchanged.

    Returns:
        One entry per output line, without trailing newlines. ``wrap=True``
        rows may produce several lines, wrapped at 80 columns with
        continuation lines starting at the value column.
    """
    width = _section_label_width(lines)
    out: list[str] = []
    for item in lines:
        if isinstance(item, str):
            out.append(item)
            continue
        prefix = _format_row_prefix(
            item.label, item.marker, indent=item.indent, label_width=width
        )
        if item.wrap:
            out.extend(
                textwrap.wrap(
                    item.value,
                    width=80,
                    initial_indent=prefix,
                    subsequent_indent=" " * len(prefix),
                )
            )
        else:
            out.append((prefix + item.value).rstrip())
    return out


class SectionBuilder:
    """Collect a section's lines and print it once it is closed.

    The header prints on ``open``; rows are buffered until ``close`` (or the
    next ``open``) so the whole section shares one label width. Writes use
    ``print`` at call time, so redirected ``sys.stdout`` is honoured.
    """

    def __init__(self) -> None:
        self._lines: list[Line] | None = None

    def open(self, title: str) -> None:
        """Close any open section, print ``title``'s header, start buffering."""
        self.close()
        print(_pad(title))
        self._lines = []

    def add(self, *lines: Line) -> None:
        """Buffer lines in the open section, or print them when none is open."""
        if self._lines is not None:
            self._lines.extend(lines)
            return
        for item in lines:
            if isinstance(item, Row):
                print(
                    _format_row(item.label, item.marker, item.value, indent=item.indent)
                )
            else:
                print(item)

    def close(self) -> None:
        """Render and print the open section; no-op when none is open."""
        if self._lines is None:
            return
        lines, self._lines = self._lines, None
        for line in _render_rows(lines):
            print(line)

    def section(self, title: str, lines: Iterable[Line]) -> None:
        """Open, fill and close a whole section in one call."""
        self.open(title)
        self.add(*lines)
        self.close()

    def __enter__(self) -> "SectionBuilder":
        """Return the builder itself."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *_rest: object) -> None:
        """Flush the open section; never suppress an exception in flight."""
        if exc_type is None:
            self.close()
            return
        try:
            self.close()
        except Exception:  # pylint: disable=broad-exception-caught
            # The exception already propagating is the one worth reporting.
            logger.debug("could not flush verify section", exc_info=True)
