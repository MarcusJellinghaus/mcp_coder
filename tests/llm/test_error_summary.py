"""Tests for exception summary helpers."""

import pytest

from mcp_coder.llm.error_summary import comment_safe, summarize_exception
from mcp_coder.utils.subprocess_runner import CalledProcessError


class TestSummarizeException:
    """Tests for summarize_exception()."""

    def test_generic_exception(self) -> None:
        """A generic exception renders as "Type: message"."""
        assert summarize_exception(RuntimeError("boom")) == "RuntimeError: boom"

    def test_called_process_error_uses_stderr(self) -> None:
        """CalledProcessError renders its stderr, the real cause."""
        exc = CalledProcessError(1, "claude", stderr="529 Overloaded")
        assert summarize_exception(exc) == "CalledProcessError: 529 Overloaded"

    def test_called_process_error_decodes_bytes_stderr(self) -> None:
        """Bytes stderr is decoded."""
        exc = CalledProcessError(1, "claude", stderr=b"529 Overloaded\n")
        assert summarize_exception(exc) == "CalledProcessError: 529 Overloaded"

    @pytest.mark.parametrize("stderr", [None, "  ", "Stream file: /x/y.log"])
    def test_called_process_error_falls_back_without_stderr(
        self, stderr: str | None
    ) -> None:
        """Empty or stream-file-only stderr falls back to str(exc)."""
        exc = CalledProcessError(1, "claude", stderr=stderr)
        assert summarize_exception(exc) == f"CalledProcessError: {exc}"

    def test_keeps_stream_file_suffix(self) -> None:
        """The console summary keeps the full text, stream-file path included."""
        exc = CalledProcessError(1, "copilot", stderr="err\nStream file: /x/y.log")
        assert (
            summarize_exception(exc) == "CalledProcessError: err\nStream file: /x/y.log"
        )


class TestCommentSafe:
    """Tests for comment_safe()."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("CLI failed with code 1. Stream file: /p", "CLI failed with code 1."),
            ("msg Stream file: None", "msg"),
            ("err\nStream file: /p", "err"),
        ],
    )
    def test_strips_stream_file_suffix(self, text: str, expected: str) -> None:
        """Each stream-file suffix shape is removed."""
        assert comment_safe(text) == expected

    def test_collapses_line_breaks(self) -> None:
        """Line breaks and whitespace runs collapse to single spaces."""
        assert comment_safe("line1\r\nline2\n\nline3") == "line1 line2 line3"

    def test_caps_long_text(self) -> None:
        """Long text is capped at the limit and ends with an ellipsis."""
        result = comment_safe("x" * 1000)
        assert len(result) == 300
        assert result.endswith("…")

    def test_short_text_unchanged(self) -> None:
        """Short single-line text is returned unchanged."""
        assert comment_safe("RuntimeError: boom") == "RuntimeError: boom"
