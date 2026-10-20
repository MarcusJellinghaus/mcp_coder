from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.text_io import write_lf_text


def test_write_mode_writes_lf_only_bytes(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_lf_text(path, "a\nb\n")
    assert path.read_bytes() == b"a\nb\n"


def test_write_mode_normalizes_embedded_crlf(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_lf_text(path, "a\r\nb\r\n")
    assert path.read_bytes() == b"a\nb\n"


def test_append_mode_appends_without_truncating(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_lf_text(path, "a\n")
    write_lf_text(path, "b\n", append=True)
    assert path.read_bytes() == b"a\nb\n"


def test_append_mode_normalizes_embedded_crlf(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_lf_text(path, "a\n")
    write_lf_text(path, "c\r\n", append=True)
    appended = path.read_bytes()[len(b"a\n") :]
    assert b"\r" not in appended


def test_open_called_with_newline_lf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "f.txt"
    original_open = Path.open
    captured: dict[str, object] = {}

    def spy(self: Path, *args: Any, **kwargs: Any) -> object:
        captured.update(kwargs)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy)
    write_lf_text(path, "x\n")
    assert captured["newline"] == "\n"


@pytest.mark.parametrize("append", [False, True])
@pytest.mark.parametrize("text", ["", "no newline", "a\nb", "a\n\nb\n"])
def test_lf_only_input_is_written_byte_identical(
    tmp_path: Path, append: bool, text: str
) -> None:
    path = tmp_path / "f.txt"
    if append:
        path.write_bytes(b"seed\n")
        write_lf_text(path, text, append=True)
        assert path.read_bytes() == b"seed\n" + text.encode()
    else:
        write_lf_text(path, text)
        assert path.read_bytes() == text.encode()
