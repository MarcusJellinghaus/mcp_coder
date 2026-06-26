"""Tests for LLM environment variable preparation module.

The tool-env vars (``MCP_CODER_VENV_DIR`` / ``MCP_CODER_VENV_PATH``) identify
where mcp-coder and the MCP servers are installed. They are resolved from the
running interpreter (``sys.prefix``) or a pre-set launcher value -- deliberately
NOT from ``VIRTUAL_ENV``, which in the two-environment model points at the
*project* venv and need not contain the MCP server executables.
"""

import logging
import sys
from pathlib import Path

import pytest

from mcp_coder.llm.env import prepare_llm_environment


@pytest.fixture()
def tool_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point sys.prefix at a fake tool env and clear all venv env signals.

    This isolates tests from the real interpreter and from any ``VIRTUAL_ENV`` /
    ``CONDA_PREFIX`` / ``MCP_CODER_VENV_*`` set in the parent environment, so
    ``sys.prefix`` is the only source unless a test overrides it.
    """
    for var in (
        "MCP_CODER_VENV_DIR",
        "MCP_CODER_VENV_PATH",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
    ):
        monkeypatch.delenv(var, raising=False)

    env_root = tmp_path / "tool_env"
    env_root.mkdir()
    monkeypatch.setattr(sys, "prefix", str(env_root))
    return env_root


def test_defaults_to_sys_prefix(tool_env: Path, tmp_path: Path) -> None:
    """With no overrides, the tool env is the running interpreter's prefix."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    result = prepare_llm_environment(project_dir)

    assert result["MCP_CODER_VENV_DIR"] == str(tool_env.resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())


