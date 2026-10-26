from __future__ import annotations

import argparse

import pytest

from mcp_coder.cli.main import create_parser


class TestICoderSessionArgs:
    """Tests for icoder session continuation arguments."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_icoder_parser_continue_session_flag(self) -> None:
        """icoder --continue-session sets continue_session=True."""
        args = self._parse("icoder", "--continue-session")
        assert args.continue_session is True

    def test_icoder_parser_continue_session_from(self) -> None:
        """icoder --continue-session-from sets the file path."""
        args = self._parse("icoder", "--continue-session-from", "/path/to/file")
        assert args.continue_session_from == "/path/to/file"

    def test_icoder_parser_session_id(self) -> None:
        """icoder --session-id sets the session ID."""
        args = self._parse("icoder", "--session-id", "abc123")
        assert args.session_id == "abc123"

    def test_icoder_parser_default_no_continuation(self) -> None:
        """icoder with no flags has continuation defaults."""
        args = self._parse("icoder")
        assert args.continue_session is False
        assert args.session_id is None

    def test_icoder_parser_timeout_default(self) -> None:
        """icoder with no --timeout flag defaults to 300."""
        args = self._parse("icoder")
        assert args.timeout == 300

    def test_icoder_parser_timeout_custom(self) -> None:
        """icoder --timeout 600 sets timeout=600."""
        args = self._parse("icoder", "--timeout", "600")
        assert args.timeout == 600

    def test_icoder_parser_continue_flags_mutually_exclusive(self) -> None:
        """--continue-session and --continue-session-from are mutually exclusive."""
        with pytest.raises(SystemExit):
            self._parse(
                "icoder", "--continue-session", "--continue-session-from", "/path"
            )
