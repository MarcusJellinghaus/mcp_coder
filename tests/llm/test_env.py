"""Tests for LLM environment variable preparation module."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.env import prepare_llm_environment


def test_prepare_llm_environment_success(tmp_path: Path) -> None:
    """Test successful environment preparation with valid venv."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    venv_dir.mkdir()

    # Mock detect_python_environment to return a valid venv
    with patch("mcp_coder.llm.env.detect_python_environment") as mock_detect:
        mock_detect.return_value = (
            str(venv_dir / "bin" / "python"),
            str(venv_dir),
        )

        result = prepare_llm_environment(project_dir)

        # Verify function was called with project_dir
        mock_detect.assert_called_once_with(project_dir)

        # Verify return value
        assert "MCP_CODER_PROJECT_DIR" in result
        assert "MCP_CODER_VENV_DIR" in result

        # Verify paths are absolute
        assert Path(result["MCP_CODER_PROJECT_DIR"]).is_absolute()
        assert Path(result["MCP_CODER_VENV_DIR"]).is_absolute()

        # Verify paths match expected values (resolved absolute paths)
        assert result["MCP_CODER_PROJECT_DIR"] == str(project_dir.resolve())
        assert result["MCP_CODER_VENV_DIR"] == str(venv_dir.resolve())


def test_prepare_llm_environment_no_venv(tmp_path: Path) -> None:
    """Test environment preparation fails when no venv is found."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Mock detect_python_environment to return None for venv_path
    with patch("mcp_coder.llm.env.detect_python_environment") as mock_detect:
        mock_detect.return_value = ("/usr/bin/python3", None)

        with pytest.raises(RuntimeError) as exc_info:
            prepare_llm_environment(project_dir)

        # Verify error message contains helpful information
        error_msg = str(exc_info.value)
        assert "No virtual environment found" in error_msg
        assert str(project_dir) in error_msg
        assert "python -m venv .venv" in error_msg


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


def test_prepare_llm_environment_logging(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that environment preparation logs debug messages."""
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
