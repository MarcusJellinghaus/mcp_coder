"""Comment-preserving write-back of one matcher into a JSONC settings file.

:func:`write_rule` inserts exactly one matcher string into the ``allow`` /
``ask`` / ``deny`` list of a settings file (v1: ``.icoder/settings.local.json``),
preserving comments, order, indentation, encoding and newline style. A JSON
round-trip is deliberately not used — comments must survive.

The module rests on one primitive, :func:`_scan`, which tokenises the text into
``code`` / ``string`` / ``comment`` spans as offsets into the *original* text.
Every locator slices that text; bracket depth is counted over code spans only,
so a bracket inside a string or a comment can never move it. The loader's
``_strip_jsonc`` is reused only as a *parser* (to learn what the file already
contains), never as a locator: it returns a stripped copy without offsets.

After every mutation the text is re-scanned; offsets are never adjusted.
:class:`PersistError` is the only failure type and is raised before anything
is written, so the caller's single ``except OSError`` degrade branch covers
every non-I/O failure as well.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Literal, NamedTuple

from mcp_coder.icoder.permissions.loader import _strip_jsonc

Section = Literal["allow", "ask", "deny"]

_SECTIONS: tuple[Section, ...] = ("allow", "ask", "deny")
_DEPTH = {"{": 1, "[": 1, "}": -1, "]": -1}
_NEW_FILE = "{\n}\n"


class PersistError(OSError):
    """The target cannot be parsed or holds a section this writer refuses to edit.

    Subclasses :class:`OSError` so the caller's existing degrade branch already
    covers it.
    """


class Span(NamedTuple):
    """One token of the JSONC text: ``[start, end)`` offsets into the original."""

    kind: str  # "code" | "string" | "comment"
    start: int
    end: int


def _scan(text: str) -> list[Span]:
    """Tokenise JSONC text into ``code`` / ``string`` / ``comment`` spans.

    String walking honours backslash escapes; both ``//`` (to end of line,
    newline excluded) and ``/* ... */`` comments are recognised. An unterminated
    string or block comment runs to the end of the text.

    Args:
        text: The JSONC source.

    Returns:
        Contiguous, non-overlapping spans covering the whole text in order.
    """
    spans: list[Span] = []
    n = len(text)
    i = code_start = 0

    def flush(end: int) -> None:
        if end > code_start:
            spans.append(Span("code", code_start, end))

    while i < n:
        c = text[i]
        peek = text[i + 1] if i + 1 < n else ""
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            kind, end = "string", min(j + 1, n)
        elif c == "/" and peek == "/":
            j = text.find("\n", i)
            kind, end = "comment", n if j == -1 else j
        elif c == "/" and peek == "*":
            j = text.find("*/", i + 2)
            kind, end = "comment", n if j == -1 else j + 2
        else:
            i += 1
            continue
        flush(i)
        spans.append(Span(kind, i, end))
        i = code_start = end
    flush(n)
    return spans


def _code_view(text: str, spans: list[Span]) -> str:
    """Return ``text`` with every non-code span blanked to spaces (offsets kept)."""
    out = list(text)
    for span in spans:
        if span.kind != "code":
            out[span.start : span.end] = " " * (span.end - span.start)
    return "".join(out)


def _top_level_strings(text: str, spans: list[Span]) -> Iterator[Span]:
    """Yield the string spans sitting directly inside the root object (depth 1)."""
    depth = 0
    for span in spans:
        if span.kind == "code":
            depth += sum(_DEPTH.get(c, 0) for c in text[span.start : span.end])
        elif span.kind == "string" and depth == 1:
            yield span


def _skip_ws(code: str, pos: int) -> int:
    """Return the first offset at or after ``pos`` that is not whitespace."""
    while pos < len(code) and code[pos].isspace():
        pos += 1
    return pos


def _find_section_array(
    text: str, spans: list[Span], section: Section
) -> tuple[int, int] | None:
    """Locate the ``[`` and ``]`` of the top-level ``"<section>": [...]`` list.

    A depth-1 string equal to the section name is the key only when followed
    by ``:`` then ``[`` (comments and whitespace skipped). On any other shape
    the scan continues: ``"defaultMode": "allow"`` legitimately puts a depth-1
    ``"allow"`` string in the text that is a value, not a key.

    Args:
        text: The JSONC source.
        spans: ``_scan(text)``.
        section: The list key to find.

    Returns:
        ``(open_i, close_i)`` offsets of the brackets, or ``None`` if absent.
    """
    code = _code_view(text, spans)
    key = f'"{section}"'
    for span in _top_level_strings(text, spans):
        if text[span.start : span.end] != key:
            continue
        pos = _skip_ws(code, span.end)
        if code[pos : pos + 1] != ":":
            continue
        open_i = _skip_ws(code, pos + 1)
        if code[open_i : open_i + 1] != "[":
            continue
        depth = 0
        for close_i in range(open_i, len(code)):
            depth += _DEPTH.get(code[close_i], 0)
            if depth == 0:
                return open_i, close_i
    return None


def _find_item(
    text: str, spans: list[Span], open_i: int, close_i: int, matcher: str
) -> Span | None:
    """Return the string span inside ``[open_i, close_i]`` whose value is ``matcher``."""
    for span in spans:
        if span.kind != "string" or span.start < open_i or span.end > close_i:
            continue
        try:
            value = json.loads(text[span.start : span.end])
        except ValueError:
            continue
        if value == matcher:
            return span
    return None


def _locate_item(text: str, section: Section, matcher: str) -> Span:
    """Find ``matcher`` inside the top-level ``section`` list.

    Args:
        text: The JSONC source.
        section: The list the matcher is expected in (per the parsed data).
        matcher: The matcher string to find.

    Returns:
        The span of the string literal.

    Raises:
        PersistError: The list or the item cannot be located in the text —
            e.g. a duplicate top-level key, where ``json.loads`` keeps the
            last value but the locator finds the first.
    """
    spans = _scan(text)
    bounds = _find_section_array(text, spans, section)
    if bounds is None:
        raise PersistError(f"cannot locate the {section!r} list to move {matcher!r}")
    item = _find_item(text, spans, *bounds, matcher)
    if item is None:
        raise PersistError(f"cannot locate {matcher!r} inside the {section!r} list")
    return item


def _line_indent(text: str, pos: int) -> str:
    """Return the leading whitespace of the line containing ``pos``."""
    start = text.rfind("\n", 0, pos) + 1
    line = text[start:pos]
    return line[: len(line) - len(line.lstrip())]


def _insert_item(
    text: str, open_i: int, close_i: int, matcher: str, newline: str
) -> str:
    """Insert ``matcher`` immediately after the opening ``[`` at ``open_i``.

    Existing items, their comments and their indentation are never touched.
    A newline-free array stays inline; otherwise the new item takes its own
    line, indented like the first existing item (else the ``[`` line + two
    spaces).

    Args:
        text: The JSONC source.
        open_i: Offset of the list's ``[``.
        close_i: Offset of the list's ``]``.
        matcher: The matcher string to insert.
        newline: LF or CRLF, matching the file.

    Returns:
        The updated text.
    """
    literal = json.dumps(matcher, ensure_ascii=False)
    inner = text[open_i + 1 : close_i]
    has_items = any(
        s.kind == "string" and open_i < s.start < close_i for s in _scan(text)
    )
    head, tail = text[: open_i + 1], text[close_i:]
    if "\n" not in inner:
        lead = inner[: len(inner) - len(inner.lstrip())]
        sep = ", " if has_items else ""
        return f"{head}{lead}{literal}{sep}{inner.lstrip()}{tail}"
    indent = next(
        (
            line[: len(line) - len(line.lstrip())]
            for line in inner.split("\n")[1:]
            if line.strip()
        ),
        _line_indent(text, open_i) + "  ",
    )
    sep = "," if has_items else ""
    return f"{head}{newline}{indent}{literal}{sep}{inner}{tail}"


def _insert_section(
    text: str, spans: list[Span], section: Section, matcher: str, newline: str
) -> str:
    """Add a fresh ``"<section>": [ matcher ]`` block right after the root ``{``.

    Args:
        text: The JSONC source, whose root is an object.
        spans: ``_scan(text)``.
        section: The list key to add.
        matcher: The single item of the new list.
        newline: LF or CRLF, matching the file.

    Returns:
        The updated text.

    Raises:
        PersistError: No root ``{`` is found in code (not reachable after the
            parse guard, kept so a corrupt edit can never be written).
    """
    code = _code_view(text, spans)
    brace_i = code.find("{")
    if brace_i == -1:
        raise PersistError("root object not found")
    # Indent like the first existing key when it starts its own line, else
    # like the ``{`` line plus two spaces (covers the new-file skeleton).
    key_indent = _line_indent(text, brace_i) + "  "
    first_key = next(_top_level_strings(text, spans), None)
    if first_key is not None:
        prefix = text[text.rfind("\n", 0, first_key.start) + 1 : first_key.start]
        if not prefix.strip():
            key_indent = prefix
    literal = json.dumps(matcher, ensure_ascii=False)
    block = (
        f'{newline}{key_indent}"{section}": [{newline}{key_indent}  {literal}'
        f"{newline}{key_indent}]"
    )
    after_brace = _skip_ws(code, brace_i + 1)
    comma = "" if code[after_brace : after_brace + 1] == "}" else ","
    return f"{text[: brace_i + 1]}{block}{comma}{text[brace_i + 1 :]}"


def _remove_item(text: str, span: Span) -> str:
    """Delete the item at ``span`` plus one adjacent comma.

    Adjacency is judged on the code view, so whitespace *and comments* between
    the item and its comma are skipped (and removed with it). The comma after
    the item is preferred, else the one before it. When nothing but whitespace
    remains on the item's line, the whole line goes.

    Args:
        text: The JSONC source.
        span: The string literal to remove.

    Returns:
        The updated text.

    Raises:
        PersistError: No comma is adjacent yet the item is not alone in its
            list — deleting it would leave the file unparseable.
    """
    start, end = span.start, span.end
    code = _code_view(text, _scan(text))
    after = _skip_ws(code, end)
    before = start
    while before > 0 and code[before - 1].isspace():
        before -= 1
    if code[after : after + 1] == ",":
        end = after + 1
    elif code[before - 1 : before] == ",":
        start = before - 1
    elif code[before - 1 : before] != "[" or code[after : after + 1] != "]":
        raise PersistError(f"no comma adjacent to {text[span.start:span.end]}")
    out = text[:start] + text[end:]
    line_start = out.rfind("\n", 0, start) + 1
    line_end = out.find("\n", start)
    line_end = len(out) if line_end == -1 else line_end + 1
    if not out[line_start:line_end].strip():
        out = out[:line_start] + out[line_end:]
    return out


def _read(target: Path) -> tuple[str, str]:
    """Return ``(text, newline)`` for ``target``; an absent file yields a skeleton.

    Reads bytes rather than ``read_text()`` so CRLF survives (universal
    newlines would silently translate it).

    Args:
        target: The settings file.

    Returns:
        The decoded text and its newline style (CRLF if any is present, else LF).

    Raises:
        PersistError: The file is not valid UTF-8.
    """
    try:
        raw = target.read_bytes()
    except FileNotFoundError:
        return _NEW_FILE, "\n"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PersistError(f"{target}: not UTF-8: {exc}") from exc
    return text, ("\r\n" if "\r\n" in text else "\n")


def _parse(text: str, target: Path) -> dict[Section, list[object]]:
    """Parse the file and return its three section lists (absent -> ``[]``).

    Args:
        text: The JSONC source.
        target: The file, for error messages.

    Returns:
        A dict with every key of ``_SECTIONS``.

    Raises:
        PersistError: Unparseable JSONC, a non-object root, or a section
            whose value is not a list.
    """
    try:
        data = json.loads(_strip_jsonc(text))
    except ValueError as exc:
        raise PersistError(f"{target}: cannot parse: {exc}") from exc
    if not isinstance(data, dict):
        raise PersistError(f"{target}: root is not an object")
    sections: dict[Section, list[object]] = {}
    for section in _SECTIONS:
        value = data.get(section, [])
        if not isinstance(value, list):
            raise PersistError(f"{target}: {section!r} is not a list")
        sections[section] = value
    return sections


def _atomic_write(target: Path, text: str) -> None:
    """Write ``text`` via a sibling temp file and ``os.replace``.

    Creates the parent directory. ``newline=""`` keeps the newlines already in
    ``text`` intact on win32. On any failure the temp file is removed before
    the exception propagates.

    Args:
        target: The destination file.
        text: The full new content.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_name, target)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def write_rule(target: Path, matcher: str, section: Section = "allow") -> None:
    """Insert ``matcher`` into the top-level ``section`` list of ``target``.

    Idempotent: a matcher already in ``section`` returns without touching the
    file. A matcher found in one of the other two sections is moved, not
    duplicated. An absent file or an absent key is scaffolded. Comments,
    order, indentation, encoding and newline style are preserved.

    Args:
        target: The JSONC settings file (v1: ``.icoder/settings.local.json``).
        matcher: The matcher string to persist.
        section: Which list receives it.

    Raises:
        PersistError: The file cannot be parsed, its root is not an object, a
            section value is not a list, or the item to move cannot be located
            or removed cleanly. Nothing is written in that case. Plain
            :class:`OSError` propagates from an unwritable target.
    """  # noqa: DOC502 - raised by _read/_parse/_locate_item/_remove_item, part of the contract
    text, newline = _read(target)
    sections = _parse(text, target)
    if matcher in sections[section]:
        return
    for other in _SECTIONS:
        if other != section and matcher in sections[other]:
            text = _remove_item(text, _locate_item(text, other, matcher))
    spans = _scan(text)
    bounds = _find_section_array(text, spans, section)
    if bounds is None:
        text = _insert_section(text, spans, section, matcher, newline)
    else:
        text = _insert_item(text, *bounds, matcher, newline)
    _atomic_write(target, text)
