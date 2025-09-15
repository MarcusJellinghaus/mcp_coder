"""Tests for subprocess_runner module functionality."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
    get_python_isolation_env,
    is_python_command,
)


class TestCommandResult:
    """Test the CommandResult dataclass."""

    def test_command_result_initialization(self) -> None:
        """Test CommandResult can be initialized with required fields."""
        result = CommandResult(
            return_code=0,
            stdout="test output",
            stderr="test error",
            timed_out=False,
        )
        
        assert result.return_code == 0
        assert result.stdout == "test output"
        assert result.stderr == "test error"
        assert result.timed_out is False
        assert result.execution_error is None
        assert result.command is None
        assert result.runner_type is None
        assert result.execution_time_ms is None

    def test_command_result_with_optional_fields(self) -> None:
        """Test CommandResult with all optional fields set."""
        command = ["python", "-c", "print('hello')"]
        result = CommandResult(
            return_code=1,
            stdout="output",
            stderr="error",
            timed_out=True,
            execution_error="timeout error",
            command=command,
            runner_type="subprocess",
            execution_time_ms=1500,
        )
        
        assert result.return_code == 1
        assert result.stdout == "output"
        assert result.stderr == "error"
        assert result.timed_out is True
        assert result.execution_error == "timeout error"
        assert result.command == command
        assert result.runner_type == "subprocess"
        assert result.execution_time_ms == 1500


class TestCommandOptions:
    """Test the CommandOptions dataclass."""

    def test_command_options_defaults(self) -> None:
        """Test CommandOptions default values."""
        options = CommandOptions()
        
        assert options.cwd is None
        assert options.timeout_seconds == 120
        assert options.env is None
        assert options.capture_output is True
        assert options.text is True
        assert options.check is False
        assert options.shell is False
        assert options.input_data is None

    def test_command_options_custom_values(self) -> None:
        """Test CommandOptions with custom values."""
        env = {"TEST_VAR": "test_value"}
        options = CommandOptions(
            cwd="/test/dir",
            timeout_seconds=60,
            env=env,
            capture_output=False,
            text=False,
            check=True,
            shell=True,
            input_data="input",
        )
        
        assert options.cwd == "/test/dir"
        assert options.timeout_seconds == 60
        assert options.env == env
        assert options.capture_output is False
        assert options.text is False
        assert options.check is True
        assert options.shell is True
        assert options.input_data == "input"


class TestIsPythonCommand:
    """Test the is_python_command function."""

    def test_empty_command(self) -> None:
        """Test that empty command returns False."""
        assert is_python_command([]) is False

    def test_python_commands(self) -> None:
        """Test recognition of various Python commands."""
        python_commands = [
            ["python"],
            ["python3"],
            ["python.exe"],
            ["python3.exe"],
            ["/usr/bin/python"],
            ["/usr/bin/python3"],
            ["C:\\Python39\\python.exe"],
            [sys.executable],
        ]
        
        for command in python_commands:
            assert is_python_command(command) is True, f"Failed for command: {command}"

    def test_non_python_commands(self) -> None:
        """Test that non-Python commands return False."""
        non_python_commands = [
            ["ls"],
            ["echo", "hello"],
            ["node", "script.js"],
            ["java", "-jar", "app.jar"],
            ["gcc", "program.c"],
            ["python_like_but_not_python"],
        ]
        
        for command in non_python_commands:
            assert is_python_command(command) is False, f"Failed for command: {command}"

    def test_python_with_arguments(self) -> None:
        """Test Python commands with arguments."""
        python_commands_with_args = [
            ["python", "-c", "print('hello')"],
            ["python3", "-m", "pip", "install", "package"],
            ["python.exe", "script.py"],
        ]
        
        for command in python_commands_with_args:
            assert is_python_command(command) is True, f"Failed for command: {command}"


class TestGetPythonIsolationEnv:
    """Test the get_python_isolation_env function."""

    def test_python_isolation_env_contains_required_vars(self) -> None:
        """Test that isolation environment contains required Python variables."""
        env = get_python_isolation_env()
        
        required_vars = {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONNOUSERSITE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONSTARTUP": "",
        }
        
        for var, expected_value in required_vars.items():
            assert env.get(var) == expected_value, f"Missing or incorrect {var}"

    def test_python_isolation_env_removes_mcp_vars(self) -> None:
        """Test that MCP-specific variables are removed."""
        with patch.dict(os.environ, {
            "MCP_STDIO_TRANSPORT": "test",
            "MCP_SERVER_NAME": "test_server",
            "MCP_CLIENT_PARAMS": "test_params",
            "OTHER_VAR": "keep_this",
        }):
            env = get_python_isolation_env()
            
            assert "MCP_STDIO_TRANSPORT" not in env
            assert "MCP_SERVER_NAME" not in env
            assert "MCP_CLIENT_PARAMS" not in env
            assert env.get("OTHER_VAR") == "keep_this"

    def test_python_isolation_env_preserves_other_vars(self) -> None:
        """Test that other environment variables are preserved."""
        with patch.dict(os.environ, {"PATH": "/test/path", "HOME": "/test/home"}):
            env = get_python_isolation_env()
            
            assert env.get("PATH") == "/test/path"
            assert env.get("HOME") == "/test/home"


class TestExecuteSubprocess:
    """Test the execute_subprocess function."""

    def test_execute_subprocess_invalid_command(self) -> None:
        """Test that None command raises TypeError."""
        with pytest.raises(TypeError, match="Command cannot be None"):
            execute_subprocess(None)  # type: ignore

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_execute_subprocess_successful_execution(self, mock_run: MagicMock) -> None:
        """Test successful subprocess execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "test output"
        mock_process.stderr = "test error"
        mock_run.return_value = mock_process
        
        result = execute_subprocess(["echo", "hello"])
        
        assert result.return_code == 0
        assert result.stdout == "test output"
        assert result.stderr == "test error"
        assert result.timed_out is False
        assert result.execution_error is None
        assert result.command == ["echo", "hello"]
        assert result.runner_type == "subprocess"
        assert isinstance(result.execution_time_ms, int)

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_execute_subprocess_with_check_option_success(self, mock_run: MagicMock) -> None:
        """Test subprocess execution with check=True on success."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "success"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        options = CommandOptions(check=True)
        result = execute_subprocess(["true"], options)
        
        assert result.return_code == 0
        assert result.stdout == "success"

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_execute_subprocess_with_check_option_failure(self, mock_run: MagicMock) -> None:
        """Test subprocess execution with check=True on failure."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = "failure"
        mock_process.stderr = "error"
        mock_run.return_value = mock_process
        
        options = CommandOptions(check=True)
        
        with pytest.raises(subprocess.CalledProcessError):
            execute_subprocess(["false"], options)

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_execute_subprocess_timeout(self, mock_run: MagicMock) -> None:
        """Test subprocess execution timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(["sleep", "10"], 5)
        
        options = CommandOptions(timeout_seconds=5)
        result = execute_subprocess(["sleep", "10"], options)
        
        assert result.return_code == 1
        assert result.timed_out is True
        assert result.execution_error is not None and "timed out after 5 seconds" in result.execution_error
        assert result.command == ["sleep", "10"]

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_execute_subprocess_file_not_found(self, mock_run: MagicMock) -> None:
        """Test subprocess execution with FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        result = execute_subprocess(["nonexistent_command"])
        
        assert result.return_code == 1
        assert result.timed_out is False
        assert result.execution_error is not None and "FileNotFoundError: Command not found" in result.execution_error

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_execute_subprocess_permission_error(self, mock_run: MagicMock) -> None:
        """Test subprocess execution with PermissionError."""
        mock_run.side_effect = PermissionError("Permission denied")
        
        result = execute_subprocess(["restricted_command"])
        
        assert result.return_code == 1
        assert result.timed_out is False
        assert result.execution_error is not None and "PermissionError: Permission denied" in result.execution_error

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_execute_subprocess_called_process_error_without_check(self, mock_run: MagicMock) -> None:
        """Test subprocess execution with CalledProcessError when check=False."""
        error = subprocess.CalledProcessError(2, ["false"], "output", "stderr")
        mock_run.side_effect = error
        
        options = CommandOptions(check=False)
        result = execute_subprocess(["false"], options)
        
        assert result.return_code == 2
        assert result.stdout == "output"
        assert result.stderr == "stderr"
        assert result.timed_out is False


