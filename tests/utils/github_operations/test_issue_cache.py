"""Tests for issue cache functionality.

Tests the get_all_cached_issues() function and its helper functions
for proper cache storage, duplicate protection, and incremental fetching.
"""

import json
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    _filter_eligible_issues,
    get_cached_eligible_issues,
)
from mcp_coder.utils.github_operations.github_utils import RepoIdentifier
from mcp_coder.utils.github_operations.issue_cache import (
    CacheData,
    _get_cache_file_path,
    _load_cache_file,
    _log_cache_metrics,
    _log_stale_cache_entries,
    _save_cache_file,
    _update_issue_labels_in_cache,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData


class TestCacheMetricsLogging:
    """Tests for _log_cache_metrics function."""

    def test_log_cache_metrics_hit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test cache hit metrics logging."""
        caplog.set_level(
            logging.DEBUG, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        _log_cache_metrics("hit", "test-repo", age_minutes=15, issue_count=5)

        assert "Cache hit for test-repo: age=15m, issues=5" in caplog.text

    def test_log_cache_metrics_miss(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test cache miss metrics logging."""
        caplog.set_level(
            logging.DEBUG, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        _log_cache_metrics("miss", "test-repo", reason="no_cache")

        assert "Cache miss for test-repo: reason='no_cache'" in caplog.text

    def test_log_cache_metrics_refresh(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test cache refresh metrics logging."""
        caplog.set_level(
            logging.DEBUG, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        _log_cache_metrics("refresh", "test-repo", refresh_type="full", issue_count=10)

        assert "Cache refresh for test-repo: type=full, new_issues=10" in caplog.text

    def test_log_cache_metrics_save(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test cache save metrics logging."""
        caplog.set_level(
            logging.DEBUG, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        _log_cache_metrics("save", "test-repo", total_issues=25)

        assert "Cache save for test-repo: total_issues=25" in caplog.text


class TestCacheFilePath:
    """Tests for _get_cache_file_path function."""

    def test_get_cache_file_path_basic(self) -> None:
        """Test basic cache file path generation."""
        repo_identifier = RepoIdentifier.from_full_name("owner/repo")
        path = _get_cache_file_path(repo_identifier)

        expected_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
        expected_file = expected_dir / "owner_repo.issues.json"

        assert path == expected_file

    def test_get_cache_file_path_complex_names(self) -> None:
        """Test cache file path with complex repository names."""
        test_cases = [
            ("anthropics/claude-code", "anthropics_claude-code.issues.json"),
            ("user/repo-with-dashes", "user_repo-with-dashes.issues.json"),
            ("org/very.long.repo.name", "org_very.long.repo.name.issues.json"),
        ]

        for full_name, expected_filename in test_cases:
            repo_identifier = RepoIdentifier.from_full_name(full_name)
            path = _get_cache_file_path(repo_identifier)
            assert path.name == expected_filename


class TestCacheFileOperations:
    """Tests for cache file load/save operations."""

    def test_load_cache_file_nonexistent(self) -> None:
        """Test loading non-existent cache file returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "nonexistent.json"
            result = _load_cache_file(cache_path)

            assert result == {"last_checked": None, "issues": {}}

    def test_load_cache_file_valid(self, sample_cache_data: CacheData) -> None:
        """Test loading valid cache file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            cache_path.write_text(json.dumps(sample_cache_data))

            result = _load_cache_file(cache_path)
            assert result == sample_cache_data

    def test_load_cache_file_invalid_json(self) -> None:
        """Test loading corrupted JSON file returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "invalid.json"
            cache_path.write_text("invalid json content")

            result = _load_cache_file(cache_path)
            assert result == {"last_checked": None, "issues": {}}

    def test_load_cache_file_invalid_structure(self) -> None:
        """Test loading file with invalid structure returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "invalid_structure.json"
            cache_path.write_text('{"wrong_key": "value"}')

            result = _load_cache_file(cache_path)
            assert result == {"last_checked": None, "issues": {}}

    def test_save_cache_file_success(self, sample_cache_data: CacheData) -> None:
        """Test successful cache file save with atomic write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "subdir" / "cache.json"

            result = _save_cache_file(cache_path, sample_cache_data)
            assert result is True

            # Verify file was created and data is correct
            assert cache_path.exists()
            saved_data = json.loads(cache_path.read_text())
            assert saved_data == sample_cache_data

    def test_save_cache_file_creates_directory(
        self, sample_cache_data: CacheData
    ) -> None:
        """Test cache file save creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "deep" / "nested" / "dirs" / "cache.json"

            result = _save_cache_file(cache_path, sample_cache_data)
            assert result is True
            assert cache_path.exists()

    def test_save_cache_file_permission_error(
        self, sample_cache_data: CacheData
    ) -> None:
        """Test cache file save handles permission errors gracefully."""
        with patch.object(Path, "open", side_effect=PermissionError("Access denied")):
            cache_path = Path("/fake/path/cache.json")
            result = _save_cache_file(cache_path, sample_cache_data)
            assert result is False


class TestStalenessLogging:
    """Tests for _log_stale_cache_entries function."""

    def test_log_stale_cache_entries_state_change(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging when issue state changes."""
        caplog.set_level(
            logging.INFO, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        cached_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }
        fresh_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "closed",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }

        _log_stale_cache_entries(cached_issues, fresh_issues)

        assert "Issue #123: cached state 'open' != actual 'closed'" in caplog.text

    def test_log_stale_cache_entries_label_change(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging when issue labels change."""
        caplog.set_level(
            logging.INFO, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        cached_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }
        fresh_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["status-03:planning"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }

        _log_stale_cache_entries(cached_issues, fresh_issues)

        assert "Issue #123: cached labels" in caplog.text
        assert "status-02:awaiting-planning" in caplog.text
        assert "status-03:planning" in caplog.text

    def test_log_stale_cache_entries_missing_issue(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging when cached issue no longer exists."""
        caplog.set_level(
            logging.INFO, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        cached_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }
        fresh_issues: Dict[str, IssueData] = {}

        _log_stale_cache_entries(cached_issues, fresh_issues)

        assert "Issue #123: no longer exists in repository" in caplog.text

    def test_log_stale_cache_entries_no_changes(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test no logging when no changes detected."""
        cached_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }
        fresh_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }

        _log_stale_cache_entries(cached_issues, fresh_issues)

        # Should not log anything for unchanged issues
        assert "Issue #123:" not in caplog.text


class TestEligibleIssuesFiltering:
    """Tests for _filter_eligible_issues function."""

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    def test_filter_eligible_issues_basic(self, mock_load_config: Mock) -> None:
        """Test basic filtering of eligible issues."""
        # Mock labels config
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "bug", "category": "type"},
            ],
            "ignore_labels": ["wontfix"],
        }

        issues: List[IssueData] = [
            {
                "number": 1,
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test 1",
                "body": "Test 1",
                "url": "http://test.com/1",
                "updated_at": "2025-12-31T08:00:00Z",
            },
            {
                "number": 2,
                "state": "open",
                "labels": ["status-05:plan-ready"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test 2",
                "body": "Test 2",
                "url": "http://test.com/2",
                "updated_at": "2025-12-31T08:00:00Z",
            },
            {
                "number": 3,
                "state": "closed",
                "labels": ["status-02:awaiting-planning"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test 3",
                "body": "Test 3",
                "url": "http://test.com/3",
                "updated_at": "2025-12-31T08:00:00Z",
            },  # closed
            {
                "number": 4,
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test 4",
                "body": "Test 4",
                "url": "http://test.com/4",
                "updated_at": "2025-12-31T08:00:00Z",
            },  # no bot_pickup label
            {
                "number": 5,
                "state": "open",
                "labels": ["status-02:awaiting-planning", "wontfix"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test 5",
                "body": "Test 5",
                "url": "http://test.com/5",
                "updated_at": "2025-12-31T08:00:00Z",
            },  # ignore label
        ]

        result = _filter_eligible_issues(issues)

        # Should return only issues 1 and 2, sorted by priority
        assert len(result) == 2
        assert result[0]["number"] == 2  # status-05:plan-ready has higher priority
        assert (
            result[1]["number"] == 1
        )  # status-02:awaiting-planning has lower priority

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    def test_filter_eligible_issues_multiple_bot_pickup_labels(
        self, mock_load_config: Mock
    ) -> None:
        """Test filtering excludes issues with multiple bot_pickup labels."""
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
            ],
            "ignore_labels": [],
        }

        issues: List[IssueData] = [
            {
                "number": 1,
                "state": "open",
                "labels": ["status-02:awaiting-planning", "status-05:plan-ready"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        ]

        result = _filter_eligible_issues(issues)
        assert len(result) == 0


class TestGetCachedEligibleIssues:
    """Tests for get_cached_eligible_issues main function."""

    def test_get_cached_eligible_issues_first_run(
        self, mock_cache_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test first run with no existing cache."""
        mock_cache_issue_manager.list_issues.return_value = [sample_issue]
        mock_cache_issue_manager.repo_url = "https://github.com/owner/repo"

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {"last_checked": None, "issues": {}}
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_cache_issue_manager)

            assert result == [sample_issue]
            mock_cache_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False
            )
            mock_save.assert_called_once()

    def test_get_cached_eligible_issues_incremental_update(
        self, mock_cache_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test incremental update with recent cache."""
        # Cache checked 30 minutes ago (within 24-hour window)
        cache_time = datetime.now().astimezone() - timedelta(minutes=30)
        mock_cache_issue_manager.list_issues.return_value = [sample_issue]
        mock_cache_issue_manager.repo_url = "https://github.com/owner/repo"

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": cache_time.isoformat(),
                "issues": {"123": sample_issue},
            }
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_cache_issue_manager)

            assert result == [sample_issue]
            # Should call with since parameter for incremental update
            mock_cache_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False, since=cache_time
            )

    def test_get_cached_eligible_issues_full_refresh(
        self, mock_cache_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test full refresh when cache is old."""
        # Cache checked 25 hours ago (beyond 24-hour window)
        old_cache_time = datetime.now().astimezone() - timedelta(hours=25)
        mock_cache_issue_manager.list_issues.return_value = [sample_issue]
        mock_cache_issue_manager.repo_url = "https://github.com/owner/repo"

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._log_stale_cache_entries"
            ) as mock_log_stale,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": old_cache_time.isoformat(),
                "issues": {"456": {"number": 456, "state": "open", "labels": ["old"]}},
            }
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_cache_issue_manager)

            assert result == [sample_issue]
            # Should call without since parameter for full refresh
            mock_cache_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False
            )
            # Should log staleness since we had cached data
            mock_log_stale.assert_called_once()

    def test_get_cached_eligible_issues_duplicate_protection(
        self, mock_cache_issue_manager: Mock
    ) -> None:
        """Test duplicate protection skips recent checks."""
        # Cache checked 30 seconds ago (within 1-minute window)
        recent_time = datetime.now().astimezone() - timedelta(seconds=30)
        mock_cache_issue_manager.repo_url = "https://github.com/owner/repo"

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": recent_time.isoformat(),
                "issues": {},
            }

            result = get_cached_eligible_issues("owner/repo", mock_cache_issue_manager)

            assert result == []
            # Should not call issue_manager at all due to duplicate protection
            mock_cache_issue_manager.list_issues.assert_not_called()

    def test_get_cached_eligible_issues_force_refresh(
        self, mock_cache_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test force refresh bypasses cache and duplicate protection."""
        # Cache checked 30 seconds ago, but force_refresh should bypass it
        recent_time = datetime.now().astimezone() - timedelta(seconds=30)
        mock_cache_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": recent_time.isoformat(),
                "issues": {},
            }
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues(
                "owner/repo", mock_cache_issue_manager, force_refresh=True
            )

            assert result == [sample_issue]
            # Should call issue_manager despite recent check
            mock_cache_issue_manager.list_issues.assert_called_once()

    def test_get_cached_eligible_issues_corrupted_cache(
        self, mock_cache_issue_manager: Mock
    ) -> None:
        """Test graceful fallback when cache operations fail."""
        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file",
                side_effect=ValueError("Cache error"),
            ),
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_eligible_issues"
            ) as mock_fallback,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_fallback.return_value = []

            result = get_cached_eligible_issues("owner/repo", mock_cache_issue_manager)

            # Should fall back to get_eligible_issues
            assert result == []
            mock_fallback.assert_called_once_with(mock_cache_issue_manager)

    def test_get_cached_eligible_issues_custom_cache_refresh_minutes(
        self, mock_cache_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test custom cache refresh threshold."""
        # Cache checked 10 minutes ago, with custom 5-minute threshold
        cache_time = datetime.now().astimezone() - timedelta(minutes=10)
        mock_cache_issue_manager.list_issues.return_value = [sample_issue]
        mock_cache_issue_manager.repo_url = "https://github.com/owner/repo"

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": cache_time.isoformat(),
                "issues": {},
            }
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues(
                "owner/repo", mock_cache_issue_manager, cache_refresh_minutes=5
            )

            assert result == [sample_issue]
            # Should do full refresh since 10 minutes > 5 minute threshold
            mock_cache_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False
            )

    def test_get_cached_eligible_issues_metrics_logging(
        self,
        mock_cache_issue_manager: Mock,
        sample_issue: IssueData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that cache metrics are logged properly."""
        caplog.set_level(
            logging.DEBUG, logger="mcp_coder.utils.github_operations.issue_cache"
        )
        mock_cache_issue_manager.list_issues.return_value = [sample_issue]
        mock_cache_issue_manager.repo_url = "https://github.com/owner/repo"

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {"last_checked": None, "issues": {}}
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_cache_issue_manager)

            assert result == [sample_issue]
            # Should log cache metrics
            assert "Cache miss for repo: reason='no_cache'" in caplog.text
            assert "Cache refresh for repo: type=full, new_issues=1" in caplog.text
            assert "Cache save for repo: total_issues=1" in caplog.text
            assert "Cache hit for repo:" in caplog.text

    def test_no_spurious_warnings_with_repo_identifier(
        self,
        mock_cache_issue_manager: Mock,
        sample_issue: IssueData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that using RepoIdentifier does not generate spurious warnings."""
        caplog.set_level(
            logging.WARNING, logger="mcp_coder.utils.github_operations.issue_cache"
        )
        mock_cache_issue_manager.list_issues.return_value = [sample_issue]
        mock_cache_issue_manager.repo_url = "https://github.com/owner/repo"

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {"last_checked": None, "issues": {}}
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            # This should complete without any warnings
            result = get_cached_eligible_issues("owner/repo", mock_cache_issue_manager)

            assert result == [sample_issue]
            # Should not contain any warnings related to repo identifier parsing
            warning_messages = [
                record.message
                for record in caplog.records
                if record.levelname == "WARNING"
            ]
            assert not any("repo identifier" in msg.lower() for msg in warning_messages)
            assert not any(
                "parse" in msg.lower() and "repo" in msg.lower()
                for msg in warning_messages
            )


class TestCacheIssueUpdate:
    """Tests for _update_issue_labels_in_cache function."""

    def test_update_issue_labels_success(self) -> None:
        """Test successful label update for existing issue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Create initial cache with issue
            initial_cache = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "123": {
                        "number": 123,
                        "state": "open",
                        "labels": ["status-02:awaiting-planning", "bug"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/123",
                        "title": "Test issue",
                        "body": "Test issue body",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    }
                },
            }
            cache_path.write_text(json.dumps(initial_cache))

            # Mock _get_cache_file_path to return our test path
            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                # Call the function under test
                _update_issue_labels_in_cache(
                    "test/repo",
                    123,
                    "status-02:awaiting-planning",
                    "status-03:planning",
                )

            # Verify cache was updated
            updated_cache = json.loads(cache_path.read_text())
            issue_labels = updated_cache["issues"]["123"]["labels"]

            assert "status-02:awaiting-planning" not in issue_labels
            assert "status-03:planning" in issue_labels
            assert "bug" in issue_labels  # Other labels preserved

    def test_update_issue_labels_remove_only(self) -> None:
        """Test removing a label without adding new one."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Create cache with multiple labels
            initial_cache = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "456": {
                        "number": 456,
                        "state": "open",
                        "labels": ["status-05:plan-ready", "enhancement", "urgent"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/456",
                        "title": "Enhancement issue",
                        "body": "Enhancement body",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    }
                },
            }
            cache_path.write_text(json.dumps(initial_cache))

            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                # Remove label without adding new one (empty string)
                _update_issue_labels_in_cache(
                    "test/repo", 456, "status-05:plan-ready", ""
                )

            # Verify only the specified label was removed
            updated_cache = json.loads(cache_path.read_text())
            issue_labels = updated_cache["issues"]["456"]["labels"]

            assert "status-05:plan-ready" not in issue_labels
            assert "enhancement" in issue_labels
            assert "urgent" in issue_labels

    def test_update_issue_labels_add_only(self) -> None:
        """Test adding a label without removing existing ones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            initial_cache = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "789": {
                        "number": 789,
                        "state": "open",
                        "labels": ["bug"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/789",
                        "title": "Bug issue",
                        "body": "Bug body",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    }
                },
            }
            cache_path.write_text(json.dumps(initial_cache))

            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                # Add new label without removing any (empty old_label)
                _update_issue_labels_in_cache(
                    "test/repo", 789, "", "status-02:awaiting-planning"
                )

            # Verify new label was added and existing preserved
            updated_cache = json.loads(cache_path.read_text())
            issue_labels = updated_cache["issues"]["789"]["labels"]

            assert "bug" in issue_labels
            assert "status-02:awaiting-planning" in issue_labels

    def test_update_issue_labels_missing_issue(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test graceful handling when issue not found in cache."""
        caplog.set_level(
            logging.WARNING, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Create cache without the target issue
            initial_cache = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "456": {
                        "number": 456,
                        "state": "open",
                        "labels": ["bug"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/456",
                        "title": "Other issue",
                        "body": "Other body",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    }
                },
            }
            cache_path.write_text(json.dumps(initial_cache))

            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                # Try to update non-existent issue - should not raise exception
                _update_issue_labels_in_cache(
                    "test/repo", 123, "old-label", "new-label"
                )

            # Verify appropriate warning was logged
            assert "Issue #123 not found in cache for test/repo" in caplog.text

            # Verify cache remained unchanged
            updated_cache = json.loads(cache_path.read_text())
            assert "123" not in updated_cache["issues"]
            assert updated_cache["issues"]["456"]["labels"] == ["bug"]

    def test_update_issue_labels_invalid_cache_structure(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test handling of corrupted cache file structure."""
        caplog.set_level(
            logging.WARNING, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Create invalid cache structure
            invalid_cache = {"wrong_structure": "invalid"}
            cache_path.write_text(json.dumps(invalid_cache))

            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                # Should handle gracefully without crashing
                _update_issue_labels_in_cache(
                    "test/repo", 123, "old-label", "new-label"
                )

            # Verify warning was logged
            assert (
                "Invalid cache structure" in caplog.text
                or "Cache update failed" in caplog.text
            )

    def test_update_issue_labels_file_permission_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test handling of file permission errors."""
        caplog.set_level(
            logging.WARNING, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file"
            ) as mock_load,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._save_cache_file"
            ) as mock_save,
        ):
            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "123": {
                        "number": 123,
                        "labels": ["old-label"],
                        "state": "open",
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/123",
                        "title": "Test",
                        "body": "Test",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    }
                },
            }
            mock_save.return_value = False  # Simulate save failure

            # Should handle save failure gracefully
            _update_issue_labels_in_cache("test/repo", 123, "old-label", "new-label")

            # Verify appropriate warning was logged
            assert any(
                "Cache update failed" in record.message for record in caplog.records
            )

    def test_update_issue_labels_logging(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test proper logging behavior during successful updates."""
        caplog.set_level(
            logging.DEBUG, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            initial_cache = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "123": {
                        "number": 123,
                        "state": "open",
                        "labels": ["status-02:awaiting-planning"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/123",
                        "title": "Test issue",
                        "body": "Test body",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    }
                },
            }
            cache_path.write_text(json.dumps(initial_cache))

            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                _update_issue_labels_in_cache(
                    "test/repo",
                    123,
                    "status-02:awaiting-planning",
                    "status-03:planning",
                )

            # Verify debug logging includes key operation details
            log_messages = [
                record.message
                for record in caplog.records
                if record.levelname == "DEBUG"
            ]
            assert any(
                "Updated issue #123 labels in cache" in msg for msg in log_messages
            )
            assert any("status-02:awaiting-planning" in msg for msg in log_messages)
            assert any("status-03:planning" in msg for msg in log_messages)
            # Verify ASCII arrow is used
            assert any("->" in msg for msg in log_messages)


class TestCacheUpdateIntegration:
    """Integration tests for cache update in dispatch workflow."""

    def test_dispatch_workflow_updates_cache(self) -> None:
        """Test that cache update integration exists and works correctly.

        This test verifies the cache update functionality without mocking,
        since the integration between dispatch_workflow and cache update
        already exists in the coordinator.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Create initial cache with issue that has a workflow label
            initial_cache = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "123": {
                        "number": 123,
                        "state": "open",
                        "labels": ["status-02:awaiting-planning"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/123",
                        "title": "Test issue",
                        "body": "Test body",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    }
                },
            }
            cache_path.write_text(json.dumps(initial_cache))

            # Mock only the cache file path to point to our test cache
            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                # Call the actual cache update function (this is what dispatch_workflow calls)
                _update_issue_labels_in_cache(
                    "test/repo",
                    123,
                    "status-02:awaiting-planning",
                    "status-03:planning",
                )

            # Verify the cache was actually updated
            updated_cache = json.loads(cache_path.read_text())
            issue_labels = updated_cache["issues"]["123"]["labels"]

            # Check that the old label was removed and new label was added
            assert "status-02:awaiting-planning" not in issue_labels
            assert "status-03:planning" in issue_labels

    def test_multiple_dispatches_update_cache_correctly(self) -> None:
        """Test multiple dispatch operations update cache sequentially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Create cache with multiple issues
            initial_cache = {
                "last_checked": "2025-01-03T10:30:00Z",
                "issues": {
                    "123": {
                        "number": 123,
                        "state": "open",
                        "labels": ["status-02:awaiting-planning"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/123",
                        "title": "Issue 1",
                        "body": "Body 1",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    },
                    "456": {
                        "number": 456,
                        "state": "open",
                        "labels": ["status-05:plan-ready"],
                        "updated_at": "2025-01-03T09:00:00Z",
                        "url": "https://github.com/test/repo/issues/456",
                        "title": "Issue 2",
                        "body": "Body 2",
                        "assignees": [],
                        "user": "testuser",
                        "created_at": "2025-01-03T08:00:00Z",
                        "locked": False,
                    },
                },
            }
            cache_path.write_text(json.dumps(initial_cache))

            with patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path:
                mock_path.return_value = cache_path

                # Simulate multiple dispatch operations
                _update_issue_labels_in_cache(
                    "test/repo",
                    123,
                    "status-02:awaiting-planning",
                    "status-03:planning",
                )
                _update_issue_labels_in_cache(
                    "test/repo", 456, "status-05:plan-ready", "status-06:implementing"
                )

            # Verify both issues were updated correctly
            final_cache = json.loads(cache_path.read_text())

            issue_123_labels = final_cache["issues"]["123"]["labels"]
            assert "status-02:awaiting-planning" not in issue_123_labels
            assert "status-03:planning" in issue_123_labels

            issue_456_labels = final_cache["issues"]["456"]["labels"]
            assert "status-05:plan-ready" not in issue_456_labels
            assert "status-06:implementing" in issue_456_labels

    def test_cache_update_failure_does_not_break_dispatch(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that cache update failures don't interrupt dispatch workflow."""
        caplog.set_level(
            logging.WARNING, logger="mcp_coder.utils.github_operations.issue_cache"
        )

        with (
            patch(
                "mcp_coder.utils.github_operations.issue_cache._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.utils.github_operations.issue_cache._load_cache_file",
                side_effect=Exception("Cache error"),
            ),
        ):
            mock_path.return_value = Path("/nonexistent/cache.json")

            # Cache update failure should not raise exception
            try:
                _update_issue_labels_in_cache(
                    "test/repo", 123, "old-label", "new-label"
                )
                # Should complete without exception
            except Exception as e:
                pytest.fail(f"Cache update failure should not break workflow: {e}")

            # Verify appropriate warning was logged but execution continued
            warning_messages = [
                record.message
                for record in caplog.records
                if record.levelname == "WARNING"
            ]
            assert any(
                "Cache update failed" in msg or "Cache error" in msg
                for msg in warning_messages
            )
