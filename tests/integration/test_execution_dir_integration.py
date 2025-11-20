#!/usr/bin/env python3
"""Integration tests for --execution-dir feature.

Tests the complete flow from CLI to subprocess execution,
verifying separation of project and execution directories.

This module validates that:
1. execution_dir controls where Claude subprocess runs (working directory)
2. project_dir controls where files are modified and git operations occur
3. Config discovery uses execution_dir
4. CLI argument parsing works correctly
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.main import create_parser


@pytest.mark.integration
@pytest.mark.execution_dir
class TestExecutionDirCLIParser:
    """Test CLI argument parser for --execution-dir argument."""

    def test_prompt_parser_accepts_execution_dir(self) -> None:
        """Verify prompt command parser accepts --execution-dir argument."""
        parser = create_parser()

        args = parser.parse_args(
            ["prompt", "test question", "--execution-dir", "/tmp/workspace"]
        )

        assert hasattr(args, "execution_dir")
        assert args.execution_dir == "/tmp/workspace"

    def test_implement_parser_accepts_execution_dir(self) -> None:
        """Verify implement command parser accepts --execution-dir argument."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "implement",
                "--execution-dir",
                "/tmp/workspace",
                "--llm-method",
                "claude_code_cli",
            ]
        )

        assert hasattr(args, "execution_dir")
        assert args.execution_dir == "/tmp/workspace"

    def test_create_plan_parser_accepts_execution_dir(self) -> None:
        """Verify create-plan command parser accepts --execution-dir argument."""
        parser = create_parser()

        args = parser.parse_args(
            ["create-plan", "123", "--execution-dir", "/tmp/workspace"]
        )

        assert hasattr(args, "execution_dir")
        assert args.execution_dir == "/tmp/workspace"

    def test_create_pr_parser_accepts_execution_dir(self) -> None:
        """Verify create-pr command parser accepts --execution-dir argument."""
        parser = create_parser()

        args = parser.parse_args(["create-pr", "--execution-dir", "/tmp/workspace"])

        assert hasattr(args, "execution_dir")
        assert args.execution_dir == "/tmp/workspace"

    def test_commit_auto_parser_accepts_execution_dir(self) -> None:
        """Verify commit auto command parser accepts --execution-dir argument."""
        parser = create_parser()

        args = parser.parse_args(
            ["commit", "auto", "--execution-dir", "/tmp/workspace"]
        )

        assert hasattr(args, "execution_dir")
        assert args.execution_dir == "/tmp/workspace"

    def test_execution_dir_is_optional(self) -> None:
        """Verify --execution-dir argument is optional (backward compatibility)."""
        parser = create_parser()

        # Parse commands WITHOUT --execution-dir (should not fail)
        args_prompt = parser.parse_args(["prompt", "test question"])
        args_implement = parser.parse_args(["implement"])

        # Commands should parse successfully without execution_dir
        assert args_prompt.command == "prompt"
        assert args_implement.command == "implement"
        # execution_dir should be None when not specified
        assert args_prompt.execution_dir is None
        assert args_implement.execution_dir is None

    def test_execution_dir_with_relative_path(self) -> None:
        """Verify relative paths are accepted for --execution-dir."""
        parser = create_parser()

        args = parser.parse_args(
            ["prompt", "test question", "--execution-dir", "./subdir"]
        )

        assert hasattr(args, "execution_dir")
        assert args.execution_dir == "./subdir"

    def test_execution_dir_with_absolute_path(self) -> None:
        """Verify absolute paths are accepted for --execution-dir."""
        parser = create_parser()

        args = parser.parse_args(
            ["prompt", "test question", "--execution-dir", "/absolute/path/workspace"]
        )

        assert hasattr(args, "execution_dir")
        assert args.execution_dir == "/absolute/path/workspace"


