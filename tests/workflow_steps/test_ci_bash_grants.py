"""Tests for the Bash grants of the CI fix and analysis sessions."""

from unittest.mock import MagicMock, patch

from mcp_coder.workflow_steps.ci import _run_ci_analysis, _run_ci_fix
from tests.workflow_steps.test_ci import _make_config, _make_failed_summary


class TestBashGrants:
    """_run_ci_fix passes toolkit Bash grants; _run_ci_analysis does not."""

    @patch("mcp_coder.workflow_steps.ci.push_changes", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.commit_changes", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.run_formatters", return_value=True)
    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.resolve_prompt_slots",
        return_value={"check_instructions": "Run npm test."},
    )
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt",
        return_value="Problem: [problem_description]\n\n[check_instructions]\n",
    )
    @patch(
        "mcp_coder.workflow_steps.ci.llm_permissions",
        return_value=["Bash(npm test)", "mcp__x__y"],
    )
    def test_fix_passes_bash_grants(
        self,
        mock_perms: MagicMock,
        _mock_get_prompt: MagicMock,
        mock_slots: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
        _mock_format: MagicMock,
        _mock_commit: MagicMock,
        _mock_push: MagicMock,
    ) -> None:
        """The fix session gets only the Bash entries; slots see the same grants."""
        mock_prompt_llm.return_value = {"text": "fix response"}
        config = _make_config()

        _run_ci_fix(config, "the problem", fix_attempt=0)

        mock_perms.assert_called_once_with(config.project_dir, config.provider)
        grants = mock_prompt_llm.call_args.kwargs["bash_grants"]
        assert grants == ["Bash(npm test)"]
        assert mock_slots.call_args.args[3] == grants
        prompt = mock_prompt_llm.call_args.args[0]
        assert "Problem: the problem" in prompt
        assert "Run npm test." in prompt
        assert "[check_instructions]" not in prompt

    @patch("mcp_coder.workflow_steps.ci.store_session")
    @patch("mcp_coder.workflow_steps.ci.prompt_llm")
    @patch(
        "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
        return_value="analysis prompt",
    )
    @patch(
        "mcp_coder.workflow_steps.ci.llm_permissions",
        return_value=["Bash(npm test)"],
    )
    def test_analysis_passes_no_bash_grants(
        self,
        mock_perms: MagicMock,
        _mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
    ) -> None:
        """The analysis session is not granted Bash."""
        mock_prompt_llm.return_value = {"text": "analysis response"}

        _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

        mock_perms.assert_not_called()
        assert "bash_grants" not in mock_prompt_llm.call_args.kwargs
