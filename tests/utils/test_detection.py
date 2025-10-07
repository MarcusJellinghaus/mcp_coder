"""Tests for Python environment detection utilities."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.utils.detection import (
    _detect_active_venv,
    detect_python_environment,
    find_virtual_environments,
    is_valid_venv,
)


class TestDetectActiveVenv:
    """Tests for _detect_active_venv function."""

    def test_detect_from_virtual_env_variable(self, tmp_path: Path) -> None:
        """Test detection from VIRTUAL_ENV environment variable."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        # Create minimal venv structure
        if sys.platform == "win32":
            scripts_dir = venv_dir / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
            activate = scripts_dir / "activate.bat"
        else:
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"
            activate = bin_dir / "activate"

        python_exe.touch()
        activate.touch()

        with patch.dict(os.environ, {"VIRTUAL_ENV": str(venv_dir)}):
            result = _detect_active_venv()

        assert result == str(venv_dir)

    def test_detect_from_sys_prefix(self, tmp_path: Path) -> None:
        """Test detection from sys.prefix when different from base_prefix."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        # Create minimal venv structure
        if sys.platform == "win32":
            scripts_dir = venv_dir / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
        else:
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"

        python_exe.touch()
        pyvenv_cfg = venv_dir / "pyvenv.cfg"
        pyvenv_cfg.touch()

        # Mock sys.prefix and sys.base_prefix to simulate venv
        # Also clear VIRTUAL_ENV so it doesn't take priority
        with patch.dict(os.environ, {}, clear=False):
            if "VIRTUAL_ENV" in os.environ:
                del os.environ["VIRTUAL_ENV"]

            with patch.object(sys, "prefix", str(venv_dir)):
                with patch.object(sys, "base_prefix", "/usr"):
                    result = _detect_active_venv()

        assert result == str(venv_dir)

    def test_no_venv_detected(self) -> None:
        """Test when not running from a virtual environment."""
        # Clear VIRTUAL_ENV and mock sys.prefix == sys.base_prefix
        with patch.dict(os.environ, {}, clear=False):
            if "VIRTUAL_ENV" in os.environ:
                del os.environ["VIRTUAL_ENV"]

            with patch.object(sys, "prefix", "/usr"):
                with patch.object(sys, "base_prefix", "/usr"):
                    result = _detect_active_venv()

        assert result is None

    def test_invalid_virtual_env_path(self, tmp_path: Path) -> None:
        """Test when VIRTUAL_ENV points to invalid path."""
        fake_venv = tmp_path / "not_a_venv"
        fake_venv.mkdir()

        # Mock sys.prefix == base_prefix to simulate not running in venv
        with patch.dict(os.environ, {"VIRTUAL_ENV": str(fake_venv)}):
            with patch.object(sys, "prefix", "/usr"):
                with patch.object(sys, "base_prefix", "/usr"):
                    result = _detect_active_venv()

        # Should return None because it's not a valid venv
        assert result is None


class TestDetectPythonEnvironmentWithActiveVenv:
    """Tests for detect_python_environment with active venv detection."""

    def test_project_venv_takes_priority(self, tmp_path: Path) -> None:
        """Test that project venv is prioritized over active venv."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_venv = project_dir / ".venv"
        project_venv.mkdir()

        active_venv = tmp_path / "active_venv"
        active_venv.mkdir()

        # Create minimal venv structures
        for venv_dir in [project_venv, active_venv]:
            if sys.platform == "win32":
                scripts_dir = venv_dir / "Scripts"
                scripts_dir.mkdir()
                python_exe = scripts_dir / "python.exe"
            else:
                bin_dir = venv_dir / "bin"
                bin_dir.mkdir()
                python_exe = bin_dir / "python"

            python_exe.touch()
            pyvenv_cfg = venv_dir / "pyvenv.cfg"
            pyvenv_cfg.touch()

        # Mock running from active_venv
        with patch.dict(os.environ, {"VIRTUAL_ENV": str(active_venv)}):
            with patch(
                "mcp_coder.utils.detection.validate_python_executable",
                return_value=True,
            ):
                python_exe_result, venv_path = detect_python_environment(project_dir)

        # Should use project venv, not active venv
        assert venv_path == str(project_venv)

    def test_active_venv_used_when_no_project_venv(self, tmp_path: Path) -> None:
        """Test that active venv is used when project has no venv."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        active_venv = tmp_path / "active_venv"
        active_venv.mkdir()

        # Create minimal venv structure for active venv
        if sys.platform == "win32":
            scripts_dir = active_venv / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
        else:
            bin_dir = active_venv / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"

        python_exe.touch()
        pyvenv_cfg = active_venv / "pyvenv.cfg"
        pyvenv_cfg.touch()

        # Mock running from active_venv
        with patch.dict(os.environ, {"VIRTUAL_ENV": str(active_venv)}):
            with patch(
                "mcp_coder.utils.detection.validate_python_executable",
                return_value=True,
            ):
                python_exe_result, venv_path = detect_python_environment(project_dir)

        # Should use active venv
        assert venv_path == str(active_venv)
        assert python_exe_result == sys.executable

    def test_no_venv_returns_none(self, tmp_path: Path) -> None:
        """Test that None is returned when no venv is available."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Clear VIRTUAL_ENV and mock no venv
        with patch.dict(os.environ, {}, clear=False):
            if "VIRTUAL_ENV" in os.environ:
                del os.environ["VIRTUAL_ENV"]

            with patch.object(sys, "prefix", "/usr"):
                with patch.object(sys, "base_prefix", "/usr"):
                    with patch(
                        "mcp_coder.utils.detection.validate_python_executable",
                        return_value=True,
                    ):
                        python_exe_result, venv_path = detect_python_environment(
                            project_dir
                        )

        # Should return None for venv_path
        assert venv_path is None
        assert python_exe_result == sys.executable


