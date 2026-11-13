"""Tests for [tool.mcp-coder.setup] loading and the shared table lookup."""

from pathlib import Path

import pytest

from mcp_coder.utils.setup_config import (
    DEFAULT_STEP_TIMEOUT,
    SetupConfig,
    SetupStep,
    load_setup_config,
)
from mcp_coder.utils.toml_utils import find_mcp_coder_table
from mcp_coder.utils.toolkit_runner import load_toolkit_config

MALFORMED_TOML = "this is not valid toml {{{"


def _write(directory: Path, name: str, content: str) -> None:
    (directory / name).write_text(content, encoding="utf-8")


def _setup(directory: Path, steps: str) -> None:
    """Write pyproject.toml with a setup table whose steps are ``steps``."""
    _write(directory, "pyproject.toml", f"[tool.mcp-coder.setup]\nsteps = {steps}\n")


class TestFindMcpCoderTable:
    """The shared two-file table lookup."""

    def test_absent(self, tmp_path: Path) -> None:
        """No file defines the table → None."""
        _write(tmp_path, "pyproject.toml", "[tool.mcp-coder.toolkit]\n")
        assert find_mcp_coder_table(tmp_path, "setup") is None

    def test_no_files(self, tmp_path: Path) -> None:
        """No config files at all → None."""
        assert find_mcp_coder_table(tmp_path, "setup") is None

    def test_found(self, tmp_path: Path) -> None:
        """The raw value and its file are returned."""
        _write(tmp_path, "mcp-coder.toml", "[tool.mcp-coder.setup]\nsteps = []\n")
        assert find_mcp_coder_table(tmp_path, "setup") == (
            "mcp-coder.toml",
            {"steps": []},
        )

    def test_tool_not_table(self, tmp_path: Path) -> None:
        """A non-table 'tool' is an error naming the file."""
        _write(tmp_path, "pyproject.toml", 'tool = "x"\n')
        with pytest.raises(ValueError, match=r"Invalid 'tool' in pyproject\.toml"):
            find_mcp_coder_table(tmp_path, "setup")

    def test_mcp_coder_not_table(self, tmp_path: Path) -> None:
        """A non-table 'mcp-coder' is an error naming the file."""
        _write(tmp_path, "mcp-coder.toml", "[tool]\nmcp-coder = 1\n")
        with pytest.raises(ValueError, match=r"Invalid 'mcp-coder' in mcp-coder\.toml"):
            find_mcp_coder_table(tmp_path, "setup")

    def test_both_files(self, tmp_path: Path) -> None:
        """Both files defining the table is an error naming the table."""
        _write(tmp_path, "pyproject.toml", "[tool.mcp-coder.setup]\n")
        _write(tmp_path, "mcp-coder.toml", "[tool.mcp-coder.setup]\n")
        with pytest.raises(ValueError, match=r"define \[tool\.mcp-coder\.setup\]"):
            find_mcp_coder_table(tmp_path, "setup")


class TestDefaults:
    """No setup table anywhere."""

    def test_pyproject_without_table(self, tmp_path: Path) -> None:
        """pyproject.toml present → one python built-in step."""
        _write(tmp_path, "pyproject.toml", "[project]\nname = 'x'\n")
        config = load_setup_config(tmp_path)
        assert config.source is None
        assert config.steps == (SetupStep(None, "python", None, DEFAULT_STEP_TIMEOUT),)
        assert config.uses_python()

    def test_no_pyproject(self, tmp_path: Path) -> None:
        """No pyproject.toml → no steps."""
        config = load_setup_config(tmp_path)
        assert config == SetupConfig((), None)
        assert not config.uses_python()

    def test_mcp_coder_toml_without_table(self, tmp_path: Path) -> None:
        """mcp-coder.toml alone without the table → no steps."""
        _write(tmp_path, "mcp-coder.toml", "[tool.mcp-coder.toolkit]\n")
        assert load_setup_config(tmp_path).steps == ()


class TestSource:
    """Which file the table comes from."""

    def test_empty_steps(self, tmp_path: Path) -> None:
        """steps = [] → no steps, even with pyproject.toml."""
        _setup(tmp_path, "[]")
        config = load_setup_config(tmp_path)
        assert config.steps == ()
        assert config.source == "pyproject.toml"

    def test_mcp_coder_toml_only(self, tmp_path: Path) -> None:
        """Table in mcp-coder.toml is resolved."""
        _write(
            tmp_path,
            "mcp-coder.toml",
            '[tool.mcp-coder.setup]\nsteps = [{ argv = ["npm", "ci"] }]\n',
        )
        config = load_setup_config(tmp_path)
        assert config.source == "mcp-coder.toml"
        assert config.steps[0].argv == ("npm", "ci")

    def test_both_files(self, tmp_path: Path) -> None:
        """Both files defining the table is an error."""
        _setup(tmp_path, "[]")
        _write(tmp_path, "mcp-coder.toml", "[tool.mcp-coder.setup]\nsteps = []\n")
        with pytest.raises(ValueError, match="keep one"):
            load_setup_config(tmp_path)

    def test_tables_in_different_files(self, tmp_path: Path) -> None:
        """Toolkit in mcp-coder.toml and setup in pyproject.toml both load."""
        _setup(tmp_path, '[{ argv = ["make"] }]')
        _write(
            tmp_path, "mcp-coder.toml", '[tool.mcp-coder.toolkit]\ntoolkit = "kit"\n'
        )
        assert load_setup_config(tmp_path).source == "pyproject.toml"
        toolkit = load_toolkit_config(tmp_path)
        assert toolkit.source == "mcp-coder.toml"
        assert toolkit.toolkit == "kit"

    def test_malformed_toml(self, tmp_path: Path) -> None:
        """A malformed file is an error naming the file."""
        _write(tmp_path, "mcp-coder.toml", MALFORMED_TOML)
        with pytest.raises(ValueError, match="mcp-coder.toml"):
            load_setup_config(tmp_path)


