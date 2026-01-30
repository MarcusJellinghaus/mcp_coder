"""Test helper functions for VSCode Claude orchestration."""

from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.vscodeclaude.helpers import (
    get_issue_status,
    get_repo_full_name,
    get_repo_short_name,
    get_repo_short_name_from_full,
    get_stage_display_name,
    truncate_title,
)
from mcp_coder.utils.vscodeclaude.types import (
    STAGE_DISPLAY_NAMES,
    VSCODECLAUDE_PRIORITY,
)


class TestRepoNameParsing:
    """Test repo URL parsing functions.

    These tests ensure repo names are correctly extracted from URLs,
    especially for edge cases where rstrip() could corrupt the name.
    """

    def test_get_repo_full_name_standard_url(self) -> None:
        """Extracts owner/repo from standard GitHub URL."""
        config = {"repo_url": "https://github.com/owner/repo.git"}
        assert get_repo_full_name(config) == "owner/repo"

    def test_get_repo_full_name_without_git_suffix(self) -> None:
        """Works without .git suffix."""
        config = {"repo_url": "https://github.com/owner/repo"}
        assert get_repo_full_name(config) == "owner/repo"

    def test_get_repo_full_name_with_trailing_slash(self) -> None:
        """Handles trailing slash."""
        config = {"repo_url": "https://github.com/owner/repo/"}
        assert get_repo_full_name(config) == "owner/repo"

    def test_get_repo_full_name_preserves_config_in_name(self) -> None:
        """Preserves 'config' in repo name (regression test for rstrip bug).

        rstrip('.git') would corrupt 'mcp-config' to 'mcp-conf' because
        it strips all chars in the set {'.', 'g', 'i', 't'}, not the suffix.
        """
        config = {"repo_url": "https://github.com/owner/mcp-config.git"}
        result = get_repo_full_name(config)
        assert result == "owner/mcp-config"
        assert "mcp-config" in result  # Not corrupted to mcp-conf

    def test_get_repo_full_name_preserves_git_in_name(self) -> None:
        """Preserves 'git' in repo name."""
        config = {"repo_url": "https://github.com/owner/my-git-tool.git"}
        assert get_repo_full_name(config) == "owner/my-git-tool"

    def test_get_repo_short_name_standard_url(self) -> None:
        """Extracts repo from standard GitHub URL."""
        config = {"repo_url": "https://github.com/owner/repo.git"}
        assert get_repo_short_name(config) == "repo"

    def test_get_repo_short_name_preserves_config_in_name(self) -> None:
        """Preserves 'config' in repo name (regression test for rstrip bug)."""
        config = {"repo_url": "https://github.com/owner/mcp-config.git"}
        result = get_repo_short_name(config)
        assert result == "mcp-config"
        assert result != "mcp-conf"  # Would be corrupted by rstrip('.git')

    def test_get_repo_short_name_empty_url(self) -> None:
        """Returns 'repo' for empty URL."""
        config = {"repo_url": ""}
        assert get_repo_short_name(config) == "repo"

    def test_get_repo_short_name_from_full_standard(self) -> None:
        """Extracts short name from full repo name."""
        assert get_repo_short_name_from_full("owner/repo") == "repo"

    def test_get_repo_short_name_from_full_no_slash(self) -> None:
        """Returns unchanged if no slash."""
        assert get_repo_short_name_from_full("repo") == "repo"


class TestIssueStatus:
    """Test issue status extraction."""

    def test_get_issue_status_with_status_label(self) -> None:
        """Extracts status label from issue."""
        issue: IssueData = {
            "number": 1,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["bug", "status-07:code-review", "priority-high"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        assert get_issue_status(issue) == "status-07:code-review"

    def test_get_issue_status_no_status_label(self) -> None:
        """Returns empty string if no status label."""
        issue: IssueData = {
            "number": 1,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["bug", "priority-high"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        assert get_issue_status(issue) == ""


class TestDisplayHelpers:
    """Test display helper functions."""

    def test_get_stage_display_name_known_statuses(self) -> None:
        """Returns human-readable stage names."""
        assert get_stage_display_name("status-07:code-review") == "CODE REVIEW"
        assert get_stage_display_name("status-04:plan-review") == "PLAN REVIEW"
        assert get_stage_display_name("status-01:created") == "ISSUE ANALYSIS"
        assert get_stage_display_name("status-10:pr-created") == "PR CREATED"

    def test_get_stage_display_name_unknown_status(self) -> None:
        """Returns uppercased status for unknown statuses."""
        result = get_stage_display_name("unknown-status")
        assert result == "UNKNOWN-STATUS"

    def test_truncate_title_short(self) -> None:
        """Returns unchanged if under max length."""
        assert truncate_title("Short title", 50) == "Short title"

    def test_truncate_title_exact_length(self) -> None:
        """Returns unchanged if exactly at max length."""
        title = "A" * 50
        result = truncate_title(title, 50)
        assert result == title
        assert len(result) == 50

    def test_truncate_title_long(self) -> None:
        """Truncates with ellipsis if over max."""
        long_title = "A" * 100
        result = truncate_title(long_title, 50)
        assert len(result) == 50
        assert result.endswith("...")
        # Should have 47 'A's followed by '...'
        assert result == "A" * 47 + "..."

    def test_stage_display_names_coverage(self) -> None:
        """All priority statuses have display names."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in STAGE_DISPLAY_NAMES