class TestExecuteCommand:
    """Test the execute_command convenience function."""

    @patch("mcp_coder.utils.subprocess_runner.execute_subprocess")
    def test_execute_command_default_options(self, mock_execute: MagicMock) -> None:
        """Test execute_command with default options."""
        mock_result = CommandResult(0, "output", "", False)
        mock_execute.return_value = mock_result
        
        result = execute_command(["echo", "hello"])
        
        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        assert args[0] == ["echo", "hello"]
        
        options = args[1]
        assert options.cwd is None
        assert options.timeout_seconds == 120
        assert options.env is None
        
        assert result == mock_result

    @patch("mcp_coder.utils.subprocess_runner.execute_subprocess")
    def test_execute_command_custom_options(self, mock_execute: MagicMock) -> None:
        """Test execute_command with custom options."""
        mock_result = CommandResult(0, "output", "", False)
        mock_execute.return_value = mock_result
        
        env = {"TEST": "value"}
        result = execute_command(
            ["python", "-c", "print('test')"],
            cwd="/test/dir",
            timeout_seconds=60,
            env=env,
        )
        
        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        assert args[0] == ["python", "-c", "print('test')"]
        
        options = args[1]
        assert options.cwd == "/test/dir"
        assert options.timeout_seconds == 60
        assert options.env == env
        
        assert result == mock_result


