"""Unit tests for mcp_coder.utils.repo_config.get_repo_flag."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.utils.repo_config import get_repo_flag

_SECTION = "coordinator.repos.myrepo"


class TestGetRepoFlag:
    """Test cases for get_repo_flag."""

    @patch("mcp_coder.utils.repo_config.get_config_values")
    @patch(
        "mcp_coder.utils.repo_config.find_repo_section_by_url",
        return_value=_SECTION,
    )
    @patch(
        "mcp_coder.utils.repo_config.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_flag_true_returns_true(
        self,
        _mock_id: MagicMock,
        _mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Flag set True in the matching section -> True."""
        mock_config.return_value = {(_SECTION, "auto_review_plan"): True}
        result = get_repo_flag(Path("/tmp/project"), "auto_review_plan")
        assert result is True

    @patch("mcp_coder.utils.repo_config.get_config_values")
    @patch(
        "mcp_coder.utils.repo_config.find_repo_section_by_url",
        return_value=_SECTION,
    )
    @patch(
        "mcp_coder.utils.repo_config.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_flag_false_returns_false(
        self,
        _mock_id: MagicMock,
        _mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Flag set False in the matching section -> False."""
        mock_config.return_value = {(_SECTION, "auto_review_plan"): False}
        result = get_repo_flag(Path("/tmp/project"), "auto_review_plan")
        assert result is False

    @patch("mcp_coder.utils.repo_config.get_config_values")
    @patch(
        "mcp_coder.utils.repo_config.find_repo_section_by_url",
        return_value=_SECTION,
    )
    @patch(
        "mcp_coder.utils.repo_config.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_flag_unset_returns_default_false(
        self,
        _mock_id: MagicMock,
        _mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Flag unset (None) -> default False."""
        mock_config.return_value = {(_SECTION, "auto_review_plan"): None}
        result = get_repo_flag(Path("/tmp/project"), "auto_review_plan")
        assert result is False

    @patch("mcp_coder.utils.repo_config.get_config_values")
    @patch(
        "mcp_coder.utils.repo_config.find_repo_section_by_url",
        return_value=_SECTION,
    )
    @patch(
        "mcp_coder.utils.repo_config.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_flag_unset_returns_default_true(
        self,
        _mock_id: MagicMock,
        _mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Flag unset (None) with default True -> True."""
        mock_config.return_value = {(_SECTION, "auto_review_plan"): None}
        result = get_repo_flag(Path("/tmp/project"), "auto_review_plan", default=True)
        assert result is True

    @patch("mcp_coder.utils.repo_config.find_repo_section_by_url", return_value=None)
    @patch(
        "mcp_coder.utils.repo_config.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/unknown-repo"),
    )
    def test_no_matching_section_returns_default(
        self,
        _mock_id: MagicMock,
        _mock_find: MagicMock,
    ) -> None:
        """No matching config section -> default."""
        assert get_repo_flag(Path("/tmp/project"), "auto_review_plan") is False
        assert (
            get_repo_flag(Path("/tmp/project"), "auto_review_plan", default=True)
            is True
        )

    @patch(
        "mcp_coder.utils.repo_config.get_repository_identifier",
        return_value=None,
    )
    def test_no_git_remote_returns_default(self, _mock_id: MagicMock) -> None:
        """No git remote (identifier is None) -> default."""
        assert get_repo_flag(Path("/tmp/project"), "auto_review_plan") is False
        assert (
            get_repo_flag(Path("/tmp/project"), "auto_review_plan", default=True)
            is True
        )

    @patch("mcp_coder.utils.repo_config.get_config_values")
    @patch(
        "mcp_coder.utils.repo_config.find_repo_section_by_url",
        return_value=_SECTION,
    )
    @patch(
        "mcp_coder.utils.repo_config.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_non_boolean_value_returns_default(
        self,
        _mock_id: MagicMock,
        _mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Non-boolean value -> default (defensive isinstance guard)."""
        mock_config.return_value = {(_SECTION, "auto_review_plan"): "true"}
        result = get_repo_flag(Path("/tmp/project"), "auto_review_plan")
        assert result is False
