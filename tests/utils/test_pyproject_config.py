"""Tests for pyproject_config utility functions."""

import logging
from pathlib import Path

import pytest

from mcp_coder.utils.pyproject_config import (
    FormatCodeSetting,
    ImplementConfig,
    _load_pyproject,
    get_format_code,
    get_github_install_config,
    get_implement_config,
    get_install_extras,
    get_post_install_checks,
    get_prompts_config,
    has_legacy_format_code_key,
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

    def test_returns_packages_when_only_packages_declared(self, tmp_path: Path) -> None:
        """Only the packages key is set."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.install-from-github]
packages = ["pkg-a @ git+https://example.com/a.git"]
""",
            encoding="utf-8",
        )
        config = get_github_install_config(tmp_path)
        assert config.packages == ["pkg-a @ git+https://example.com/a.git"]
        assert config.packages_no_deps == []

    def test_returns_no_deps_when_only_no_deps_declared(self, tmp_path: Path) -> None:
        """Only the packages-no-deps key is set."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.install-from-github]
packages-no-deps = ["pkg-b @ git+https://example.com/b.git"]
""",
            encoding="utf-8",
        )
        config = get_github_install_config(tmp_path)
        assert config.packages == []
        assert config.packages_no_deps == ["pkg-b @ git+https://example.com/b.git"]

    @pytest.mark.parametrize("key", ["packages", "packages-no-deps"])
    def test_raises_when_value_is_a_bare_string(self, tmp_path: Path, key: str) -> None:
        """A string instead of a list is rejected, naming the file and the key.

        The installer concatenates these onto a uv argv, so a bare string would
        otherwise surface as a TypeError mid-install.
        """
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install-from-github]\n"
            f'{key} = "pkg-a @ git+https://example.com/a.git"\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError) as exc_info:
            get_github_install_config(tmp_path)
        message = str(exc_info.value)
        assert key in message
        assert "pyproject.toml" in message
        assert "list of strings" in message

    @pytest.mark.parametrize("key", ["packages", "packages-no-deps"])
    def test_raises_when_list_holds_a_non_string(
        self, tmp_path: Path, key: str
    ) -> None:
        """A list with a non-string entry is rejected too."""
        (tmp_path / "pyproject.toml").write_text(
            f'[tool.mcp-coder.install-from-github]\n{key} = ["pkg-a", 42]\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError) as exc_info:
            get_github_install_config(tmp_path)
        assert key in str(exc_info.value)


class TestGetImplementConfig:
    """Tests for get_implement_config."""

    def test_returns_true_when_configured(self, tmp_path: Path) -> None:
        """check_type_hints set to true is returned."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.implement]
check_type_hints = true
""",
            encoding="utf-8",
        )
        config = get_implement_config(tmp_path)
        assert config.check_type_hints is True

    def test_defaults_to_false_when_section_missing(self, tmp_path: Path) -> None:
        """Missing [tool.mcp-coder.implement] returns False."""
        (tmp_path / "pyproject.toml").write_text("[tool.mcp-coder]\n", encoding="utf-8")
        config = get_implement_config(tmp_path)
        assert config.check_type_hints is False

    def test_defaults_to_false_when_file_missing(self, tmp_path: Path) -> None:
        """No pyproject.toml returns False."""
        config = get_implement_config(tmp_path)
        assert config.check_type_hints is False

    def test_legacy_format_code_key_is_ignored(self, tmp_path: Path) -> None:
        """A leftover format_code key does not affect the config."""
        (tmp_path / "pyproject.toml").write_text(
            """\
[tool.mcp-coder.implement]
format_code = true
""",
            encoding="utf-8",
        )
        config = get_implement_config(tmp_path)
        assert config == ImplementConfig(check_type_hints=False)

    def test_handles_invalid_toml(self, tmp_path: Path) -> None:
        """Malformed TOML file returns defaults."""
        (tmp_path / "pyproject.toml").write_text(
            "this is not valid toml {{{", encoding="utf-8"
        )
        config = get_implement_config(tmp_path)
        assert config.check_type_hints is False


