"""LF-only text writes for files that may end up in a git commit."""

from pathlib import Path


def write_lf_text(path: Path, text: str, *, append: bool = False) -> None:
    """Write text to path with LF-only line endings, never CRLF.

    Normalizes embedded "\\r\\n" to "\\n"; a lone "\\r" is left untouched.
    """
    normalized = text.replace("\r\n", "\n")
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        handle.write(normalized)
