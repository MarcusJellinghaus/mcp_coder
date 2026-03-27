"""Tests for pyproject.toml configuration sections."""

import tomllib
from pathlib import Path


def test_pyproject_from_github_config_exists() -> None:
    """Verify [tool.mcp-coder.from-github] section exists with expected keys."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    from_github = config["tool"]["mcp-coder"]["from-github"]

    assert "packages" in from_github
    assert isinstance(from_github["packages"], list)

    assert "packages-no-deps" in from_github
    assert isinstance(from_github["packages-no-deps"], list)
