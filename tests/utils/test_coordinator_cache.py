"""Tests for coordinator caching functionality.

Tests the get_cached_eligible_issues() function and its helper functions
for proper cache storage, duplicate protection, and incremental fetching.
"""

import json
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    _filter_eligible_issues,
    _get_cache_file_path,
    _load_cache_file,
    _log_stale_cache_entries,
    _save_cache_file,
    get_cached_eligible_issues,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData


@pytest.fixture
def sample_issue() -> IssueData:
    """Sample issue data for testing."""
    return {
        "number": 123,
        "state": "open",
        "labels": ["status-02:awaiting-planning"],
        "updated_at": "2025-12-31T09:00:00Z",
        "url": "https://github.com/test/repo/issues/123",
        "title": "Test issue",
        "body": "Test issue body",
        "assignees": [],
        "user": "testuser",
        "created_at": "2025-12-31T08:00:00Z",
        "locked": False,
    }


@pytest.fixture
def sample_cache_data() -> Dict[str, object]:
    """Sample cache data structure."""
    return {
        "last_checked": "2025-12-31T10:30:00Z",
        "issues": {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/test/repo/issues/123",
                "title": "Test issue",
                "body": "Test issue body",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
            }
        },
    }


@pytest.fixture
def mock_issue_manager() -> Mock:
    """Mock IssueManager for testing."""
    manager = Mock()
    manager.list_issues.return_value = []
    return manager


class TestCacheFilePath:
    """Tests for _get_cache_file_path function."""

    def test_get_cache_file_path_basic(self) -> None:
        """Test basic cache file path generation."""
        repo_name = "owner/repo"
        path = _get_cache_file_path(repo_name)

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

        for repo_name, expected_filename in test_cases:
            path = _get_cache_file_path(repo_name)
            assert path.name == expected_filename


class TestCacheFileOperations:
    """Tests for cache file load/save operations."""

    def test_load_cache_file_nonexistent(self) -> None:
        """Test loading non-existent cache file returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "nonexistent.json"
            result = _load_cache_file(cache_path)

            assert result == {"last_checked": None, "issues": {}}

    def test_load_cache_file_valid(self, sample_cache_data: Dict[str, object]) -> None:
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

    def test_save_cache_file_success(
        self, sample_cache_data: Dict[str, object]
    ) -> None:
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
        self, sample_cache_data: Dict[str, object]
    ) -> None:
        """Test cache file save creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "deep" / "nested" / "dirs" / "cache.json"

            result = _save_cache_file(cache_path, sample_cache_data)
            assert result is True
            assert cache_path.exists()

    def test_save_cache_file_permission_error(
        self, sample_cache_data: Dict[str, object]
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
        caplog.set_level(logging.INFO, logger="mcp_coder.cli.commands.coordinator")

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
        caplog.set_level(logging.INFO, logger="mcp_coder.cli.commands.coordinator")

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
        caplog.set_level(logging.INFO, logger="mcp_coder.cli.commands.coordinator")

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
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test first run with no existing cache."""
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {"last_checked": None, "issues": {}}
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == [sample_issue]
            mock_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False
            )
            mock_save.assert_called_once()

    def test_get_cached_eligible_issues_incremental_update(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test incremental update with recent cache."""
        # Cache checked 30 minutes ago (within 24-hour window)
        cache_time = datetime.now().astimezone() - timedelta(minutes=30)
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
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

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == [sample_issue]
            # Should call with since parameter for incremental update
            mock_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False, since=cache_time
            )

    def test_get_cached_eligible_issues_full_refresh(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test full refresh when cache is old."""
        # Cache checked 25 hours ago (beyond 24-hour window)
        old_cache_time = datetime.now().astimezone() - timedelta(hours=25)
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
            patch(
                "mcp_coder.cli.commands.coordinator._log_stale_cache_entries"
            ) as mock_log_stale,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": old_cache_time.isoformat(),
                "issues": {"456": {"number": 456, "state": "open", "labels": ["old"]}},
            }
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == [sample_issue]
            # Should call without since parameter for full refresh
            mock_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False
            )
            # Should log staleness since we had cached data
            mock_log_stale.assert_called_once()

    def test_get_cached_eligible_issues_duplicate_protection(
        self, mock_issue_manager: Mock
    ) -> None:
        """Test duplicate protection skips recent checks."""
        # Cache checked 30 seconds ago (within 1-minute window)
        recent_time = datetime.now().astimezone() - timedelta(seconds=30)

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": recent_time.isoformat(),
                "issues": {},
            }

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == []
            # Should not call issue_manager at all due to duplicate protection
            mock_issue_manager.list_issues.assert_not_called()

    def test_get_cached_eligible_issues_force_refresh(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test force refresh bypasses cache and duplicate protection."""
        # Cache checked 30 seconds ago, but force_refresh should bypass it
        recent_time = datetime.now().astimezone() - timedelta(seconds=30)
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
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
                "owner/repo", mock_issue_manager, force_refresh=True
            )

            assert result == [sample_issue]
            # Should call issue_manager despite recent check
            mock_issue_manager.list_issues.assert_called_once()

    def test_get_cached_eligible_issues_corrupted_cache(
        self, mock_issue_manager: Mock
    ) -> None:
        """Test graceful fallback when cache operations fail."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.cli.commands.coordinator._load_cache_file",
                side_effect=Exception("Cache error"),
            ),
            patch(
                "mcp_coder.cli.commands.coordinator.get_eligible_issues"
            ) as mock_fallback,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_fallback.return_value = []

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            # Should fall back to get_eligible_issues
            assert result == []
            mock_fallback.assert_called_once_with(mock_issue_manager)

    def test_get_cached_eligible_issues_custom_cache_refresh_minutes(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test custom cache refresh threshold."""
        # Cache checked 10 minutes ago, with custom 5-minute threshold
        cache_time = datetime.now().astimezone() - timedelta(minutes=10)
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
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
                "owner/repo", mock_issue_manager, cache_refresh_minutes=5
            )

            assert result == [sample_issue]
            # Should do full refresh since 10 minutes > 5 minute threshold
            mock_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False
            )
