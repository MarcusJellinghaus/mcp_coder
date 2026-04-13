"""Tests for pyproject_config utility functions."""

from pathlib import Path

from mcp_coder.utils.pyproject_config import get_github_install_config


class TestGetGithubInstallConfig:
    """Tests for get_github_install_config."""

    def test_returns_packages_and_no_deps(self, tmp_path: Path) -> None:
        """Both packages and packages-no-deps are returned."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.install-from-github]
packages = ["pkg-a @ git+https://example.com/a.git"]
packages-no-deps = ["pkg-b @ git+https://example.com/b.git"]
""",
            encoding="utf-8",
        )
        config = get_github_install_config(tmp_path)
        assert config.packages == ["pkg-a @ git+https://example.com/a.git"]
        assert config.packages_no_deps == ["pkg-b @ git+https://example.com/b.git"]

    def test_returns_empty_when_section_missing(self, tmp_path: Path) -> None:
        """Missing [tool.mcp-coder.install-from-github] returns empty lists."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname = 'test'\n", encoding="utf-8"
        )
        config = get_github_install_config(tmp_path)
        assert config.packages == []
        assert config.packages_no_deps == []

    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        """No pyproject.toml returns empty lists."""
        config = get_github_install_config(tmp_path)
        assert config.packages == []
        assert config.packages_no_deps == []

    def test_returns_empty_when_lists_empty(self, tmp_path: Path) -> None:
        """Section exists but lists are empty."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.install-from-github]
packages = []
packages-no-deps = []
""",
            encoding="utf-8",
        )
        config = get_github_install_config(tmp_path)
        assert config.packages == []
        assert config.packages_no_deps == []
