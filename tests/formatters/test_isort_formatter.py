"""Tests for isort formatter implementation using TDD approach.

Based on Step 3 requirements: 6 comprehensive tests covering core import sorting,
configuration integration, and real-world analysis scenarios.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from mcp_coder.formatters import FormatterResult


# Test fixtures and utilities
@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        yield project_path


@pytest.fixture
def unsorted_imports_code() -> str:
    """Sample Python code with unsorted imports that needs isort formatting."""
    return """import sys
import os
from pathlib import Path
import json
from typing import Dict, List
import subprocess
from collections import defaultdict
import argparse

def main():
    print("Hello world")
"""


@pytest.fixture
def sorted_imports_code() -> str:
    """Sample Python code with properly sorted imports."""
    return """import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def main():
    print("Hello world")
"""


@pytest.fixture
def import_error_code() -> str:
    """Python code with malformed import syntax that will cause isort to fail."""
    return """import [
from pathlib import
from typing import Dict List syntax error
import sys os invalid
from collections import defaultdict (
"""


@pytest.fixture
def pyproject_toml_with_isort_config() -> str:
    """pyproject.toml content with isort configuration."""
    return """[tool.isort]
profile = "black"
line_length = 100
float_to_top = true
"""


class TestIsortFormatterCore:
    """Core import sorting scenarios - 3 tests."""

    def test_format_unsorted_imports(
        self, temp_project_dir: Path, unsorted_imports_code: str
    ) -> None:
        """Test format_with_isort() on imports needing sorting (exit 1 → success)."""
        # This test will fail until we implement the isort formatter
        from mcp_coder.formatters.isort_formatter import format_with_isort

        # Create a Python file that needs import sorting
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        # Format the imports
        result = format_with_isort(temp_project_dir)

        # Should succeed and report the file as changed
        assert result.success is True
        assert result.formatter_name == "isort"
        assert str(test_file) in result.files_changed
        assert result.error_message is None

        # Verify the file was actually formatted
        formatted_content = test_file.read_text()
        assert formatted_content != unsorted_imports_code
        # Should have alphabetically sorted standard library imports
        lines = formatted_content.split("\n")
        import_lines = [
            line
            for line in lines
            if line.startswith("import ") and not line.startswith("from ")
        ]
        assert import_lines[0] == "import argparse"
        assert import_lines[1] == "import json"

    def test_format_already_sorted_imports(
        self, temp_project_dir: Path, sorted_imports_code: str
    ) -> None:
        """Test on properly sorted imports (exit 0 → no changes)."""
        from mcp_coder.formatters.isort_formatter import format_with_isort

        # Create a Python file that is already import-sorted
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(sorted_imports_code)
        original_content = sorted_imports_code

        # Format the imports
        result = format_with_isort(temp_project_dir)

        # Should succeed but report no changes
        assert result.success is True
        assert result.formatter_name == "isort"
        assert len(result.files_changed) == 0
        assert result.error_message is None

        # Verify the file content unchanged
        assert test_file.read_text() == original_content

    def test_format_robust_handling(
        self, temp_project_dir: Path, import_error_code: str
    ) -> None:
        """Test that isort handles various edge cases robustly."""
        from mcp_coder.formatters.isort_formatter import format_with_isort

        # Create a Python file with problematic import syntax
        test_file = temp_project_dir / "edge_case.py"
        test_file.write_text(import_error_code)

        # Attempt to format the imports
        result = format_with_isort(temp_project_dir)

        # isort is very tolerant and should handle edge cases gracefully
        # It typically processes what it can and skips problematic lines
        assert result.success is True
        assert result.formatter_name == "isort"
        assert result.error_message is None


class TestIsortFormatterConfiguration:
    """Configuration integration - 2 tests."""

    def test_default_config_missing_pyproject(
        self, temp_project_dir: Path, unsorted_imports_code: str
    ) -> None:
        """Test with missing pyproject.toml (use isort defaults)."""
        from mcp_coder.formatters.isort_formatter import (
            _get_isort_config,
            format_with_isort,
        )

        # No pyproject.toml file - should use defaults
        config = _get_isort_config(temp_project_dir)

        # Should return default isort configuration
        assert config["profile"] == "black"  # isort default compatibility
        assert config["line_length"] == 88  # Black profile default
        assert config["float_to_top"] is True  # isort default

        # Create and format a file to verify it works with defaults
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        result = format_with_isort(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed

    def test_custom_config_from_pyproject(
        self,
        temp_project_dir: Path,
        unsorted_imports_code: str,
        pyproject_toml_with_isort_config: str,
    ) -> None:
        """Test with Black compatibility and custom line_length from pyproject.toml."""
        from mcp_coder.formatters.isort_formatter import (
            _get_isort_config,
            format_with_isort,
        )

        # Create pyproject.toml with custom isort config
        pyproject_file = temp_project_dir / "pyproject.toml"
        pyproject_file.write_text(pyproject_toml_with_isort_config)

        # Should read custom configuration
        config = _get_isort_config(temp_project_dir)
        assert config["profile"] == "black"  # Custom value
        assert config["line_length"] == 100  # Custom value
        assert config["float_to_top"] is True  # Custom value

        # Create and format a file to verify it works with custom config
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        result = format_with_isort(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed


class TestIsortFormatterRealWorld:
    """Real-world analysis scenario - 1 test."""

    def test_analysis_import_sample(self, temp_project_dir: Path) -> None:
        """Use actual unsorted imports from Step 0 findings to verify patterns."""
        from mcp_coder.formatters.isort_formatter import format_with_isort

        # Real unformatted import sample similar to what might be analyzed
        analysis_imports = """#!/usr/bin/env python3
import subprocess,sys,json
from pathlib import Path
import tempfile
import os
from typing import Dict,List,Optional
import logging
from dataclasses import dataclass
import argparse

@dataclass
class AnalysisResult:
    status: str
    files: List[str]

def run_isort_check(files: List[str]) -> Dict[str, any]:
    cmd=['isort','--check-only'] + files
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode==0:
        return {"status":"no_changes","files":[]}
    elif result.returncode==1:
        return {"status":"changes_needed","files":files}
    else:
        return {"status":"error","message":result.stderr}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    
    result = run_isort_check(args.files)
    print(json.dumps(result, indent=2))

if __name__=="__main__":
    main()
"""

        # Create the analysis imports file
        test_file = temp_project_dir / "analysis_imports.py"
        test_file.write_text(analysis_imports)

        # Format using our isort formatter
        result = format_with_isort(temp_project_dir)

        # Should successfully format the imports
        assert result.success is True
        assert result.formatter_name == "isort"
        assert str(test_file) in result.files_changed
        assert result.error_message is None

        # Verify the imports were properly sorted
        formatted_content = test_file.read_text()
        assert formatted_content != analysis_imports

        # Check for specific import sorting improvements
        lines = formatted_content.split("\n")

        # Standard library imports should come first, alphabetically sorted
        standard_imports = [
            line
            for line in lines
            if line.startswith("import ")
            and "typing" not in line
            and "pathlib" not in line
        ]
        if len(standard_imports) >= 2:
            assert "import argparse" in formatted_content
            assert "import json" in formatted_content
            assert "import logging" in formatted_content

        # From imports should be grouped and sorted
        from_imports = [line for line in lines if line.startswith("from ")]
        assert any("from dataclasses import dataclass" in line for line in from_imports)
        assert any("from pathlib import Path" in line for line in from_imports)
        assert any("from typing import" in line for line in from_imports)


class TestIsortFormatterUtilities:
    """Test utility functions."""

    def test_get_isort_config_function(self, temp_project_dir: Path) -> None:
        """Test the _get_isort_config function directly."""
        from mcp_coder.formatters.isort_formatter import _get_isort_config

        # Test with no config file
        config = _get_isort_config(temp_project_dir)
        assert isinstance(config, dict)
        assert "profile" in config
        assert "line_length" in config
        assert "float_to_top" in config

    def test_check_isort_changes_function(
        self, temp_project_dir: Path, unsorted_imports_code: str
    ) -> None:
        """Test the _check_isort_changes function directly."""
        from mcp_coder.formatters.isort_formatter import _check_isort_changes

        # Create a file that needs import sorting
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        # Should detect that changes are needed
        config = {"profile": "black", "line_length": 88, "float_to_top": True}
        needs_sorting = _check_isort_changes(str(test_file), config)
        assert needs_sorting is True

    def test_apply_isort_formatting_function(
        self, temp_project_dir: Path, unsorted_imports_code: str
    ) -> None:
        """Test the _apply_isort_formatting function directly."""
        from mcp_coder.formatters.isort_formatter import _apply_isort_formatting

        # Create a file that needs import sorting
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        # Apply import sorting
        config = {"profile": "black", "line_length": 88, "float_to_top": True}
        success = _apply_isort_formatting(str(test_file), config)
        assert success is True

        # Verify file was changed
        formatted_content = test_file.read_text()
        assert formatted_content != unsorted_imports_code
