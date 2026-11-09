"""Tests for strict [tool.mcp-coder.toolkit] config loading in toolkit_runner."""

from pathlib import Path

import pytest

from mcp_coder.utils.toolkit_runner import (
    DEFAULT_BINDINGS,
    get_binding,
    load_toolkit_config,
)

MALFORMED_TOML = "this is not valid toml {{{"


def _write(directory: Path, name: str, content: str) -> None:
    (directory / name).write_text(content, encoding="utf-8")


class TestDefaults:
    """No config table anywhere."""

    def test_no_files(self, tmp_path: Path) -> None:
        """No pyproject.toml and no mcp-coder.toml → defaults."""
        config = load_toolkit_config(tmp_path)
        assert config.toolkit == "mcp-tools-py"
        assert config.bindings == DEFAULT_BINDINGS
        assert config.params == {}
        assert config.section == {}
        assert config.source is None

    def test_no_table(self, tmp_path: Path) -> None:
        """pyproject.toml without the table → defaults."""
        _write(tmp_path, "pyproject.toml", "[project]\nname = 'x'\n")
        config = load_toolkit_config(tmp_path)
        assert config.toolkit == "mcp-tools-py"
        assert config.bindings == DEFAULT_BINDINGS
        assert config.source is None

    def test_defaults_not_shared(self, tmp_path: Path) -> None:
        """The returned bindings dict is a copy of DEFAULT_BINDINGS."""
        config = load_toolkit_config(tmp_path)
        assert config.bindings is not DEFAULT_BINDINGS


class TestSource:
    """Which file the table comes from."""

    def test_pyproject_only(self, tmp_path: Path) -> None:
        """Table in pyproject.toml is resolved."""
        _write(
            tmp_path,
            "pyproject.toml",
            '[tool.mcp-coder.toolkit]\ntoolkit = "other-kit"\n',
        )
        config = load_toolkit_config(tmp_path)
        assert config.toolkit == "other-kit"
        assert config.source == "pyproject.toml"

    def test_mcp_coder_toml_only(self, tmp_path: Path) -> None:
        """Table in mcp-coder.toml without a pyproject.toml is resolved."""
        _write(
            tmp_path,
            "mcp-coder.toml",
            '[tool.mcp-coder.toolkit]\ntoolkit = "other-kit"\n',
        )
        config = load_toolkit_config(tmp_path)
        assert config.toolkit == "other-kit"
        assert config.source == "mcp-coder.toml"

    def test_toolkit_key_defaults(self, tmp_path: Path) -> None:
        """An empty table selects the default toolkit."""
        _write(tmp_path, "pyproject.toml", "[tool.mcp-coder.toolkit]\n")
        config = load_toolkit_config(tmp_path)
        assert config.toolkit == "mcp-tools-py"
        assert config.source == "pyproject.toml"

    def test_both_files_with_table(self, tmp_path: Path) -> None:
        """Both files defining the table is an error."""
        _write(tmp_path, "pyproject.toml", "[tool.mcp-coder.toolkit]\n")
        _write(tmp_path, "mcp-coder.toml", "[tool.mcp-coder.toolkit]\n")
        with pytest.raises(ValueError, match="keep one"):
            load_toolkit_config(tmp_path)

    def test_both_files_one_table(self, tmp_path: Path) -> None:
        """Both files present, only one with the table → ok."""
        _write(tmp_path, "pyproject.toml", "[project]\nname = 'x'\n")
        _write(
            tmp_path,
            "mcp-coder.toml",
            '[tool.mcp-coder.toolkit]\ntoolkit = "other-kit"\n',
        )
        config = load_toolkit_config(tmp_path)
        assert config.toolkit == "other-kit"
        assert config.source == "mcp-coder.toml"

    @pytest.mark.parametrize(
        ("bad", "good"),
        [("pyproject.toml", "mcp-coder.toml"), ("mcp-coder.toml", "pyproject.toml")],
    )
    def test_malformed_file(self, tmp_path: Path, bad: str, good: str) -> None:
        """Malformed TOML in either file raises, even when the other is fine."""
        _write(tmp_path, bad, MALFORMED_TOML)
        _write(tmp_path, good, "[tool.mcp-coder.toolkit]\n")
        with pytest.raises(ValueError, match="TOML parse error"):
            load_toolkit_config(tmp_path)


