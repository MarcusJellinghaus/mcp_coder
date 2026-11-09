"""Tests for mcp_coder.utils.env_placeholders."""

import os

import pytest

from mcp_coder.utils.env_placeholders import resolve_placeholders


class TestResolvePlaceholders:
    """Tests for resolve_placeholders()."""

    def test_resolves_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_A", raising=False)
        result = resolve_placeholders("${MCPC_TEST_PH_A}/src", {"MCPC_TEST_PH_A": "/p"})
        assert result == ("/p/src", [])

    def test_resolves_from_os_environ(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCPC_TEST_PH_A", "/env")
        assert resolve_placeholders("${MCPC_TEST_PH_A}") == ("/env", [])

    def test_multiple_placeholders(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_A", raising=False)
        monkeypatch.delenv("MCPC_TEST_PH_B", raising=False)
        result = resolve_placeholders(
            "${MCPC_TEST_PH_A}:${MCPC_TEST_PH_B}",
            {"MCPC_TEST_PH_A": "1", "MCPC_TEST_PH_B": "2"},
        )
        assert result == ("1:2", [])

    def test_empty_string_unchanged(self) -> None:
        assert resolve_placeholders("") == ("", [])

    def test_plain_text_unchanged(self) -> None:
        assert resolve_placeholders("no placeholders here") == (
            "no placeholders here",
            [],
        )

    def test_env_vars_win_over_os_environ(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCPC_TEST_PH_A", "from_env")
        result = resolve_placeholders("${MCPC_TEST_PH_A}", {"MCPC_TEST_PH_A": "wins"})
        assert result == ("wins", [])

    def test_default_used_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_UNSET", raising=False)
        assert resolve_placeholders("${MCPC_TEST_PH_UNSET:-fallback}") == (
            "fallback",
            [],
        )

    def test_default_ignored_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCPC_TEST_PH_A", "value")
        assert resolve_placeholders("${MCPC_TEST_PH_A:-fallback}") == ("value", [])

    def test_default_ignored_when_set_to_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_A", raising=False)
        result = resolve_placeholders(
            "${MCPC_TEST_PH_A:-fallback}", {"MCPC_TEST_PH_A": ""}
        )
        assert result == ("", [])

    def test_default_not_expanded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_UNSET", raising=False)
        monkeypatch.setenv("MCPC_TEST_PH_X", "expanded")
        # The default stops at the first "}", so the default is "${MCPC_TEST_PH_X"
        # and the trailing "}" is kept as plain text.
        result = resolve_placeholders("${MCPC_TEST_PH_UNSET:-${MCPC_TEST_PH_X}}")
        assert result == ("${MCPC_TEST_PH_X}", [])

    def test_unresolved_stays_literal_and_reported(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_UNSET", raising=False)
        assert resolve_placeholders("x/${MCPC_TEST_PH_UNSET}") == (
            "x/${MCPC_TEST_PH_UNSET}",
            ["MCPC_TEST_PH_UNSET"],
        )

    def test_unresolved_duplicates_reported_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_U1", raising=False)
        monkeypatch.delenv("MCPC_TEST_PH_U2", raising=False)
        value = "${MCPC_TEST_PH_U1}${MCPC_TEST_PH_U2}${MCPC_TEST_PH_U1}"
        assert resolve_placeholders(value) == (
            value,
            ["MCPC_TEST_PH_U1", "MCPC_TEST_PH_U2"],
        )

    def test_case_insensitive_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_CI", raising=False)
        result = resolve_placeholders(
            "${mcpc_test_ph_ci}", {"MCPC_TEST_PH_CI": "1"}, case_insensitive=True
        )
        assert result == ("1", [])

    def test_case_sensitive_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCPC_TEST_PH_CI", raising=False)
        result = resolve_placeholders(
            "${mcpc_test_ph_ci}", {"MCPC_TEST_PH_CI": "1"}, case_insensitive=False
        )
        assert result == ("${mcpc_test_ph_ci}", ["mcpc_test_ph_ci"])

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only casing behaviour")
    def test_windows_os_environ_case_insensitive(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCPC_TEST_PH_CASE", "x")
        assert resolve_placeholders("${Mcpc_Test_Ph_Case}") == ("x", [])
