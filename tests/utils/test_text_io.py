from pathlib import Path

import pytest

from mcp_coder.utils.text_io import write_repo_text


def test_write_mode_writes_lf_only_bytes(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_repo_text(path, "a\nb\n")
    assert path.read_bytes() == b"a\nb\n"


def test_write_mode_normalizes_embedded_crlf(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_repo_text(path, "a\r\nb\r\n")
    assert path.read_bytes() == b"a\nb\n"


def test_append_mode_appends_without_truncating(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_repo_text(path, "a\n")
    write_repo_text(path, "b\n", append=True)
    assert path.read_bytes() == b"a\nb\n"


def test_append_mode_normalizes_embedded_crlf(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    write_repo_text(path, "a\n")
    write_repo_text(path, "c\r\n", append=True)
    appended = path.read_bytes()[len(b"a\n") :]
    assert b"\r" not in appended


@pytest.mark.parametrize("append", [False, True])
@pytest.mark.parametrize("text", ["", "no newline", "a\nb", "a\n\nb\n"])
def test_lf_only_input_is_written_byte_identical(
    tmp_path: Path, append: bool, text: str
) -> None:
    path = tmp_path / "f.txt"
    if append:
        path.write_bytes(b"seed\n")
        write_repo_text(path, text, append=True)
        assert path.read_bytes() == b"seed\n" + text.encode()
    else:
        write_repo_text(path, text)
        assert path.read_bytes() == text.encode()


@pytest.mark.parametrize(
    ("append", "expected"),
    [(True, b"a\r\nb\r\nc\r\nd\r\n"), (False, b"c\r\nd\r\n")],
)
def test_existing_crlf_file_keeps_crlf(
    tmp_path: Path, append: bool, expected: bytes
) -> None:
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