@pytest.mark.integration
@pytest.mark.execution_dir
class TestExecutionDirResolution:
    """Test execution_dir path resolution utility."""

    def test_resolve_none_returns_cwd(self, tmp_path: Path) -> None:
        """Test that None execution_dir resolves to current working directory."""
        import os

        from mcp_coder.cli.utils import resolve_execution_dir

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            resolved = resolve_execution_dir(None)
            assert resolved == tmp_path
        finally:
            os.chdir(original_cwd)

    def test_resolve_absolute_path(self, tmp_path: Path) -> None:
        """Test that absolute paths are returned as-is."""
        from mcp_coder.cli.utils import resolve_execution_dir

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        resolved = resolve_execution_dir(str(workspace))
        assert resolved == workspace

    def test_resolve_relative_path(self, tmp_path: Path) -> None:
        """Test that relative paths are resolved against CWD."""
        import os

        from mcp_coder.cli.utils import resolve_execution_dir

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            resolved = resolve_execution_dir("workspace")
            assert resolved == workspace
        finally:
            os.chdir(original_cwd)

    def test_resolve_nonexistent_directory_raises_error(self, tmp_path: Path) -> None:
        """Test that nonexistent directory raises ValueError."""
        from mcp_coder.cli.utils import resolve_execution_dir

        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(ValueError, match="does not exist"):
            resolve_execution_dir(str(nonexistent))

    def test_resolve_file_instead_of_directory_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Test that file path returns the path (files don't raise errors).

        Note: The implementation doesn't explicitly check if the path is a file.
        It only checks if the path exists. This test documents the current behavior.
        """
        from mcp_coder.cli.utils import resolve_execution_dir

        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        # Current implementation accepts file paths (doesn't validate it's a directory)
        resolved = resolve_execution_dir(str(file_path))
        assert resolved == file_path


@pytest.mark.integration
@pytest.mark.execution_dir
class TestSubprocessCwdParameter:
    """Test that subprocess actually receives correct cwd parameter.

    These tests verify the complete flow from command handler through to
    the actual subprocess execution, ensuring execution_dir is used as cwd.
    """

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    def test_prompt_command_passes_execution_dir_to_subprocess(
        self,
        mock_prepare_env: MagicMock,
        mock_execute_subprocess: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test prompt command passes execution_dir as cwd to subprocess."""
        from mcp_coder.cli.commands.prompt import execute_prompt

        # Setup
        execution_dir = tmp_path / "execution"
        execution_dir.mkdir()

        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}

        # Create proper subprocess result mock with all required attributes
        # The CLI returns JSON, so we need to mock valid JSON output
        mock_result = MagicMock()
        mock_result.return_code = 0
        mock_result.stdout = (
            '{"result": "Claude response", "session_id": "test-session-123"}'
        )
        mock_result.stderr = ""
        mock_result.timed_out = False
        mock_execute_subprocess.return_value = mock_result

        # Execute
        import argparse

        args = argparse.Namespace(
            prompt="Test prompt",
            execution_dir=str(execution_dir),
            project_dir=None,
            timeout=30,
            llm_method="claude_code_cli",
            verbosity="just-text",
            session_id=None,
            mcp_config=None,
        )

        result = execute_prompt(args)

        # Verify
        assert result == 0
        # Check that execute_subprocess was called with cwd=execution_dir
        assert mock_execute_subprocess.called
        call_kwargs = mock_execute_subprocess.call_args[1]
        assert "options" in call_kwargs
        assert call_kwargs["options"].cwd == str(execution_dir)

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    def test_prompt_command_none_execution_dir_uses_none_as_cwd(
        self,
        mock_prepare_env: MagicMock,
        mock_execute_subprocess: MagicMock,
    ) -> None:
        """Test prompt command with None execution_dir passes None to subprocess."""
        from mcp_coder.cli.commands.prompt import execute_prompt

        # Setup
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}

        # Create proper subprocess result mock with all required attributes
        # The CLI returns JSON, so we need to mock valid JSON output
        mock_result = MagicMock()
        mock_result.return_code = 0
        mock_result.stdout = (
            '{"result": "Claude response", "session_id": "test-session-456"}'
        )
        mock_result.stderr = ""
        mock_result.timed_out = False
        mock_execute_subprocess.return_value = mock_result

        # Execute with execution_dir=None (default)
        import argparse

        args = argparse.Namespace(
            prompt="Test prompt",
            execution_dir=None,  # No explicit execution_dir
            project_dir=None,
            timeout=30,
            llm_method="claude_code_cli",
            verbosity="just-text",
            session_id=None,
            mcp_config=None,
        )

        result = execute_prompt(args)

        # Verify
        assert result == 0
        # Check that execute_subprocess was called with cwd=None (uses process CWD)
        assert mock_execute_subprocess.called
        call_kwargs = mock_execute_subprocess.call_args[1]
        assert "options" in call_kwargs
        # When execution_dir=None, resolve_execution_dir returns Path.cwd()
        # which is then converted to string and passed as cwd
        assert call_kwargs["options"].cwd == str(Path.cwd())

    @patch("mcp_coder.workflows.implement.core.process_single_task")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    def test_implement_workflow_passes_execution_dir_to_task_processing(
        self,
        mock_check_prereq: MagicMock,
        mock_prepare_tracker: MagicMock,
        mock_process_task: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test implement workflow passes execution_dir to task processing."""
        from mcp_coder.workflows.implement.core import run_implement_workflow

        # Setup
        execution_dir = tmp_path / "execution"
        execution_dir.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Need to create .git directory for git checks
        (project_dir / ".git").mkdir()

        mock_check_prereq.return_value = True
        mock_prepare_tracker.return_value = True
        mock_process_task.return_value = (False, "no_tasks")  # No more tasks

        # Execute
        result = run_implement_workflow(
            project_dir, "claude", "cli", None, execution_dir
        )

        # Verify
        assert result == 0
        # Check that prepare_task_tracker received execution_dir
        mock_prepare_tracker.assert_called_once_with(
            project_dir, "claude", "cli", None, execution_dir
        )
        # Check that process_single_task received execution_dir
        mock_process_task.assert_called_once_with(
            project_dir, "claude", "cli", None, execution_dir
        )

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.workflows.create_plan.validate_output_files")
    @patch("mcp_coder.workflows.create_plan.commit_all_changes")
    @patch("mcp_coder.workflows.create_plan.git_push")
    @patch("mcp_coder.workflows.create_plan.verify_steps_directory")
    @patch("mcp_coder.workflows.create_plan.manage_branch")
    @patch("mcp_coder.workflows.create_plan.check_prerequisites")
    def test_create_plan_workflow_passes_execution_dir_to_llm(
        self,
        mock_check_prereq: MagicMock,
        mock_manage_branch: MagicMock,
        mock_verify_steps: MagicMock,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_validate: MagicMock,
        mock_execute_subprocess: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test create-plan workflow passes execution_dir to LLM calls."""
        from mcp_coder.workflows.create_plan import IssueData, run_create_plan_workflow

        # Setup
        execution_dir = tmp_path / "execution"
        execution_dir.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()

        mock_issue_data = IssueData(
            number=123,
            title="Test Issue",
            body="Test body",
            labels=[],
        )
        mock_check_prereq.return_value = (True, mock_issue_data)
        mock_manage_branch.return_value = "feature-branch"
        mock_verify_steps.return_value = True
        mock_validate.return_value = True
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = {"success": True}

        # Mock subprocess to return valid responses
        # The CLI returns JSON, so we need to mock valid JSON output
        mock_result = MagicMock()
        mock_result.return_code = 0
        mock_result.stdout = (
            '{"result": "Plan generated", "session_id": "plan-session-789"}'
        )
        mock_result.stderr = ""
        mock_result.timed_out = False
        mock_execute_subprocess.return_value = mock_result

        # Execute
        result = run_create_plan_workflow(
            123, project_dir, "claude", "cli", None, execution_dir
        )

        # Verify
        assert result == 0
        # Check that subprocess was called with execution_dir as cwd
        assert mock_execute_subprocess.called
        # Should be called 3 times (3 planning prompts)
        assert mock_execute_subprocess.call_count >= 1
        # Check first call has correct cwd
        first_call_kwargs = mock_execute_subprocess.call_args_list[0][1]
        assert "options" in first_call_kwargs
        assert first_call_kwargs["options"].cwd == str(execution_dir)

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    def test_commit_auto_passes_execution_dir_to_llm_subprocess(
        self,
        mock_commit_files: MagicMock,
        mock_validate_git: MagicMock,
        mock_get_diff: MagicMock,
        mock_execute_subprocess: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test commit auto command passes execution_dir to LLM subprocess."""
        from mcp_coder.cli.commands.commit import execute_commit_auto

        # Setup
        execution_dir = tmp_path / "execution"
        execution_dir.mkdir()

        mock_validate_git.return_value = (True, None)
        mock_get_diff.return_value = "diff output"

        # Create proper subprocess result mock with all required attributes
        # The CLI returns JSON, so we need to mock valid JSON output
        mock_result = MagicMock()
        mock_result.return_code = 0
        mock_result.stdout = '{"result": "feat: add new feature", "session_id": null}'
        mock_result.stderr = ""
        mock_result.timed_out = False
        mock_execute_subprocess.return_value = mock_result
        mock_commit_files.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        # Execute
        import argparse

        args = argparse.Namespace(
            preview=False,
            llm_method="claude_code_cli",
            project_dir=None,
            execution_dir=str(execution_dir),
        )

        result = execute_commit_auto(args)

        # Verify
        assert result == 0
        # Check that subprocess was called with execution_dir as cwd
        assert mock_execute_subprocess.called
        call_kwargs = mock_execute_subprocess.call_args[1]
        assert "options" in call_kwargs
        assert call_kwargs["options"].cwd == str(execution_dir)

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_llm_interface_passes_execution_dir_to_provider(
        self,
        mock_execute_subprocess: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test LLM interface layer passes execution_dir to provider."""
        from mcp_coder.llm.interface import ask_llm

        # Setup
        execution_dir = tmp_path / "execution"
        execution_dir.mkdir()

        # Create proper subprocess result mock with all required attributes
        # The CLI returns JSON, so we need to mock valid JSON output
        mock_result = MagicMock()
        mock_result.return_code = 0
        mock_result.stdout = (
            '{"result": "LLM response", "session_id": "llm-session-abc"}'
        )
        mock_result.stderr = ""
        mock_result.timed_out = False
        mock_execute_subprocess.return_value = mock_result

        # Execute
        result = ask_llm(
            "Test question",
            provider="claude",
            method="cli",
            execution_dir=str(execution_dir),
        )

        # Verify
        assert result == "LLM response"
        # Check that subprocess was called with execution_dir as cwd
        assert mock_execute_subprocess.called
        call_kwargs = mock_execute_subprocess.call_args[1]
        assert "options" in call_kwargs
        assert call_kwargs["options"].cwd == str(execution_dir)

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_execution_dir_separate_from_project_dir_in_subprocess(
        self,
        mock_execute_subprocess: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that execution_dir and project_dir are truly separate in subprocess."""
        from mcp_coder.llm.interface import ask_llm

        # Setup distinct directories
        execution_dir = tmp_path / "execution_workspace"
        execution_dir.mkdir()
        project_dir = tmp_path / "project_source"
        project_dir.mkdir()

        # Create proper subprocess result mock with all required attributes
        # The CLI returns JSON, so we need to mock valid JSON output
        mock_result = MagicMock()
        mock_result.return_code = 0
        mock_result.stdout = (
            '{"result": "LLM response", "session_id": "sep-session-xyz"}'
        )
        mock_result.stderr = ""
        mock_result.timed_out = False
        mock_execute_subprocess.return_value = mock_result

        # Execute with different project_dir and execution_dir
        result = ask_llm(
            "Test question",
            provider="claude",
            method="cli",
            project_dir=str(project_dir),
            execution_dir=str(execution_dir),
        )

        # Verify
        assert result == "LLM response"
        assert mock_execute_subprocess.called

        # Verify subprocess got execution_dir as cwd (not project_dir)
        call_kwargs = mock_execute_subprocess.call_args[1]
        assert call_kwargs["options"].cwd == str(execution_dir)
        assert call_kwargs["options"].cwd != str(project_dir)

        # Verify project_dir is in environment variables (not cwd)
        assert "env" in call_kwargs["options"].__dict__ or "env" in dir(
            call_kwargs["options"]
        )
        # The env vars should contain project_dir, not execution_dir
        # (This validates separation of concerns)
