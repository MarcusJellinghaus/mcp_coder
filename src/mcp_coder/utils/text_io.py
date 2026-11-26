"""Text writes into the target repo under its line-ending policy."""

from pathlib import Path

from .fs import dominant_newline, write_text


def write_repo_text(path: Path, text: str, *, append: bool = False) -> None:
    r"""Write text to path in the existing file's dominant line ending, else LF.

    An existing file with line breaks keeps its dominant ending; a tie, a file
    without line breaks, or a new file gets LF. Applies to appends and
    overwrites. Every line break in ``text`` (CRLF, LF, lone CR) is converted
    to that ending. The text is encoded before the file is opened, so an
    encode error leaves an existing file untouched.
    """
    existing = path.read_bytes() if path.is_file() else None
    write_text(
        path, text, newline=dominant_newline(existing or b"") or "\n", append=append
    )
