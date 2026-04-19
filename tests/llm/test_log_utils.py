"""Tests for shared LLM log utilities."""

from mcp_coder.llm.log_utils import DEFAULT_LOGS_DIR, sanitize_branch_identifier


class TestSanitizeBranchIdentifier:
    """Tests for sanitize_branch_identifier at the canonical location."""

    def test_sanitize_branch_identifier_simple(self) -> None:
        """Simple branch name passes through."""
        assert sanitize_branch_identifier("main") == "main"

    def test_sanitize_branch_identifier_slashes(self) -> None:
        """Slashes are handled — first part extracted."""
        assert sanitize_branch_identifier("feature/foo") == "feature"

    def test_sanitize_branch_identifier_special_chars(self) -> None:
        """Non-alphanumeric characters are stripped."""
        result = sanitize_branch_identifier("feat@#$/bar")
        assert result == "feat"

    def test_sanitize_branch_identifier_numeric_issue_id(self) -> None:
        """Numeric issue IDs at start are preferred."""
        assert sanitize_branch_identifier("123-feature-name") == "123"

    def test_sanitize_branch_identifier_none(self) -> None:
        """None returns empty string."""
        assert sanitize_branch_identifier(None) == ""

    def test_sanitize_branch_identifier_empty(self) -> None:
        """Empty string returns empty string."""
        assert sanitize_branch_identifier("") == ""

    def test_sanitize_branch_identifier_head(self) -> None:
        """HEAD returns empty string."""
        assert sanitize_branch_identifier("HEAD") == ""


class TestDefaultLogsDir:
    """Tests for DEFAULT_LOGS_DIR constant."""

    def test_default_logs_dir_value(self) -> None:
        """DEFAULT_LOGS_DIR should be 'logs'."""
        assert DEFAULT_LOGS_DIR == "logs"