class TestFindVirtualEnvironments:
    """Tests for find_virtual_environments function."""

    def test_find_common_venv_names(self, tmp_path: Path) -> None:
        """Test finding virtual environments with common names."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create .venv
        venv_dir = project_dir / ".venv"
        venv_dir.mkdir()

        if sys.platform == "win32":
            scripts_dir = venv_dir / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
        else:
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"

        python_exe.touch()
        pyvenv_cfg = venv_dir / "pyvenv.cfg"
        pyvenv_cfg.touch()

        venvs = find_virtual_environments(project_dir)

        assert len(venvs) == 1
        assert venvs[0] == venv_dir

    def test_no_venvs_found(self, tmp_path: Path) -> None:
        """Test when no virtual environments exist."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        venvs = find_virtual_environments(project_dir)

        assert len(venvs) == 0


class TestIsValidVenv:
    """Tests for is_valid_venv function."""

    def test_valid_venv_with_pyvenv_cfg(self, tmp_path: Path) -> None:
        """Test validation of venv with pyvenv.cfg."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        if sys.platform == "win32":
            scripts_dir = venv_dir / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
        else:
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"

        python_exe.touch()
        pyvenv_cfg = venv_dir / "pyvenv.cfg"
        pyvenv_cfg.touch()

        assert is_valid_venv(venv_dir) is True

    def test_valid_venv_with_activate(self, tmp_path: Path) -> None:
        """Test validation of venv with activate script."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        if sys.platform == "win32":
            scripts_dir = venv_dir / "Scripts"
            scripts_dir.mkdir()
            python_exe = scripts_dir / "python.exe"
            activate = scripts_dir / "activate.bat"
        else:
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir()
            python_exe = bin_dir / "python"
            activate = bin_dir / "activate"

        python_exe.touch()
        activate.touch()

        assert is_valid_venv(venv_dir) is True

    def test_invalid_venv_no_python(self, tmp_path: Path) -> None:
        """Test that venv without Python executable is invalid."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        pyvenv_cfg = venv_dir / "pyvenv.cfg"
        pyvenv_cfg.touch()

        assert is_valid_venv(venv_dir) is False

    def test_invalid_venv_not_directory(self, tmp_path: Path) -> None:
        """Test that file path is not valid venv."""
        fake_venv = tmp_path / "not_a_dir"
        fake_venv.touch()

        assert is_valid_venv(fake_venv) is False

    def test_invalid_venv_doesnt_exist(self, tmp_path: Path) -> None:
        """Test that non-existent path is not valid venv."""
        fake_venv = tmp_path / "doesnt_exist"

        assert is_valid_venv(fake_venv) is False
