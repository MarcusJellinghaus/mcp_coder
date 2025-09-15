"""Tests for the utils module initialization."""

import importlib

import pytest


class TestUtilsInit:
    """Test the utils module initialization."""

    def test_module_can_be_imported(self) -> None:
        """Test that the utils module can be imported successfully."""
        try:
            import mcp_coder.utils
            assert mcp_coder.utils is not None
        except ImportError as e:
            pytest.fail(f"Failed to import utils module: {e}")

    def test_module_reload(self) -> None:
        """Test that the module can be reloaded without issues."""
        import mcp_coder.utils
        try:
            importlib.reload(mcp_coder.utils)
        except Exception as e:
            pytest.fail(f"Failed to reload utils module: {e}")

    def test_module_attributes(self) -> None:
        """Test that the module has expected attributes."""
        import mcp_coder.utils
        
        # The module should be importable and have the __name__ attribute
        assert hasattr(mcp_coder.utils, "__name__")
        assert mcp_coder.utils.__name__ == "mcp_coder.utils"

    def test_subprocess_runner_is_importable(self) -> None:
        """Test that subprocess_runner can be imported from utils."""
        try:
            from mcp_coder.utils import subprocess_runner
            assert subprocess_runner is not None
        except ImportError as e:
            pytest.fail(f"Failed to import subprocess_runner from utils: {e}")

    def test_subprocess_runner_functions_available(self) -> None:
        """Test that key functions from subprocess_runner are available."""
        from mcp_coder.utils.subprocess_runner import (
            CommandOptions,
            CommandResult,
            execute_command,
            execute_subprocess,
        )
        
        # Verify these are callable
        assert callable(execute_command)
        assert callable(execute_subprocess)
        
        # Verify these are classes/types
        assert CommandOptions is not None
        assert CommandResult is not None
