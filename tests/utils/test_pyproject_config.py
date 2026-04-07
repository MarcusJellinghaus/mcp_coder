"""Tests for pyproject_config utility functions."""

from pathlib import Path

from mcp_coder.utils.pyproject_config import (
    check_line_length_conflicts,
    get_formatter_config,
    get_github_install_config,
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


class TestGetFormatterConfig:
    """Tests for get_formatter_config."""

    def test_reads_black_and_isort(self, tmp_path: Path) -> None:
        """Both black and isort configs are returned."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88
""",
            encoding="utf-8",
        )
        config = get_formatter_config(tmp_path)
        assert config["black"]["line-length"] == 100
        assert config["isort"]["profile"] == "black"
        assert config["isort"]["line_length"] == 88

    def test_returns_empty_when_no_tool_section(self, tmp_path: Path) -> None:
        """No [tool] section returns empty dict."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname = 'test'\n", encoding="utf-8"
        )
        config = get_formatter_config(tmp_path)
        assert config == {}

    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        """No pyproject.toml returns empty dict."""
        config = get_formatter_config(tmp_path)
        assert config == {}


class TestCheckLineLengthConflicts:
    """Tests for check_line_length_conflicts."""

    def test_detects_conflict(self) -> None:
        """Detects mismatched line lengths between black and isort."""
        config = {"black": {"line-length": 100}, "isort": {"line_length": 88}}
        result = check_line_length_conflicts(config)
        assert result is not None
        assert "100" in result
        assert "88" in result

    def test_no_conflict_when_matching(self) -> None:
        """No warning when line lengths match."""
        config = {"black": {"line-length": 88}, "isort": {"line_length": 88}}
        assert check_line_length_conflicts(config) is None

    def test_no_conflict_when_missing(self) -> None:
        """No warning when line-length settings are absent."""
        config = {"black": {"target-version": ["py311"]}, "isort": {"profile": "black"}}
        assert check_line_length_conflicts(config) is None
