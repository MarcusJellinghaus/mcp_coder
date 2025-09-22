"""Unit tests for formatter data models."""

from pathlib import Path
from typing import Any, Dict

import pytest

from mcp_coder.formatters.models import FileChange, FormatterConfig, FormatterResult


class TestFormatterConfig:
    """Test FormatterConfig data model."""

    def test_formatter_config_creation(self) -> None:
        """Test basic FormatterConfig creation."""
        config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88},
            target_directories=[Path("src")],
            project_root=Path("/project"),
        )

        assert config.tool_name == "black"
        assert config.settings == {"line-length": 88}
        assert config.target_directories == [Path("src")]
        assert config.project_root == Path("/project")

    def test_formatter_config_empty_settings(self) -> None:
        """Test FormatterConfig with empty settings."""
        config = FormatterConfig(
            tool_name="isort",
            settings={},
            target_directories=[Path("src"), Path("tests")],
            project_root=Path("."),
        )

        assert config.tool_name == "isort"
        assert config.settings == {}
        assert len(config.target_directories) == 2
        assert config.project_root == Path(".")

    def test_formatter_config_multiple_directories(self) -> None:
        """Test FormatterConfig with multiple target directories."""
        dirs = [Path("src"), Path("tests"), Path("scripts")]
        config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 100},
            target_directories=dirs,
            project_root=Path("/workspace"),
        )

        assert config.target_directories == dirs
        assert len(config.target_directories) == 3

    def test_formatter_config_complex_settings(self) -> None:
        """Test FormatterConfig with complex settings."""
        settings = {
            "line-length": 88,
            "target-version": ["py38", "py39"],
            "skip-string-normalization": True,
            "exclude": "migrations/",
        }

        config = FormatterConfig(
            tool_name="black",
            settings=settings,
            target_directories=[Path("app")],
            project_root=Path("/myproject"),
        )

        assert config.settings == settings
        assert config.settings["line-length"] == 88
        assert config.settings["target-version"] == ["py38", "py39"]
        assert config.settings["skip-string-normalization"] is True


class TestFileChange:
    """Test FileChange data model."""

    def test_file_change_creation(self) -> None:
        """Test basic FileChange creation."""
        change = FileChange(file_path=Path("src/main.py"), had_changes=True)

        assert change.file_path == Path("src/main.py")
        assert change.had_changes is True

    def test_file_change_no_changes(self) -> None:
        """Test FileChange with no changes."""
        change = FileChange(file_path=Path("tests/test_utils.py"), had_changes=False)

        assert change.file_path == Path("tests/test_utils.py")
        assert change.had_changes is False

    def test_file_change_absolute_path(self) -> None:
        """Test FileChange with absolute path."""
        # Use a path that's absolute on current platform
        abs_path = Path.cwd() / "src" / "module.py"
        change = FileChange(file_path=abs_path, had_changes=True)

        assert change.file_path == abs_path
        assert change.file_path.is_absolute()

    def test_file_change_relative_path(self) -> None:
        """Test FileChange with relative path."""
        rel_path = Path("src/utils.py")
        change = FileChange(file_path=rel_path, had_changes=False)

        assert change.file_path == rel_path
        assert not change.file_path.is_absolute()


