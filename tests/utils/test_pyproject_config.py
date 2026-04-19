"""Tests for pyproject_config utility functions."""

from pathlib import Path

from mcp_coder.utils.pyproject_config import (
    get_github_install_config,
    get_implement_config,
)


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


class TestGetImplementConfig:
    """Tests for get_implement_config."""

    def test_returns_both_true_when_configured(self, tmp_path: Path) -> None:
        """Both keys set to true are returned."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.implement]
format_code = true
check_type_hints = true
""",
            encoding="utf-8",
        )
        config = get_implement_config(tmp_path)
        assert config.format_code is True
        assert config.check_type_hints is True

    def test_defaults_to_false_when_section_missing(self, tmp_path: Path) -> None:
        """Missing [tool.mcp-coder.implement] returns False for both."""
        (tmp_path / "pyproject.toml").write_text("[tool.mcp-coder]\n", encoding="utf-8")
        config = get_implement_config(tmp_path)
        assert config.format_code is False
        assert config.check_type_hints is False

    def test_defaults_to_false_when_file_missing(self, tmp_path: Path) -> None:
        """No pyproject.toml returns False for both."""
        config = get_implement_config(tmp_path)
        assert config.format_code is False
        assert config.check_type_hints is False

    def test_partial_keys_default_missing_to_false(self, tmp_path: Path) -> None:
        """Only format_code set, check_type_hints defaults to False."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.implement]
format_code = true
""",
            encoding="utf-8",
        )
        config = get_implement_config(tmp_path)
        assert config.format_code is True
        assert config.check_type_hints is False

    def test_handles_invalid_toml(self, tmp_path: Path) -> None:
        """Malformed TOML file returns defaults."""
        (tmp_path / "pyproject.toml").write_text(
            "this is not valid toml {{{", encoding="utf-8"
        )
        config = get_implement_config(tmp_path)
        assert config.format_code is False
        assert config.check_type_hints is False