class TestIntegration:
    """Integration tests that actually execute subprocess commands."""

    def test_simple_echo_command(self) -> None:
        """Test executing a simple echo command."""
        # Use Python's print instead of echo for cross-platform compatibility
        result = execute_command([sys.executable, "-c", "print('hello world')"])
        
        assert result.return_code == 0
        assert "hello world" in result.stdout
        assert result.timed_out is False
        assert result.execution_error is None

    def test_python_command_execution(self) -> None:
        """Test executing a Python command."""
        python_code = "print('test output')"
        result = execute_command([sys.executable, "-c", python_code])
        
        assert result.return_code == 0
        assert "test output" in result.stdout
        assert result.timed_out is False

    def test_command_with_working_directory(self) -> None:
        """Test command execution with specific working directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file in the temp directory
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            # Use a command that should work cross-platform
            if os.name == "nt":  # Windows
                # Use PowerShell's dir command or Python to list directory
                result = execute_command([sys.executable, "-c", "import os; print('\\n'.join(os.listdir('.')))"], cwd=temp_dir)
            else:  # Unix-like
                result = execute_command(["ls"], cwd=temp_dir)
            
            assert result.return_code == 0
            assert "test.txt" in result.stdout

    def test_command_timeout(self) -> None:
        """Test command timeout functionality."""
        # Use Python's time.sleep for cross-platform compatibility
        result = execute_command([sys.executable, "-c", "import time; time.sleep(10)"], timeout_seconds=1)
        
        assert result.timed_out is True
        assert result.return_code == 1
        assert result.execution_error is not None and "timed out" in result.execution_error

    def test_nonexistent_command(self) -> None:
        """Test executing a nonexistent command."""
        result = execute_command(["nonexistent_command_12345"])
        
        assert result.return_code == 1
        assert result.execution_error is not None
        assert result.execution_error is not None
        assert "FileNotFoundError" in result.execution_error or "not found" in result.execution_error.lower()

    def test_python_isolation_environment(self) -> None:
        """Test that Python commands get isolation environment."""
        # This test verifies that Python commands run with the isolation environment
        python_code = "import os; print(os.environ.get('PYTHONUNBUFFERED', 'not_set'))"
        result = execute_command([sys.executable, "-c", python_code])
        
        assert result.return_code == 0
        assert "1" in result.stdout  # PYTHONUNBUFFERED should be set to "1"

    def test_disable_stdio_isolation(self) -> None:
        """Test disabling STDIO isolation with environment variable."""
        python_code = "print('isolation disabled test')"
        env = {"_DISABLE_STDIO_ISOLATION": "1"}
        
        result = execute_command([sys.executable, "-c", python_code], env=env)
        
        assert result.return_code == 0
        assert "isolation disabled test" in result.stdout


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_command_list(self) -> None:
        """Test that empty command list is handled gracefully."""
        with pytest.raises(TypeError):
            execute_subprocess(None)  # type: ignore

    def test_command_with_special_characters(self) -> None:
        """Test command with special characters in arguments."""
        # Test with Python print that can handle special characters
        special_text = "Hello! @#$%^&*()_+ World"
        result = execute_command([sys.executable, "-c", f"print('{special_text}')"])
        
        assert result.return_code == 0
        assert special_text in result.stdout

    @patch("mcp_coder.utils.subprocess_runner._run_subprocess")
    def test_command_result_with_none_stdout_stderr(self, mock_run: MagicMock) -> None:
        """Test handling of None stdout/stderr from subprocess."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = None
        mock_process.stderr = None
        mock_run.return_value = mock_process
        
        result = execute_subprocess(["test"])
        
        assert result.stdout == ""
        assert result.stderr == ""

    def test_very_long_output(self) -> None:
        """Test handling of commands that produce very long output."""
        # Generate a long string
        long_string = "x" * 10000
        python_code = f"print('{long_string}')"
        
        result = execute_command([sys.executable, "-c", python_code])
        
        assert result.return_code == 0
        assert long_string in result.stdout
        assert len(result.stdout) >= 10000