def test_ignores_virtual_env(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression (#995): VIRTUAL_ENV must NOT drive the tool-env path.

    A launcher activates the project venv (VIRTUAL_ENV) for pytest/mypy, but the
    MCP server executables live in the tool env. Deriving the server path from
    VIRTUAL_ENV pointed it at a venv without ``mcp-tools-py.exe`` -> servers
    failed -> ``tools: []``.
    """
    project_venv = tmp_path / "project" / ".venv"
    project_venv.mkdir(parents=True)
    monkeypatch.setenv("VIRTUAL_ENV", str(project_venv))

    project_dir = tmp_path / "project"

    result = prepare_llm_environment(project_dir)

    # Tool env follows sys.prefix, not the activated project venv.
    assert result["MCP_CODER_VENV_DIR"] == str(tool_env.resolve())
    assert result["MCP_CODER_VENV_DIR"] != str(project_venv.resolve())


def test_ignores_conda_prefix(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONDA_PREFIX must not drive the tool-env path either (sys.prefix wins)."""
    conda_env = tmp_path / "miniconda3" / "envs" / "myenv"
    conda_env.mkdir(parents=True)
    monkeypatch.setenv("CONDA_PREFIX", str(conda_env))

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    result = prepare_llm_environment(project_dir)

    assert result["MCP_CODER_VENV_DIR"] == str(tool_env.resolve())


def test_honors_preset_venv_dir(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A two-env-aware launcher's MCP_CODER_VENV_DIR takes precedence."""
    launcher_tool_env = tmp_path / "jenkins" / "tool" / ".venv"
    launcher_tool_env.mkdir(parents=True)
    monkeypatch.setenv("MCP_CODER_VENV_DIR", str(launcher_tool_env))
    # Even with a (different) project venv activated, the preset wins.
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "project" / ".venv"))

    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    result = prepare_llm_environment(project_dir)

    assert result["MCP_CODER_VENV_DIR"] == str(launcher_tool_env.resolve())


def test_preset_venv_dir_nonexistent_falls_back_to_sys_prefix(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale/non-existent MCP_CODER_VENV_DIR falls back to sys.prefix."""
    monkeypatch.setenv("MCP_CODER_VENV_DIR", str(tmp_path / "does" / "not" / "exist"))

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    result = prepare_llm_environment(project_dir)

    assert result["MCP_CODER_VENV_DIR"] == str(tool_env.resolve())


def test_honors_preset_venv_path(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A launcher-provided MCP_CODER_VENV_PATH (bin dir) is preserved."""
    launcher_bin = tmp_path / "jenkins" / "tool" / ".venv" / "Scripts"
    launcher_bin.mkdir(parents=True)
    monkeypatch.setenv("MCP_CODER_VENV_PATH", str(launcher_bin))

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    result = prepare_llm_environment(project_dir)

    assert result["MCP_CODER_VENV_PATH"] == str(launcher_bin.resolve())


def test_venv_path_defaults_to_bin_subdir(tool_env: Path, tmp_path: Path) -> None:
    """Without a preset, VENV_PATH is the Scripts/bin child of the tool env."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    result = prepare_llm_environment(project_dir)

    venv_path = Path(result["MCP_CODER_VENV_PATH"])
    expected_suffix = "Scripts" if sys.platform == "win32" else "bin"
    assert venv_path.name == expected_suffix
    assert venv_path.is_relative_to(Path(result["MCP_CODER_VENV_DIR"]))


def test_project_and_tool_env_are_independent(tool_env: Path, tmp_path: Path) -> None:
    """Project directory and tool env resolve to unrelated paths."""
    project_dir = tmp_path / "workspace" / "myproject"
    project_dir.mkdir(parents=True)

    result = prepare_llm_environment(project_dir)

    venv_path = Path(result["MCP_CODER_VENV_DIR"])
    project_path = Path(result["MCP_CODER_PROJECT_DIR"])
    assert not venv_path.is_relative_to(project_path)
    assert not project_path.is_relative_to(venv_path)


def test_paths_absolute_and_os_native(tool_env: Path, tmp_path: Path) -> None:
    """All returned paths are absolute OS-native strings."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    result = prepare_llm_environment(project_dir)

    for key in ("MCP_CODER_PROJECT_DIR", "MCP_CODER_VENV_DIR", "MCP_CODER_VENV_PATH"):
        assert isinstance(result[key], str)
        assert Path(result[key]).is_absolute()


def test_sets_disable_autoupdater_default(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DISABLE_AUTOUPDATER defaults to '1' when not set."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.delenv("DISABLE_AUTOUPDATER", raising=False)

    result = prepare_llm_environment(project_dir)

    assert result["DISABLE_AUTOUPDATER"] == "1"


def test_preserves_existing_disable_autoupdater(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing DISABLE_AUTOUPDATER value is preserved."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.setenv("DISABLE_AUTOUPDATER", "0")

    result = prepare_llm_environment(project_dir)

    assert result["DISABLE_AUTOUPDATER"] == "0"


def test_sets_mcp_timeout_default(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MCP_TIMEOUT defaults to '30000' when not set."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.delenv("MCP_TIMEOUT", raising=False)

    result = prepare_llm_environment(project_dir)

    assert result["MCP_TIMEOUT"] == "30000"


def test_preserves_existing_mcp_timeout(
    tool_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing MCP_TIMEOUT value is preserved."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.setenv("MCP_TIMEOUT", "60000")

    result = prepare_llm_environment(project_dir)

    assert result["MCP_TIMEOUT"] == "60000"


@pytest.mark.xdist_group(name="logging")
def test_logs_debug_messages(
    tool_env: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Environment preparation logs debug messages.

    Note: caplog doesn't work well with pytest-xdist; the xdist_group marker
    ensures it runs in isolation.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    module_logger = logging.getLogger("mcp_coder.llm.env")
    with caplog.at_level(logging.DEBUG, logger=module_logger.name):
        prepare_llm_environment(project_dir)

    assert any(
        "Preparing LLM environment" in record.message for record in caplog.records
    )
    assert any("MCP_CODER_PROJECT_DIR" in record.message for record in caplog.records)
