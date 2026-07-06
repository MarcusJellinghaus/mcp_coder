"""Tests for the _collect_install_hints helper."""

from typing import Any

from mcp_coder.cli.commands.verify_exit_code import _collect_install_hints


class TestCollectInstallHints:
    """Tests for _collect_install_hints helper."""

    def test_collects_hints_from_failed_entries(self) -> None:
        """Collects install_hint values from entries with ok=False."""
        result: dict[str, Any] = {
            "pkg_a": {"ok": False, "value": "missing", "install_hint": "pip install a"},
            "pkg_b": {"ok": False, "value": "missing", "install_hint": "pip install b"},
            "overall_ok": False,
        }
        hints = _collect_install_hints(result)
        assert hints == ["pip install a", "pip install b"]

    def test_skips_entries_without_hint(self) -> None:
        """Entries with ok=False but no install_hint key are skipped."""
        result: dict[str, Any] = {
            "pkg_a": {"ok": False, "value": "missing"},
            "overall_ok": False,
        }
        hints = _collect_install_hints(result)
        assert hints == []

    def test_skips_ok_entries(self) -> None:
        """Entries with ok=True are skipped even if install_hint is present."""
        result: dict[str, Any] = {
            "pkg_a": {
                "ok": True,
                "value": "installed",
                "install_hint": "pip install a",
            },
            "overall_ok": True,
        }
        hints = _collect_install_hints(result)
        assert hints == []

    def test_skips_non_dict_entries(self) -> None:
        """Non-dict entries (like overall_ok bool) are skipped."""
        result: dict[str, Any] = {
            "overall_ok": False,
        }
        hints = _collect_install_hints(result)
        assert hints == []
