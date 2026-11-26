# Step 3 — `write_repo_text` follows the aligned line-ending policy

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly. TDD: update and add the tests first, then change `write_repo_text`. Run `run_format_code`, then pylint, pytest (`-n auto`, unit markers from CLAUDE.md), mypy, ruff, lint-imports, tach and vulture via the MCP tools. All must pass. This step is one commit.

## WHERE

- `src/mcp_coder/utils/text_io.py`
- `tests/utils/test_text_io.py`
- `tests/cli/commands/test_init_file_access.py`

## WHAT

### Tests first — `tests/utils/test_text_io.py`

- **Delete** `test_open_called_with_newline_lf`. It spies on `Path.open` and fails with `KeyError` because `fs.write_text` passes no `newline`. Its purpose is covered by `test_write_mode_normalizes_embedded_crlf`. Also remove the now-unused `from typing import Any`.
- Keep all other existing tests unchanged. They write new files or LF files and stay green.
- Add:

```python
@pytest.mark.parametrize(
    ("append", "expected"),
    [(True, b"a\r\nb\r\nc\r\nd\r\n"), (False, b"c\r\nd\r\n")],
)
def test_existing_crlf_file_keeps_crlf(tmp_path: Path, append: bool, expected: bytes) -> None:
    path = tmp_path / "f.txt"
    path.write_bytes(b"a\r\nb\r\n")
    write_repo_text(path, "c\nd\n", append=append)
    assert path.read_bytes() == expected


def test_lone_cr_is_converted(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_repo_text(path, "a\rb\n")
    assert path.read_bytes() == b"a\nb\n"


def test_encode_error_leaves_existing_bytes_untouched(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    path.write_bytes(b"keep\r\n")
    with pytest.raises(UnicodeEncodeError):
        write_repo_text(path, "\ud800")
    assert path.read_bytes() == b"keep\r\n"
```

New files are already covered as LF by `test_write_mode_writes_lf_only_bytes`, so no extra test is needed for that case.

### Tests first — `tests/cli/commands/test_init_file_access.py`

Rename `test_crlf_bom_no_trailing_newline_appends_lf` → `test_crlf_bom_no_trailing_newline_appends_crlf`. The seed `b"\xef\xbb\xbf# mine\r\nread-only /docs/"` has one CRLF and no LF, so its dominant ending is CRLF:
- Docstring: `"""Existing bytes are kept; the appended rules start on a new line in the file's CRLF ending."""`
- Assertions:
  - `raw.startswith(original + b"\r\n")`
  - `b"\n" not in raw[len(original):].replace(b"\r\n", b"")`
- Keep the existing `validate_access_rules` and `_rule_lines` assertions.

### Implementation — `src/mcp_coder/utils/text_io.py`

```python
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
    write_text(path, text, newline=dominant_newline(existing or b"") or "\n", append=append)
```

## HOW

- Use a relative import `from .fs import ...` (same package, `mcp_coder.utils`).
- The callers stay unchanged: they already catch `OSError`, which also covers a failing `read_bytes()`.

## ALGORITHM

```
existing = bytes of path if it is a file, else None
newline  = dominant_newline(existing or b"")   # None on tie / no breaks / empty
newline  = newline or "\n"                     # caller default: LF
write_text(path, text, newline=newline, append=append)   # normalise, encode, write bytes
```

## DATA

Returns `None`. Raises `OSError` (read or write failure) or `UnicodeEncodeError`.

## Commit message

`feat(utils): write_repo_text keeps an existing file's dominant line ending`
