"""Tests for FormatterResult dataclass using TDD approach."""

import pytest

from mcp_coder.formatters.models import FormatterResult


@pytest.mark.formatter_integration
class TestFormatterResult:
    """Test FormatterResult dataclass creation scenarios."""

    def test_success_with_changes(self) -> None:
        """Test FormatterResult creation for successful formatting with changes."""
        result = FormatterResult(
            success=True,
            files_changed=["src/module.py", "tests/test_module.py"],
            formatter_name="black",
        )

        assert result.success is True
        assert result.files_changed == ["src/module.py", "tests/test_module.py"]
        assert result.formatter_name == "black"
        assert result.error_message is None

    def test_failure_with_error(self) -> None:
        """Test FormatterResult creation for failed formatting with error."""
        result = FormatterResult(
            success=False,
            files_changed=[],
            formatter_name="isort",
            error_message="syntax error in file.py",
        )

        assert result.success is False
        assert result.files_changed == []
        assert result.formatter_name == "isort"
        assert result.error_message == "syntax error in file.py"

    def test_success_no_changes(self) -> None:
        """Test FormatterResult creation for successful formatting with no changes."""
        result = FormatterResult(success=True, files_changed=[], formatter_name="black")

        assert result.success is True
        assert result.files_changed == []
        assert result.formatter_name == "black"
        assert result.error_message is None

    def test_subprocess_integration_pattern(self) -> None:
        """Test FormatterResult supports subprocess.CompletedProcess integration patterns."""
        # Simulate patterns from Step 0 analysis - exit code 0 = success, no changes
        result_no_changes = FormatterResult(
            success=True,  # exit code 0
            files_changed=[],  # no changes detected
            formatter_name="black",
        )

        # Simulate exit code 1 = success with changes
        result_with_changes = FormatterResult(
            success=True,  # exit code 1 in black means changes made
            files_changed=["file.py"],  # changes detected
            formatter_name="black",
        )

        # Simulate exit code > 1 = failure
        result_failure = FormatterResult(
            success=False,  # exit code > 1
            files_changed=[],
            formatter_name="black",
            error_message="subprocess failed",
        )

        assert result_no_changes.success is True
        assert len(result_no_changes.files_changed) == 0

        assert result_with_changes.success is True
        assert len(result_with_changes.files_changed) == 1

        assert result_failure.success is False
        assert result_failure.error_message is not None
