"""verify_langchain() folds the MCP package checks back into the provider rows."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain.verification import (
    _check_mcp_adapter_packages,
    verify_langchain,
)

_VERIFICATION = "mcp_coder.llm.providers.langchain.verification"
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


def test_missing_mcp_packages_fail_overall_ok() -> None:
    with (
        patch(f"{_VERIFICATION}._load_langchain_config", return_value=_OPENAI_CONFIG),
        patch(f"{_PROVIDER_CHECKS}._check_package_installed", side_effect=_not_mcp),
    ):
        result = verify_langchain()

    assert result["backend_package"]["ok"] is True
    assert result["mcp_adapters"]["ok"] is False
    assert result["langgraph"]["ok"] is False
    assert result["overall_ok"] is False


def test_mcp_check_sees_the_provider_checks_patch() -> None:
    """One patch on _provider_checks covers the MCP package check too."""
    with patch(
        f"{_PROVIDER_CHECKS}._check_package_installed", side_effect=_not_mcp
    ) as mock_pkg:
        result = _check_mcp_adapter_packages()

    assert mock_pkg.call_count == 2
    assert result["mcp_adapters"]["ok"] is False
    assert result["langgraph"]["ok"] is False
