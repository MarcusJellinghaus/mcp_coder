"""Tests for pyproject.toml configuration sections."""

import tomllib
from pathlib import Path


def test_pyproject_install_from_github_config_exists() -> None:
    """Verify [tool.mcp-coder.install-from-github] section exists with expected keys."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    install_from_github = config["tool"]["mcp-coder"]["install-from-github"]

    assert "packages" in install_from_github
    assert isinstance(install_from_github["packages"], list)

    assert "packages-no-deps" in install_from_github
    assert isinstance(install_from_github["packages-no-deps"], list)


def test_pyproject_implement_config_exists() -> None:
    """Verify [tool.mcp-coder.implement] section exists with expected keys."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    implement = config["tool"]["mcp-coder"]["implement"]

    assert implement["format_code"] is True
    assert implement["check_type_hints"] is True


def test_pyproject_typecheck_extra_exists() -> None:
    """Verify [typecheck] optional-dependency group exists with mypy + types stubs."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    typecheck = config["project"]["optional-dependencies"]["typecheck"]

    assert any(
        entry.startswith("mypy>=1.13") for entry in typecheck
    ), f"typecheck extra must declare mypy>=1.13.0, got: {typecheck}"
    assert (
        "mcp-coder[types]" in typecheck
    ), f"typecheck extra must reference [types] stubs group, got: {typecheck}"


def test_pyproject_langchain_base_floors() -> None:
    """Verify [langchain-base] declares the floors that clear #1078's warning."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    base = config["project"]["optional-dependencies"]["langchain-base"]

    assert (
        "langchain-core>=1.4.7" in base
    ), f"langchain-base must declare langchain-core>=1.4.7, got: {base}"
    assert (
        "langgraph>=1.2.9" in base
    ), f"langchain-base must declare langgraph>=1.2.9, got: {base}"
