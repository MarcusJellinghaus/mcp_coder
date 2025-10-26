"""Tests for LLM environment variable preparation module."""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.env import prepare_llm_environment


def test_prepare_llm_environment_uses_virtual_env_variable(tmp_path: Path) -> None:
    """Test that VIRTUAL_ENV environment variable is used for runner environment."""
    # Arrange
    runner_venv = tmp_path / "runner" / ".venv"
    runner_venv.mkdir(parents=True)

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Act
    with patch.dict(os.environ, {"VIRTUAL_ENV": str(runner_venv)}):
        result = prepare_llm_environment(project_dir)

    # Assert
    assert result["MCP_CODER_VENV_DIR"] == str(runner_venv.resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())


def test_prepare_llm_environment_uses_conda_prefix(tmp_path: Path) -> None:
    """Test that CONDA_PREFIX is used when VIRTUAL_ENV not set."""
    # Arrange
    conda_env = tmp_path / "miniconda3" / "envs" / "myenv"
    conda_env.mkdir(parents=True)

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Act - Clear VIRTUAL_ENV, set CONDA_PREFIX
    env_vars = os.environ.copy()
    env_vars.pop("VIRTUAL_ENV", None)  # Ensure not set
    env_vars["CONDA_PREFIX"] = str(conda_env)

    with patch.dict(os.environ, env_vars, clear=True):
        result = prepare_llm_environment(project_dir)

    # Assert
    assert result["MCP_CODER_VENV_DIR"] == str(conda_env.resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())


def test_prepare_llm_environment_uses_sys_prefix_fallback(tmp_path: Path) -> None:
    """Test that sys.prefix is used when no venv/conda variables set."""
    # Arrange
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    system_prefix = "/usr" if sys.platform != "win32" else "C:\\Python311"

    # Act - Clear both VIRTUAL_ENV and CONDA_PREFIX
    env_vars = os.environ.copy()
    env_vars.pop("VIRTUAL_ENV", None)
    env_vars.pop("CONDA_PREFIX", None)

    with patch.dict(os.environ, env_vars, clear=True):
        with patch.object(sys, "prefix", system_prefix):
            result = prepare_llm_environment(project_dir)

    # Assert
    assert result["MCP_CODER_VENV_DIR"] == str(Path(system_prefix).resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())


def test_prepare_llm_environment_separate_runner_project(tmp_path: Path) -> None:
    """Test that runner environment and project directory are independent."""
    # Arrange - Create separate locations
    runner_location = tmp_path / "opt" / "mcp-coder" / ".venv"
    runner_location.mkdir(parents=True)

    project_location = tmp_path / "workspace" / "myproject"
    project_location.mkdir(parents=True)

    # Act
    with patch.dict(os.environ, {"VIRTUAL_ENV": str(runner_location)}):
        result = prepare_llm_environment(project_location)

    # Assert - They should be completely different paths
    assert result["MCP_CODER_VENV_DIR"] == str(runner_location.resolve())
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_location.resolve())

    # Verify they're truly separate
    venv_path = Path(result["MCP_CODER_VENV_DIR"])
    project_path = Path(result["MCP_CODER_PROJECT_DIR"])
    assert not venv_path.is_relative_to(project_path)
    assert not project_path.is_relative_to(venv_path)


def test_prepare_llm_environment_success(tmp_path: Path) -> None:
    """Test successful environment preparation with valid venv."""
    # Arrange
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = tmp_path / "runner" / ".venv"
    venv_dir.mkdir(parents=True)

    # Act - Use VIRTUAL_ENV instead of mocking detect_python_environment
    with patch.dict(os.environ, {"VIRTUAL_ENV": str(venv_dir)}):
        result = prepare_llm_environment(project_dir)

    # Assert
    assert "MCP_CODER_PROJECT_DIR" in result
    assert "MCP_CODER_VENV_DIR" in result
    assert Path(result["MCP_CODER_PROJECT_DIR"]).is_absolute()
    assert Path(result["MCP_CODER_VENV_DIR"]).is_absolute()
    assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())
    assert result["MCP_CODER_VENV_DIR"] == str(venv_dir.resolve())


def test_prepare_llm_environment_paths_absolute(tmp_path: Path) -> None:
    """Test that returned paths are always absolute."""
    # Use a relative path for project_dir
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    venv_dir.mkdir()

    with patch("mcp_coder.llm.env.detect_python_environment") as mock_detect:
        # Return relative paths from detect_python_environment
        mock_detect.return_value = ("bin/python", ".venv")

        result = prepare_llm_environment(project_dir)

        # Both paths should be absolute
        assert Path(result["MCP_CODER_PROJECT_DIR"]).is_absolute()
        assert Path(result["MCP_CODER_VENV_DIR"]).is_absolute()


def test_prepare_llm_environment_paths_os_native(tmp_path: Path) -> None:
    """Test that returned paths use OS-native format."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    venv_dir.mkdir()

    with patch("mcp_coder.llm.env.detect_python_environment") as mock_detect:
        mock_detect.return_value = (
            str(venv_dir / "bin" / "python"),
            str(venv_dir),
        )

        result = prepare_llm_environment(project_dir)

        # Verify paths are strings (not Path objects)
        assert isinstance(result["MCP_CODER_PROJECT_DIR"], str)
        assert isinstance(result["MCP_CODER_VENV_DIR"], str)

        # Verify they can be converted back to Path objects
        project_path = Path(result["MCP_CODER_PROJECT_DIR"])
        venv_path = Path(result["MCP_CODER_VENV_DIR"])

        assert project_path.is_absolute()
        assert venv_path.is_absolute()


@pytest.mark.xdist_group(name="logging")
def test_prepare_llm_environment_logging(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that environment preparation logs debug messages.

    Note: This test uses caplog which doesn't work well with pytest-xdist.
    The xdist_group marker ensures it runs in isolation.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    venv_dir.mkdir()

    with patch("mcp_coder.llm.env.detect_python_environment") as mock_detect:
        mock_detect.return_value = (
            str(venv_dir / "bin" / "python"),
            str(venv_dir),
        )

        with caplog.at_level(logging.DEBUG):
            prepare_llm_environment(project_dir)

        # Verify debug messages were logged
        assert any(
            "Preparing LLM environment" in record.message for record in caplog.records
        )
        assert any(
            "MCP_CODER_PROJECT_DIR" in record.message for record in caplog.records
        )
