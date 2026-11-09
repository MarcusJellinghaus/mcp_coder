"""Tests for check_provider(), the provider half of verify_langchain()."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain._provider_checks import check_provider

_PROVIDER_CHECKS = "mcp_coder.llm.providers.langchain._provider_checks"

_OPENAI_CONFIG: dict[str, str | None] = {
    "provider": "langchain",
    "backend": "openai",
    "model": "gpt-4o",
    "api_key": "sk-test1234test5678",
    "base_url": None,
    "api_version": None,
}


def _not_mcp(package: str) -> bool:
    """Every package is installed except the two MCP ones."""
    return package not in ("langchain_mcp_adapters", "langgraph")


@pytest.fixture(autouse=True)
def _clear_env() -> Iterator[None]:
    with patch.dict("os.environ", {}, clear=True):
        yield


def test_takes_config_and_returns_no_mcp_rows() -> None:
    """The config is an argument; the MCP rows belong to verify_langchain."""
    with patch(f"{_PROVIDER_CHECKS}._check_package_installed", return_value=True):
        result = check_provider(_OPENAI_CONFIG)

    assert result["backend"] == {"ok": True, "value": "openai"}
    assert result["model"]["value"] == "gpt-4o"
    assert "mcp_adapters" not in result
    assert "langgraph" not in result
    assert list(result)[-1] == "overall_ok"


def test_overall_ok_ignores_missing_mcp_packages() -> None:
    """A configured backend with its packages is ok without the MCP packages."""
    with patch(f"{_PROVIDER_CHECKS}._check_package_installed", side_effect=_not_mcp):
        result = check_provider(_OPENAI_CONFIG)

    assert result["backend_package"]["ok"] is True
    assert result["overall_ok"] is True


def test_check_models_adds_listing_rows() -> None:
    listing = {"ok": True, "value": ["gpt-4o"]}
    with (
        patch(f"{_PROVIDER_CHECKS}._check_package_installed", return_value=True),
        patch(f"{_PROVIDER_CHECKS}._list_models_for_backend", return_value=listing),
    ):
        result = check_provider(_OPENAI_CONFIG, check_models=True)

    assert result["available_models"] == listing
    assert result["model_check"]["ok"] is True
