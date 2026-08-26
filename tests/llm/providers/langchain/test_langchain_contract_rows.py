"""Contract findings merged into ``verify_langchain``'s result rows.

Step 5's :func:`validate` is non-raising, so ``verify`` can report *every*
violation at once. This module pins how those findings land in the result dict:
a finding replaces the naive row entirely — both its ``ok`` and its ``value`` —
so the rendered row names the violation instead of showing a bare ``not set``,
and any ``ok is False`` finding drives ``overall_ok`` to False (and thus exit 1)
while ``ok is None`` warnings stay exit-neutral.

Placed in its own module rather than appended to
``test_langchain_verification.py``: that file is at 537 lines and this coverage
is ~300, the same reasoning steps 7 and 8 used when they split.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify_formatting import (
    _LABEL_MAP,
    _LABEL_WIDTH,
    STATUS_SYMBOLS,
    _format_section,
)
from mcp_coder.llm.providers.langchain._config_diagnostics import ResolvedTarget
from mcp_coder.llm.providers.langchain.verification import (
    _mask_api_key,
    verify_langchain,
)

_PACKAGE = "mcp_coder.llm.providers.langchain"
_VERIFICATION = f"{_PACKAGE}.verification"
_MODELS = f"{_PACKAGE}._models"

# Every variable that can supply a credential or redirect a client, cleared
# before each test so a developer's real environment cannot satisfy — or
# violate — the contract behind the test's back.
_SENSITIVE_VARS = (
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_AD_TOKEN",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "ANTHROPIC_API_KEY",
    "OLLAMA_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_API_BASE",
    "AZURE_OPENAI_ENDPOINT",
    "OLLAMA_HOST",
)

_SDK_DEFAULT_TARGET = ResolvedTarget("https://api.openai.com/v1/", "SDK default", True)

_A_KEY = "sk-abcd1234wxyz5678"


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _SENSITIVE_VARS:
        monkeypatch.delenv(var, raising=False)


def _config(**overrides: str | None) -> dict[str, str | None]:
    """Build a full langchain config dict with *overrides* applied."""
    cfg: dict[str, str | None] = {
        "provider": "langchain",
        "backend": None,
        "model": None,
        "api_key": None,
        "base_url": None,
        "api_version": None,
    }
    cfg.update(overrides)
    return cfg


def _openai_config(**overrides: str | None) -> dict[str, str | None]:
    return _config(backend="openai", model="gpt-4o", **overrides)


def _run_verify(
    config: dict[str, str | None],
    target: ResolvedTarget = _SDK_DEFAULT_TARGET,
) -> dict[str, Any]:
    """Run verify_langchain against *config* with every probe stubbed out."""
    with (
        patch(f"{_VERIFICATION}._load_langchain_config", return_value=config),
        patch(f"{_VERIFICATION}._check_package_installed", return_value=True),
        patch(f"{_VERIFICATION}.resolve_target", return_value=target),
        patch(
            f"{_MODELS}._check_ollama_daemon",
            return_value={"ok": True, "value": "reachable"},
        ),
        patch(
            f"{_MODELS}.check_ollama_tool_capability",
            return_value={"ok": True, "value": "supports tools"},
        ),
    ):
        return verify_langchain()


def _row(result: dict[str, Any], key: str) -> str:
    """Return the rendered LLM PROVIDER DETAILS line for *key*.

    Matching is on the padded label field, so ``api_key`` cannot accidentally
    pick up the ``api_key_override`` row that follows it.
    """
    label = _LABEL_MAP.get(key, key)
    prefix = f"{' ' * 2}{label:<{_LABEL_WIDTH}s} "
    section = _format_section("LLM PROVIDER DETAILS", result, STATUS_SYMBOLS)
    matches = [line for line in section.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, f"expected exactly one {label!r} row, got {matches!r}"
    return matches[0]


# ---------------------------------------------------------------------------
# api_key — the finding branch and the no-finding branch
# ---------------------------------------------------------------------------


class TestApiKeyFindingBranch:
    """Cases 2 and 3: the row must name the violation, not describe absence."""

    @pytest.mark.parametrize("base_url", [None, "https://relay.internal/v1"])
    def test_missing_key_row_carries_the_contract_message(
        self, base_url: str | None
    ) -> None:
        """A custom base_url is no exception — the client still needs credentials."""
        result = _run_verify(_openai_config(base_url=base_url))
        row = result["api_key"]

        assert row["ok"] is False
        assert "api_key" in row["value"]
        assert "OPENAI_API_KEY" in row["value"]
        assert row["value"] not in ("not set", "not set (optional)", "None", None)
        assert result["overall_ok"] is False

    def test_missing_key_row_renders_the_message(self) -> None:
        rendered = _row(_run_verify(_openai_config()), "api_key")

        assert "[ERR]" in rendered
        assert "OPENAI_API_KEY" in rendered
        assert "not set" not in rendered


class TestApiKeyNoFindingBranch:
    """Case 2b: with the contract satisfied, the row shows the masked key."""

    def test_resolved_key_is_masked_and_attributed(self) -> None:
        result = _run_verify(_openai_config(api_key=_A_KEY))
        row = result["api_key"]

        assert row["ok"] is True
        assert row["value"] == _mask_api_key(_A_KEY)
        assert row["source"] == "config.toml"

    def test_env_key_is_masked_and_attributed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env-12345678")
        result = _run_verify(_openai_config())

        assert result["api_key"]["value"] == "sk-f...5678"
        assert result["api_key"]["source"] == "OPENAI_API_KEY env var"


class TestOptionalApiKey:
    """Case 5: the hand-rolled ollama branch is gone, its text preserved."""

    def test_ollama_without_a_key_stays_ok(self) -> None:
        result = _run_verify(_config(backend="ollama", model="llama3"))
        row = result["api_key"]

        assert row["ok"] is True
        assert row["value"] == "not set (optional)"
        assert row["source"] is None

    def test_ollama_row_never_renders_the_literal_none(self) -> None:
        """_mask_api_key(None) would stringify to "None" — the regression guard."""
        rendered = _row(
            _run_verify(_config(backend="ollama", model="llama3")), "api_key"
        )

        assert "[OK]" in rendered
        assert "not set (optional)" in rendered
        assert "None" not in rendered


class TestRequiredApiKeySatisfiedElsewhere:
    """Case 5b: "(optional)" is never claimed for a required credential."""

    def test_azure_key_from_the_sdk_fallback_variable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key-12345678")
        result = _run_verify(
            _openai_config(
                base_url="https://res.openai.azure.com", api_version="2024-02-01"
            )
        )
        row = result["api_key"]

        assert row["ok"] is True
        assert row["value"] == _mask_api_key("azure-key-12345678")
        assert row["source"] == "AZURE_OPENAI_API_KEY env var"
        assert "not set (optional)" not in _row(result, "api_key")

    def test_gemini_key_from_the_sdk_fallback_variable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GOOGLE_API_KEY", "google-key-12345678")
        result = _run_verify(_config(backend="gemini", model="gemini-2.0-flash"))
        row = result["api_key"]

        assert row["ok"] is True
        assert row["value"] == _mask_api_key("google-key-12345678")
        assert row["source"] == "GOOGLE_API_KEY env var"
        assert "not set (optional)" not in _row(result, "api_key")

    def test_gemini_keyless_vertex_carve_out(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "1")
        result = _run_verify(_config(backend="gemini", model="gemini-2.0-flash"))
        row = result["api_key"]

        assert row["ok"] is True
        assert row["value"] == "satisfied via GOOGLE_GENAI_USE_VERTEXAI env var"
        rendered = _row(result, "api_key")
        assert "[OK]" in rendered
        assert "not set (optional)" not in rendered


# ---------------------------------------------------------------------------
# base_url / api_version rows
# ---------------------------------------------------------------------------


class TestAzureBaseUrlRow:
    """Case 1: Azure mode without a resource URL is an error, not a warning."""

    def test_missing_azure_base_url_fails(self) -> None:
        result = _run_verify(_openai_config(api_key=_A_KEY, api_version="2024-02-01"))
        row = result["base_url"]

        assert row["ok"] is False
        assert "api_version" in row["value"]
        assert "AZURE_OPENAI_ENDPOINT" in row["value"]
        assert result["overall_ok"] is False
        assert "[ERR]" in _row(result, "base_url")


class TestIgnoredKeyRows:
    """Case 4: ignored keys warn, and a warning never changes the exit code."""

    def test_gemini_base_url_is_an_exit_neutral_warning(self) -> None:
        result = _run_verify(
            _config(
                backend="gemini",
                model="gemini-2.0-flash",
                api_key=_A_KEY,
                base_url="https://relay.internal/v1",
            )
        )
        row = result["base_url"]

        assert row["ok"] is None
        assert "ignored" in row["value"]
        assert result["overall_ok"] is True
        assert "[WARN]" in _row(result, "base_url")

    def test_gemini_api_version_is_an_exit_neutral_warning(self) -> None:
        result = _run_verify(
            _config(
                backend="gemini",
                model="gemini-2.0-flash",
                api_key=_A_KEY,
                api_version="2024-02-01",
            )
        )
        row = result["api_version"]

        assert row["ok"] is None
        assert "ignored" in row["value"]
        assert result["overall_ok"] is True
        assert "[WARN]" in _row(result, "api_version")


class TestContractLabels:
    """The two new keys need labels or they render as raw dict keys."""

    def test_label_map_entries(self) -> None:
        assert _LABEL_MAP["base_url"] == "Base URL"
        assert _LABEL_MAP["api_version"] == "API version"


# ---------------------------------------------------------------------------
# Reporting every violation, and the unsupported-backend row
# ---------------------------------------------------------------------------


class TestEveryViolationReported:
    """Case 6: the validator is non-raising, so nothing dies on the first."""

    def test_azure_with_nothing_configured_reports_all_three(self) -> None:
        result = _run_verify(_config(backend="openai", api_version="2024-02-01"))

        assert result["model"]["ok"] is False
        assert result["api_key"]["ok"] is False
        assert result["base_url"]["ok"] is False
        assert result["overall_ok"] is False


class TestUnsupportedBackendRow:
    """Case 8: exit 1 must always come with a visible, named cause."""

    def test_typo_backend_row_is_replaced_not_kept(self) -> None:
        result = _run_verify(_config(backend="opnai", model="gpt-4o", api_key=_A_KEY))
        row = result["backend"]

        assert row["ok"] is False
        assert "opnai" in row["value"]
        for name in ("'openai'", "'gemini'", "'anthropic'", "'ollama'"):
            assert name in row["value"]
        assert result["overall_ok"] is False

        rendered = _row(result, "backend")
        assert "[ERR]" in rendered
        assert "[OK]" not in rendered


class TestUnscopedDefaults:
    """Case 8b: "no finding" is not "satisfied" when validate short-circuited."""

    @pytest.mark.parametrize("backend", ["opnai", None])
    def test_model_and_api_key_fall_back_to_a_presence_test(
        self, backend: str | None
    ) -> None:
        result = _run_verify(_config(backend=backend))

        assert result["model"]["ok"] is False
        assert result["api_key"]["ok"] is False
        assert result["api_key"]["value"] == "not set"

    @pytest.mark.parametrize("backend", ["opnai", None])
    def test_no_ok_marker_for_a_field_the_contract_never_checked(
        self, backend: str | None
    ) -> None:
        result = _run_verify(_config(backend=backend))

        model_row = _row(result, "model")
        key_row = _row(result, "api_key")
        assert "[ERR]" in model_row and "[OK]" not in model_row
        assert "[ERR]" in key_row and "[OK]" not in key_row
        assert "(optional)" not in key_row