class TestGetFormatCode:
    """Tests for get_format_code."""

    def test_absent_defaults_to_enabled(self, tmp_path: Path) -> None:
        """Missing key → enabled, not explicit."""
        (tmp_path / "pyproject.toml").write_text("[tool.mcp-coder]\n", encoding="utf-8")
        assert get_format_code(tmp_path) == FormatCodeSetting(
            enabled=True, explicit=False
        )

    def test_true(self, tmp_path: Path) -> None:
        """format_code = true → enabled, explicit."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder]\nformat_code = true\n", encoding="utf-8"
        )
        assert get_format_code(tmp_path) == FormatCodeSetting(
            enabled=True, explicit=True
        )

    def test_false(self, tmp_path: Path) -> None:
        """format_code = false → disabled, explicit."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
        )
        assert get_format_code(tmp_path) == FormatCodeSetting(
            enabled=False, explicit=True
        )

    def test_non_bool_raises(self, tmp_path: Path) -> None:
        """A string value raises ValueError naming key and file."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder]\nformat_code = "false"\n', encoding="utf-8"
        )
        with pytest.raises(ValueError) as exc_info:
            get_format_code(tmp_path)
        assert "format_code" in str(exc_info.value)
        assert str(tmp_path / "pyproject.toml") in str(exc_info.value)

    def test_missing_file_defaults_to_enabled(self, tmp_path: Path) -> None:
        """No pyproject.toml → enabled, not explicit."""
        assert get_format_code(tmp_path) == FormatCodeSetting(
            enabled=True, explicit=False
        )

    def test_malformed_file_defaults_to_enabled(self, tmp_path: Path) -> None:
        """Malformed pyproject.toml → enabled, not explicit."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        assert get_format_code(tmp_path) == FormatCodeSetting(
            enabled=True, explicit=False
        )

    def test_legacy_key_is_not_read(self, tmp_path: Path) -> None:
        """[tool.mcp-coder.implement] format_code does not affect the switch."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.implement]\nformat_code = false\n", encoding="utf-8"
        )
        assert get_format_code(tmp_path) == FormatCodeSetting(
            enabled=True, explicit=False
        )


class TestHasLegacyFormatCodeKey:
    """Tests for has_legacy_format_code_key."""

    def test_present(self, tmp_path: Path) -> None:
        """Key under [tool.mcp-coder.implement] → True."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.implement]\nformat_code = true\n", encoding="utf-8"
        )
        assert has_legacy_format_code_key(tmp_path) is True

    def test_absent(self, tmp_path: Path) -> None:
        """Section without the key → False."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.implement]\ncheck_type_hints = true\n", encoding="utf-8"
        )
        assert has_legacy_format_code_key(tmp_path) is False

    def test_missing_file(self, tmp_path: Path) -> None:
        """No pyproject.toml → False."""
        assert has_legacy_format_code_key(tmp_path) is False


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

    def test_raises_for_non_string_value_strict(self, tmp_path: Path) -> None:
        """A list-valued extras is a target-repo error, not an install spec."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\nextras = ['dev']\n", encoding="utf-8"
        )
        with pytest.raises(ValueError) as exc_info:
            get_install_extras(tmp_path, strict=True)
        message = str(exc_info.value)
        assert str(tmp_path / "pyproject.toml") in message
        assert "extras" in message
        assert "list" in message

    def test_returns_none_for_non_string_value_lax(self, tmp_path: Path) -> None:
        """Lax callers treat a mistyped value as not declared."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\nextras = true\n", encoding="utf-8"
        )
        assert get_install_extras(tmp_path) is None


_MALFORMED_POST_INSTALL_CHECKS = [
    pytest.param("'mcp-coder --version'", "'mcp-coder --version'", id="string"),
    pytest.param(
        "['mcp-coder', '--version']",
        "['mcp-coder', '--version']",
        id="list_of_strings",
    ),
    pytest.param("[[]]", "[[]]", id="empty_inner_list"),
    pytest.param("[['mcp-coder', 1]]", "[['mcp-coder', 1]]", id="non_string_element"),
]


class TestGetPostInstallChecks:
    """Tests for get_post_install_checks."""

    def test_returns_declared_checks_in_order(self, tmp_path: Path) -> None:
        """A valid list of argv lists becomes a tuple of tuples, order kept."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\n"
            "post_install_checks = [\n"
            "    ['mcp-coder', '--version'],\n"
            "    ['mcp-workspace', '--help'],\n"
            "]\n",
            encoding="utf-8",
        )
        assert get_post_install_checks(tmp_path) == (
            ("mcp-coder", "--version"),
            ("mcp-workspace", "--help"),
        )

    def test_returns_empty_when_key_missing(self, tmp_path: Path) -> None:
        """Section present without the key returns ()."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\n", encoding="utf-8"
        )
        assert get_post_install_checks(tmp_path) == ()

    def test_returns_empty_when_section_missing(self, tmp_path: Path) -> None:
        """Missing [tool.mcp-coder.install] returns ()."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname = 'test'\n", encoding="utf-8"
        )
        assert get_post_install_checks(tmp_path) == ()

    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        """No pyproject.toml returns ()."""
        assert get_post_install_checks(tmp_path) == ()

    def test_returns_empty_for_empty_list(self, tmp_path: Path) -> None:
        """An explicit empty list declares no checks."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mcp-coder.install]\npost_install_checks = []\n", encoding="utf-8"
        )
        assert get_post_install_checks(tmp_path, strict=True) == ()

    @pytest.mark.parametrize(
        ("toml_value", "repr_fragment"), _MALFORMED_POST_INSTALL_CHECKS
    )
    def test_raises_for_malformed_value_strict(
        self, tmp_path: Path, toml_value: str, repr_fragment: str
    ) -> None:
        """Strict mode names the file, the key and the offending value."""
        (tmp_path / "pyproject.toml").write_text(
            f"[tool.mcp-coder.install]\npost_install_checks = {toml_value}\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError) as exc_info:
            get_post_install_checks(tmp_path, strict=True)
        message = str(exc_info.value)
        assert str(tmp_path / "pyproject.toml") in message
        assert "post_install_checks" in message
        assert repr_fragment in message

    @pytest.mark.parametrize(
        ("toml_value", "repr_fragment"), _MALFORMED_POST_INSTALL_CHECKS
    )
    def test_returns_empty_and_warns_for_malformed_value_lax(
        self,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
        toml_value: str,
        repr_fragment: str,
    ) -> None:
        """Lax callers get () and a warning naming the key."""
        (tmp_path / "pyproject.toml").write_text(
            f"[tool.mcp-coder.install]\npost_install_checks = {toml_value}\n",
            encoding="utf-8",
        )
        with caplog.at_level(logging.WARNING):
            assert get_post_install_checks(tmp_path) == ()
        assert "post_install_checks" in caplog.text
        assert repr_fragment in caplog.text


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
        assert config.check_type_hints is False
