"""Tests for pyproject_config utility functions."""

from pathlib import Path

import pytest

from mcp_coder.utils.pyproject_config import (
    _load_pyproject,
    get_github_install_config,
    get_implement_config,
    get_install_extras,
    get_prompts_config,
)

MALFORMED_TOML = "this is not valid toml {{{"


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


class TestLoadPyproject:
    """Tests for the shared _load_pyproject loader."""

    def test_returns_parsed_data(self, tmp_path: Path) -> None:
        """A valid file is parsed into a dict."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname = 'test'\n", encoding="utf-8"
        )
        assert _load_pyproject(tmp_path) == {"project": {"name": "test"}}

    def test_missing_file_returns_empty_lax(self, tmp_path: Path) -> None:
        """No pyproject.toml returns an empty dict when lax."""
        assert _load_pyproject(tmp_path) == {}

    def test_missing_file_returns_empty_strict(self, tmp_path: Path) -> None:
        """A missing file is never an error, even when strict."""
        assert _load_pyproject(tmp_path, strict=True) == {}

    def test_malformed_returns_empty_lax(self, tmp_path: Path) -> None:
        """Malformed TOML returns an empty dict when lax."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        assert _load_pyproject(tmp_path) == {}

    def test_malformed_raises_strict(self, tmp_path: Path) -> None:
        """Malformed TOML raises a ValueError naming the file when strict."""
        path = tmp_path / "pyproject.toml"
        path.write_text(MALFORMED_TOML, encoding="utf-8")
        with pytest.raises(ValueError, match="pyproject.toml"):
            _load_pyproject(tmp_path, strict=True)
        # The formatted message names the full path
        with pytest.raises(ValueError) as exc_info:
            _load_pyproject(tmp_path, strict=True)
        assert str(path) in str(exc_info.value)


class TestGetInstallExtras:
    """Tests for get_install_extras."""

    def test_returns_declared_value(self, tmp_path: Path) -> None:
        """A declared extras value is returned unparsed."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\nextras = 'dev,mlflow'\n", encoding="utf-8"
        )
        assert get_install_extras(tmp_path) == "dev,mlflow"

    def test_returns_none_when_key_missing(self, tmp_path: Path) -> None:
        """Section present without the key returns None."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\n", encoding="utf-8"
        )
        assert get_install_extras(tmp_path) is None

    def test_returns_none_when_section_missing(self, tmp_path: Path) -> None:
        """Missing [tool.mcp-coder.install] returns None."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname = 'test'\n", encoding="utf-8"
        )
        assert get_install_extras(tmp_path) is None

    def test_returns_none_when_file_missing(self, tmp_path: Path) -> None:
        """No pyproject.toml returns None."""
        assert get_install_extras(tmp_path) is None

    def test_returns_none_for_malformed_file_lax(self, tmp_path: Path) -> None:
        """Malformed TOML returns None when lax."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        assert get_install_extras(tmp_path) is None

    def test_raises_for_malformed_file_strict(self, tmp_path: Path) -> None:
        """Malformed TOML raises when strict."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        with pytest.raises(ValueError, match="pyproject.toml"):
            get_install_extras(tmp_path, strict=True)

    def test_empty_string_is_distinct_from_none(self, tmp_path: Path) -> None:
        """An explicit empty extras value is honoured, not treated as absent."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\nextras = ''\n", encoding="utf-8"
        )
        assert get_install_extras(tmp_path) == ""


class TestMalformedTomlRegression:
    """Existing readers keep returning neutral defaults for malformed TOML."""

    def test_prompts_config_returns_defaults(self, tmp_path: Path) -> None:
        """get_prompts_config does not raise on malformed TOML."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        config = get_prompts_config(tmp_path)
        assert config.system_prompt is None
        assert config.project_prompt is None
        assert config.claude_system_prompt_mode == "append"

    def test_github_install_config_returns_defaults(self, tmp_path: Path) -> None:
        """get_github_install_config does not raise on malformed TOML."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        config = get_github_install_config(tmp_path)
        assert config.packages == []
        assert config.packages_no_deps == []

    def test_implement_config_returns_defaults(self, tmp_path: Path) -> None:
        """get_implement_config does not raise on malformed TOML."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        config = get_implement_config(tmp_path)
        assert config.format_code is False
        assert config.check_type_hints is False
