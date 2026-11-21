"""Tests for pyproject.toml configuration sections."""

import tomllib
from pathlib import Path

from mcp_coder.utils.pyproject_config import get_leftover_check_type_hints


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


def test_pyproject_has_no_leftover_check_type_hints() -> None:
    """Verify this repo no longer sets the retired check_type_hints key."""
    root = Path(__file__).parent.parent
    assert get_leftover_check_type_hints(root) is None


def test_pyproject_typecheck_extra_exists() -> None:
    """Verify [typecheck] optional-dependency group exists with mypy + types stubs."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    typecheck = config["project"]["optional-dependencies"]["typecheck"]

    assert any(entry.startswith("mypy>=1.13") for entry in typecheck), (
        f"typecheck extra must declare mypy>=1.13.0, got: {typecheck}"
    )
    assert "mcp-coder[types]" in typecheck, (
        f"typecheck extra must reference [types] stubs group, got: {typecheck}"
    )
