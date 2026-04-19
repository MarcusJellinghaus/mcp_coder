"""Tests for Copilot CLI log path generation."""

from pathlib import Path

from mcp_coder.llm.providers.copilot.copilot_cli_log_paths import get_stream_log_path


class TestCopilotStreamLogPath:
    """Tests for get_stream_log_path."""

    def test_default_path_uses_copilot_sessions_subdir(self, tmp_path: Path) -> None:
        """Verify path contains copilot-sessions/ (not claude-sessions/)."""
        result = get_stream_log_path(logs_dir=str(tmp_path))
        assert "copilot-sessions" in str(result)
        assert "claude-sessions" not in str(result)

    def test_path_with_branch_name(self, tmp_path: Path) -> None:
        """Verify branch identifier appears in filename."""
        result = get_stream_log_path(
            logs_dir=str(tmp_path), branch_name="feature/my-branch"
        )
        assert "feature" in result.name

    def test_path_without_branch_name(self, tmp_path: Path) -> None:
        """Verify filename has no trailing identifier when no branch given."""
        result = get_stream_log_path(logs_dir=str(tmp_path))
        # Format: session_YYYYMMDD_HHMMSS_NNNNNN.ndjson (no branch part)
        stem = result.stem
        parts = stem.split("_")
        # session + date + time + microseconds = 4 parts
        assert len(parts) == 4

    def test_path_with_custom_logs_dir(self, tmp_path: Path) -> None:
        """Verify custom logs_dir is respected."""
        custom_dir = tmp_path / "custom-logs"
        result = get_stream_log_path(logs_dir=str(custom_dir))
        assert str(custom_dir) in str(result)

    def test_directory_is_created(self, tmp_path: Path) -> None:
        """Verify session directory is created."""
        logs_dir = tmp_path / "new-logs"
        result = get_stream_log_path(logs_dir=str(logs_dir))
        assert result.parent.exists()
        assert result.parent.name == "copilot-sessions"

    def test_ndjson_extension(self, tmp_path: Path) -> None:
        """Verify file ends with .ndjson."""
        result = get_stream_log_path(logs_dir=str(tmp_path))
        assert result.suffix == ".ndjson"

    def test_path_with_cwd(self, tmp_path: Path) -> None:
        """Verify cwd parameter creates logs subdirectory."""
        result = get_stream_log_path(cwd=str(tmp_path))
        assert "logs" in str(result)
        assert "copilot-sessions" in str(result)
