import json
import logging
import tempfile
from pathlib import Path

import pytest

from mcp_coder.mcp_workspace_github import (
    CacheData,
    IssueData,
    get_cache_file_path,
    load_cache_file,
    log_stale_cache_entries,
    save_cache_file,
)
from tests.github_factories import make_issue_data


class TestCacheFilePath:
    """Tests for get_cache_file_path function."""

    def test_get_cache_file_path_basic(self) -> None:
        """Test basic cache file path generation."""
        from mcp_coder.mcp_workspace_github import RepoIdentifier

        repo_identifier = RepoIdentifier.from_full_name("owner/repo")
        path = get_cache_file_path(repo_identifier)

        expected_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
        expected_file = expected_dir / "github_com_owner_repo.issues.json"

        assert path == expected_file

    def test_get_cache_file_path_complex_names(self) -> None:
        """Test cache file path with complex repository names."""
        from mcp_coder.mcp_workspace_github import RepoIdentifier

        test_cases = [
            (
                "anthropics/claude-code",
                "github_com_anthropics_claude-code.issues.json",
            ),
            (
                "user/repo-with-dashes",
                "github_com_user_repo-with-dashes.issues.json",
            ),
            (
                "org/very.long.repo.name",
                "github_com_org_very.long.repo.name.issues.json",
            ),
        ]

        for full_name, expected_filename in test_cases:
            repo_identifier = RepoIdentifier.from_full_name(full_name)
            path = get_cache_file_path(repo_identifier)
            assert path.name == expected_filename


class TestCacheFileOperations:
    """Tests for cache file load/save operations."""

    def test_load_cache_file_nonexistent(self) -> None:
        """Test loading non-existent cache file returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "nonexistent.json"
            result = load_cache_file(cache_path)

            # Assert on the keys of interest rather than exact full-dict
            # equality so the tests tolerate additive schema changes in the
            # external mcp_workspace cache structure.
            assert result["last_checked"] is None
            assert result["last_full_refresh"] is None
            assert result["issues"] == {}

    def test_load_cache_file_valid(self) -> None:
        """Test loading valid cache file."""
        sample_cache_data = {
            "last_checked": "2025-12-31T10:30:00Z",
            "issues": {
                "123": make_issue_data(
                    number=123,
                    labels=["status-02:awaiting-planning"],
                    updated_at="2025-12-31T09:00:00Z",
                    url="https://github.com/test/repo/issues/123",
                    title="Test issue",
                    body="Test issue body",
                    user="testuser",
                    created_at="2025-12-31T08:00:00Z",
                )
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            cache_path.write_text(json.dumps(sample_cache_data))

            result = load_cache_file(cache_path)
            # Assert on the keys of interest rather than exact full-dict
            # equality so the tests tolerate additive schema changes in the
            # external mcp_workspace cache structure.
            # Loaded cache gains last_full_refresh=None when not in file.
            assert result["last_checked"] == sample_cache_data["last_checked"]
            assert result["last_full_refresh"] is None
            assert result["issues"] == sample_cache_data["issues"]

    def test_load_cache_file_invalid_json(self) -> None:
        """Test loading corrupted JSON file returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "invalid.json"
            cache_path.write_text("invalid json content")

            result = load_cache_file(cache_path)
            # Assert on the keys of interest rather than exact full-dict
            # equality so the tests tolerate additive schema changes in the
            # external mcp_workspace cache structure.
            assert result["last_checked"] is None
            assert result["last_full_refresh"] is None
            assert result["issues"] == {}

    def test_save_cache_file_success(self) -> None:
        """Test successful cache file save with atomic write."""
        sample_cache_data: CacheData = {
            "last_checked": "2025-12-31T10:30:00Z",
            "issues": {
                "123": make_issue_data(
                    number=123,
                    labels=["bug"],
                    title="Test issue",
                    body="Test issue body",
                    user="testuser",
                    created_at="2025-12-31T08:00:00Z",
                    updated_at="2025-12-31T09:00:00Z",
                    url="https://github.com/test/repo/issues/123",
                )
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "subdir" / "cache.json"

            result = save_cache_file(cache_path, sample_cache_data)
            assert result is True

            # Verify file was created and data is correct
            assert cache_path.exists()
            saved_data = json.loads(cache_path.read_text())
            assert saved_data == sample_cache_data


class TestStalenessLogging:
    """Tests for log_stale_cache_entries function."""

    def test_log_stale_cache_entries_state_change(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging when issue state changes."""
        caplog.set_level(
            logging.INFO, logger="mcp_workspace.github_operations.issues.cache"
        )

        cached_issues: dict[str, IssueData] = {
            "123": make_issue_data(
                number=123,
                labels=["bug"],
                user="testuser",
                created_at="2025-12-31T08:00:00Z",
                title="Test",
                body="Test",
                url="http://test.com",
                updated_at="2025-12-31T08:00:00Z",
            )
        }
        fresh_issues: dict[str, IssueData] = {
            "123": make_issue_data(
                number=123,
                state="closed",
                labels=["bug"],
                user="testuser",
                created_at="2025-12-31T08:00:00Z",
                title="Test",
                body="Test",
                url="http://test.com",
                updated_at="2025-12-31T08:00:00Z",
            )
        }

        log_stale_cache_entries(cached_issues, fresh_issues)

        assert "Issue #123: cached state 'open' != actual 'closed'" in caplog.text

    def test_log_stale_cache_entries_label_change(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging when issue labels change."""
        caplog.set_level(
            logging.INFO, logger="mcp_workspace.github_operations.issues.cache"
        )

        cached_issues: dict[str, IssueData] = {
            "123": make_issue_data(
                number=123,
                labels=["status-02:awaiting-planning"],
                user="testuser",
                created_at="2025-12-31T08:00:00Z",
                title="Test",
                body="Test",
                url="http://test.com",
                updated_at="2025-12-31T08:00:00Z",
            )
        }
        fresh_issues: dict[str, IssueData] = {
            "123": make_issue_data(
                number=123,
                labels=["status-03:planning"],
                user="testuser",
                created_at="2025-12-31T08:00:00Z",
                title="Test",
                body="Test",
                url="http://test.com",
                updated_at="2025-12-31T08:00:00Z",
            )
        }

        log_stale_cache_entries(cached_issues, fresh_issues)

        assert "Issue #123: cached labels" in caplog.text
        assert "status-02:awaiting-planning" in caplog.text
        assert "status-03:planning" in caplog.text
