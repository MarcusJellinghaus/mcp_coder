"""Test backward compatibility for orchestrator functions."""

from mcp_coder.utils.vscodeclaude.orchestrator import (
    _get_repo_full_name,
    _get_repo_short_name,
    get_stage_display_name,
    truncate_title,
)


class TestBackwardCompatibility:
    """Test that re-exported functions maintain backward compatibility."""

    def test_underscore_prefixed_functions_work(self) -> None:
        """Underscore-prefixed aliases work for backward compatibility."""
        # These are imported from orchestrator and should work
        config = {"repo_url": "https://github.com/owner/repo.git"}
        assert _get_repo_full_name(config) == "owner/repo"
        assert _get_repo_short_name(config) == "repo"

    def test_display_functions_work(self) -> None:
        """Display functions are accessible from orchestrator."""
        assert get_stage_display_name("status-07:code-review") == "CODE REVIEW"
        assert truncate_title("Short") == "Short"
