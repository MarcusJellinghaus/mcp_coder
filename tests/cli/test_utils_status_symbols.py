"""Tests for _get_status_symbols in CLI utils."""

from typing import Any
from unittest.mock import patch

from mcp_coder.cli.utils import _get_status_symbols


class TestGetStatusSymbols:
    def test_returns_dict_with_required_keys(self) -> None:
        result = _get_status_symbols()
        assert "success" in result
        assert "failure" in result
        assert "warning" in result
        assert len(result) == 3

    @patch("mcp_coder.cli.utils.sys")
    def test_windows_uses_ascii(self, mock_sys: Any) -> None:
        mock_sys.platform = "win32"
        result = _get_status_symbols()
        assert result == {"success": "[OK]", "failure": "[NO]", "warning": "[!!]"}

    @patch("mcp_coder.cli.utils.sys")
    def test_unix_uses_unicode(self, mock_sys: Any) -> None:
        mock_sys.platform = "linux"
        result = _get_status_symbols()
        assert result == {"success": "\u2713", "failure": "\u2717", "warning": "\u26a0"}

    @patch("mcp_coder.cli.utils.sys")
    def test_darwin_uses_unicode(self, mock_sys: Any) -> None:
        mock_sys.platform = "darwin"
        result = _get_status_symbols()
        assert result == {"success": "\u2713", "failure": "\u2717", "warning": "\u26a0"}