class TestSteps:
    """Parsing valid steps."""

    def test_full_steps(self, tmp_path: Path) -> None:
        """argv, builtin, name and timeout are parsed in order."""
        _setup(
            tmp_path,
            '[{ builtin = "python" }, '
            '{ argv = ["npm", "ci"], name = "deps", timeout = 60 }]',
        )
        config = load_setup_config(tmp_path)
        assert config.steps == (
            SetupStep(None, "python", None, DEFAULT_STEP_TIMEOUT),
            SetupStep(("npm", "ci"), None, "deps", 60),
        )
        assert config.uses_python()

    def test_argv_default_timeout(self, tmp_path: Path) -> None:
        """An argv step without timeout gets the default."""
        _setup(tmp_path, '[{ argv = ["make"] }]')
        step = load_setup_config(tmp_path).steps[0]
        assert step.timeout == DEFAULT_STEP_TIMEOUT == 1800
        assert not load_setup_config(tmp_path).uses_python()

    def test_label(self) -> None:
        """label prefers name, then builtin, then the joined argv."""
        assert SetupStep(("a", "b"), None, "named", 1).label == "named"
        assert SetupStep(None, "python", None, 1).label == "python"
        assert SetupStep(None, "python", "py", 1).label == "py"
        assert SetupStep(("cargo", "fetch"), None, None, 1).label == "cargo fetch"


class TestErrors:
    """Every invalid table is a ValueError naming file, table and key."""

    @pytest.mark.parametrize(
        ("steps", "match"),
        [
            ('["npm ci"]', r"steps\[0\] in pyproject\.toml: expected a table"),
            (
                '[{ argv = ["a"] }, { argv = ["b"], cmd = "x" }]',
                r"Unknown .* key 'cmd' in steps\[1\]",
            ),
            (
                '[{ argv = ["a"], builtin = "python" }]',
                r"steps\[0\] .*exactly one of argv or builtin",
            ),
            ('[{ name = "x" }]', r"steps\[0\] .*exactly one of argv or builtin"),
            ("[{ argv = [] }]", r"steps\[0\]\.argv .*non-empty list of strings"),
            ('[{ argv = "npm ci" }]', r"steps\[0\]\.argv .*got str"),
            ('[{ argv = ["npm", 1] }]', r"steps\[0\]\.argv .*non-empty list"),
            ('[{ builtin = "node" }]', r"steps\[0\]\.builtin .*got str: 'node'"),
            ("[{ builtin = 1 }]", r"steps\[0\]\.builtin .*one of python"),
            (
                '[{ builtin = "python", timeout = 10 }]',
                r"steps\[0\] .*timeout is only allowed with argv",
            ),
            ('[{ argv = ["a"], timeout = 0 }]', r"steps\[0\]\.timeout .*got int: 0"),
            ('[{ argv = ["a"], timeout = -5 }]', r"steps\[0\]\.timeout .*-5"),
            (
                '[{ argv = ["a"], timeout = true }]',
                r"steps\[0\]\.timeout .*got bool: True",
            ),
            ('[{ argv = ["a"], timeout = "60" }]', r"steps\[0\]\.timeout .*got str"),
            (
                '[{ argv = ["a"], name = 3 }]',
                r"steps\[0\]\.name .*expected a string, got int: 3",
            ),
            (
                '{ argv = ["a"] }',
                r"Invalid .* steps in pyproject\.toml: expected a list",
            ),
        ],
    )
    def test_invalid_steps(self, tmp_path: Path, steps: str, match: str) -> None:
        """Invalid step definitions raise ValueError with a precise message."""
        _setup(tmp_path, steps)
        with pytest.raises(ValueError, match=match) as exc_info:
            load_setup_config(tmp_path)
        assert "[tool.mcp-coder.setup]" in str(exc_info.value)

    def test_missing_steps(self, tmp_path: Path) -> None:
        """A table without steps is an error."""
        _write(tmp_path, "pyproject.toml", "[tool.mcp-coder.setup]\n")
        with pytest.raises(ValueError, match=r"Missing .* key 'steps' in pyproject"):
            load_setup_config(tmp_path)

    def test_unknown_top_level_key(self, tmp_path: Path) -> None:
        """An unknown top-level key is an error."""
        _write(
            tmp_path,
            "pyproject.toml",
            "[tool.mcp-coder.setup]\nsteps = []\nrefresh = true\n",
        )
        with pytest.raises(ValueError, match=r"Unknown .* key 'refresh'"):
            load_setup_config(tmp_path)

    def test_table_not_a_table(self, tmp_path: Path) -> None:
        """A non-table setup value is an error."""
        _write(tmp_path, "pyproject.toml", '[tool.mcp-coder]\nsetup = "x"\n')
        with pytest.raises(ValueError, match="expected a table, got str"):
            load_setup_config(tmp_path)