class TestBindings:
    """Binding overrides and get_binding."""

    def test_override_replaces_one_entry(self, tmp_path: Path) -> None:
        """Overriding one entry keeps the others at their defaults."""
        _write(
            tmp_path,
            "pyproject.toml",
            "[tool.mcp-coder.toolkit.bindings]\n"
            'rebase = ["check@full"]\n'
            "implement_final = []\n",
        )
        config = load_toolkit_config(tmp_path)
        assert config.bindings["rebase"] == ("check@full",)
        assert config.bindings["implement_final"] == ()
        for entry in ("implement_task", "commit", "rebase_automated"):
            assert config.bindings[entry] == DEFAULT_BINDINGS[entry]

    def test_get_binding(self, tmp_path: Path) -> None:
        """get_binding returns the resolved entry."""
        _write(
            tmp_path,
            "pyproject.toml",
            '[tool.mcp-coder.toolkit.bindings]\ncommit = ["format@apply"]\n',
        )
        assert get_binding(tmp_path, "commit") == ("format@apply",)
        assert get_binding(tmp_path, "rebase") == DEFAULT_BINDINGS["rebase"]


class TestParamsAndSection:
    """params and the toolkit's own section."""

    def test_params_returned(self, tmp_path: Path) -> None:
        """Raw params tables are returned as-is."""
        _write(
            tmp_path,
            "pyproject.toml",
            "[tool.mcp-coder.toolkit.params.test]\ntimeout = 30\n",
        )
        assert load_toolkit_config(tmp_path).params == {"test": {"timeout": 30}}

    def test_section_returned(self, tmp_path: Path) -> None:
        """[tool.mcp-coder.toolkit.mcp-tools-py] is returned in section."""
        _write(
            tmp_path,
            "pyproject.toml",
            "[tool.mcp-coder.toolkit]\n"
            'toolkit = "mcp-tools-py"\n'
            "[tool.mcp-coder.toolkit.mcp-tools-py]\n"
            'formatter = "ruff"\n',
        )
        assert load_toolkit_config(tmp_path).section == {"formatter": "ruff"}

    def test_section_absent(self, tmp_path: Path) -> None:
        """No section → {}."""
        _write(
            tmp_path,
            "pyproject.toml",
            '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n',
        )
        assert load_toolkit_config(tmp_path).section == {}


@pytest.mark.parametrize(
    ("body", "fragment"),
    [
        pytest.param('unknown = "x"', "unknown", id="unknown-top-level-key"),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\nnope = ["check@quick"]',
            "nope",
            id="unknown-binding-entry",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\nrebase = "check@quick"',
            "rebase",
            id="non-list-binding",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\nrebase = ["check"]',
            "'check'",
            id="no-at",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\nrebase = ["check@"]',
            "'check@'",
            id="empty-depth",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\nimplement_task = ["check@quick"]',
            "implement_task",
            id="implement-task-non-empty",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\nimplement_final = ["test@quick"]',
            "test@quick",
            id="implement-final-test",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\nrebase = ["format@apply"]',
            "format@apply",
            id="rebase-format",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\ncommit = ["format@check"]',
            "format@check",
            id="commit-format-check",
        ),
        pytest.param(
            '[tool.mcp-coder.toolkit.bindings]\ncommit = ["check@quick"]',
            "check@quick",
            id="commit-check",
        ),
        pytest.param('toolkit = "bindings"', "bindings", id="toolkit-bindings"),
        pytest.param('toolkit = "params"', "params", id="toolkit-params"),
        pytest.param('check = "x"', "check", id="per-action-key"),
        pytest.param('params = "x"', "params", id="params-not-table"),
        pytest.param(
            '[tool.mcp-coder.toolkit.params]\ntest = "x"',
            "test",
            id="params-action-not-table",
        ),
        pytest.param('"mcp-tools-py" = "x"', "mcp-tools-py", id="section-not-table"),
        pytest.param("toolkit = 3", "toolkit", id="toolkit-not-string"),
    ],
)
def test_invalid_config(tmp_path: Path, body: str, fragment: str) -> None:
    """Every config error is a ValueError naming the file and the offender."""
    _write(tmp_path, "pyproject.toml", f"[tool.mcp-coder.toolkit]\n{body}\n")
    with pytest.raises(ValueError) as exc_info:
        load_toolkit_config(tmp_path)
    message = str(exc_info.value)
    assert "pyproject.toml" in message
    assert fragment in message


def test_table_not_a_dict(tmp_path: Path) -> None:
    """[tool.mcp-coder] toolkit as a scalar is an error."""
    _write(tmp_path, "pyproject.toml", '[tool.mcp-coder]\ntoolkit = "x"\n')
    with pytest.raises(ValueError, match="pyproject.toml"):
        load_toolkit_config(tmp_path)


@pytest.mark.parametrize(
    "body",
    [
        pytest.param('[tool]\n"mcp-coder" = "x"\n', id="mcp-coder-not-table"),
        pytest.param('tool = "x"\n', id="tool-not-table"),
    ],
)
def test_parent_table_not_a_dict(tmp_path: Path, body: str) -> None:
    """[tool] or [tool.mcp-coder] as a scalar is a ValueError, not a crash."""
    _write(tmp_path, "pyproject.toml", body)
    with pytest.raises(ValueError, match="pyproject.toml"):
        load_toolkit_config(tmp_path)