class TestFormatterResult:
    """Test FormatterResult data model."""

    def test_formatter_result_success(self) -> None:
        """Test successful FormatterResult."""
        changes = [
            FileChange(Path("src/main.py"), True),
            FileChange(Path("src/utils.py"), False),
        ]

        result = FormatterResult(
            success=True,
            files_changed=changes,
            execution_time_ms=1500,
            formatter_name="black",
            error_message=None,
        )

        assert result.success is True
        assert len(result.files_changed) == 2
        assert result.execution_time_ms == 1500
        assert result.formatter_name == "black"
        assert result.error_message is None

    def test_formatter_result_failure(self) -> None:
        """Test failed FormatterResult."""
        result = FormatterResult(
            success=False,
            files_changed=[],
            execution_time_ms=500,
            formatter_name="isort",
            error_message="Import sorting failed: syntax error in file.py",
        )

        assert result.success is False
        assert result.files_changed == []
        assert result.execution_time_ms == 500
        assert result.formatter_name == "isort"
        assert result.error_message == "Import sorting failed: syntax error in file.py"

    def test_formatter_result_no_changes(self) -> None:
        """Test FormatterResult with no file changes."""
        result = FormatterResult(
            success=True,
            files_changed=[],
            execution_time_ms=200,
            formatter_name="black",
            error_message=None,
        )

        assert result.success is True
        assert result.files_changed == []
        assert result.execution_time_ms == 200
        assert result.formatter_name == "black"
        assert result.error_message is None

    def test_formatter_result_multiple_changes(self) -> None:
        """Test FormatterResult with multiple file changes."""
        changes = [
            FileChange(Path("src/module1.py"), True),
            FileChange(Path("src/module2.py"), True),
            FileChange(Path("src/module3.py"), False),
            FileChange(Path("tests/test_main.py"), True),
        ]

        result = FormatterResult(
            success=True,
            files_changed=changes,
            execution_time_ms=3000,
            formatter_name="black",
            error_message=None,
        )

        assert result.success is True
        assert len(result.files_changed) == 4

        # Count files that actually had changes
        changed_files = [c for c in result.files_changed if c.had_changes]
        assert len(changed_files) == 3

        # Count files with no changes
        unchanged_files = [c for c in result.files_changed if not c.had_changes]
        assert len(unchanged_files) == 1

    def test_formatter_result_zero_execution_time(self) -> None:
        """Test FormatterResult with zero execution time."""
        result = FormatterResult(
            success=True,
            files_changed=[],
            execution_time_ms=0,
            formatter_name="isort",
            error_message=None,
        )

        assert result.execution_time_ms == 0
        assert result.success is True

    def test_formatter_result_different_formatters(self) -> None:
        """Test FormatterResult with different formatter names."""
        black_result = FormatterResult(
            success=True,
            files_changed=[FileChange(Path("main.py"), True)],
            execution_time_ms=1000,
            formatter_name="black",
            error_message=None,
        )

        isort_result = FormatterResult(
            success=True,
            files_changed=[FileChange(Path("main.py"), False)],
            execution_time_ms=500,
            formatter_name="isort",
            error_message=None,
        )

        assert black_result.formatter_name == "black"
        assert isort_result.formatter_name == "isort"
        assert black_result.execution_time_ms != isort_result.execution_time_ms


class TestDataModelIntegration:
    """Test integration between data models."""

    def test_config_to_result_workflow(self) -> None:
        """Test typical workflow from config to result."""
        # Create a configuration
        config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88},
            target_directories=[Path("src")],
            project_root=Path("/project"),
        )

        # Create file changes that might result from this config
        changes = [
            FileChange(Path("src/main.py"), True),
            FileChange(Path("src/utils.py"), False),
        ]

        # Create a result using the same formatter name
        result = FormatterResult(
            success=True,
            files_changed=changes,
            execution_time_ms=1200,
            formatter_name=config.tool_name,  # Should match
            error_message=None,
        )

        assert result.formatter_name == config.tool_name
        assert len(result.files_changed) == 2
        assert result.success is True

    def test_multiple_formatters_integration(self) -> None:
        """Test integration with multiple formatters."""
        # Black configuration
        black_config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88},
            target_directories=[Path("src")],
            project_root=Path("/project"),
        )

        # isort configuration
        isort_config = FormatterConfig(
            tool_name="isort",
            settings={"profile": "black"},
            target_directories=[Path("src")],
            project_root=Path("/project"),
        )

        # Results from both formatters
        black_changes = [FileChange(Path("src/main.py"), True)]
        isort_changes = [FileChange(Path("src/main.py"), False)]

        black_result = FormatterResult(
            success=True,
            files_changed=black_changes,
            execution_time_ms=1000,
            formatter_name=black_config.tool_name,
            error_message=None,
        )

        isort_result = FormatterResult(
            success=True,
            files_changed=isort_changes,
            execution_time_ms=800,
            formatter_name=isort_config.tool_name,
            error_message=None,
        )

        # Verify both results are independent but consistent
        assert black_result.formatter_name == "black"
        assert isort_result.formatter_name == "isort"
        assert (
            black_result.files_changed[0].file_path
            == isort_result.files_changed[0].file_path
        )
        assert (
            black_result.files_changed[0].had_changes
            != isort_result.files_changed[0].had_changes
        )

    def test_error_scenarios_integration(self) -> None:
        """Test error scenarios across data models."""
        config = FormatterConfig(
            tool_name="black",
            settings={"invalid-option": "bad-value"},
            target_directories=[Path("nonexistent")],
            project_root=Path("/missing"),
        )

        # Result representing a failure
        result = FormatterResult(
            success=False,
            files_changed=[],
            execution_time_ms=100,
            formatter_name=config.tool_name,
            error_message="Configuration error: invalid-option is not recognized",
        )

        assert result.success is False
        assert result.formatter_name == config.tool_name
        assert result.error_message is not None
        assert "Configuration error" in result.error_message
        assert len(result.files_changed) == 0
