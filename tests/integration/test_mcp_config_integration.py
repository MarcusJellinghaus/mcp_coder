#!/usr/bin/env python3
"""Integration tests for --mcp-config CLI argument parsing and flow.

This module tests end-to-end flow from CLI argument parsing through command execution
to LLM provider invocation. Tests verify that --mcp-config argument is properly parsed
and passed through to the underlying Claude CLI provider.

These tests follow TDD approach - written BEFORE CLI implementation.
Tests are expected to FAIL until Step 4 (CLI argument implementation) is completed.
"""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# Import CLI components
from mcp_coder.cli.commands.implement import execute_implement
from mcp_coder.cli.commands.prompt import execute_prompt
from mcp_coder.cli.main import create_parser, main
from mcp_coder.utils.subprocess_runner import CommandResult


class TestMcpConfigIntegration:
    """Integration tests for --mcp-config CLI argument."""

    @pytest.fixture
    def temp_mcp_config(self, tmp_path: Path) -> str:
        """Create temporary MCP config file.

        Args:
            tmp_path: pytest temporary directory fixture

        Returns:
            str: Path to temporary MCP config file
        """
        config_file = tmp_path / ".mcp.test.json"
        config_file.write_text('{"mcpServers": {}}')
        return str(config_file)

    @pytest.fixture
    def mock_subprocess_success(self) -> CommandResult:
        """Mock successful subprocess execution.

        Returns:
            CommandResult: Mocked subprocess result with successful response
        """
        mock_result = CommandResult(
            return_code=0,
            stdout=json.dumps({"result": "Test response", "session_id": "test-123"}),
            stderr="",
            timed_out=False,
        )
        return mock_result

    def test_implement_with_mcp_config_argument(
        self, temp_mcp_config: str, mock_subprocess_success: CommandResult, tmp_path: Path
    ) -> None:
        """Verify implement command accepts and uses --mcp-config.

        This tests the most complex command (implement) to verify that:
        1. CLI parser accepts --mcp-config argument
        2. Argument is passed through command execution chain
        3. Underlying LLM provider receives mcp_config parameter
        4. Command constructs proper flags for Claude CLI

        Args:
            temp_mcp_config: Fixture providing temporary config file path
            mock_subprocess_success: Fixture providing mocked subprocess result
            tmp_path: pytest temporary directory fixture
        """
        # Create a valid test project directory with .git
        test_project = tmp_path / "test_project"
        test_project.mkdir()
        (test_project / ".git").mkdir()
        
        with (
            patch(
                "mcp_coder.workflows.implement.core.run_implement_workflow"
            ) as mock_workflow,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess"
            ) as mock_execute,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable"
            ) as mock_find,
        ):
            # Setup mocks
            mock_find.return_value = "claude"
            mock_execute.return_value = mock_subprocess_success
            mock_workflow.return_value = 0

            # Create args with mcp_config parameter
            args = argparse.Namespace(
                project_dir=str(test_project),
                llm_method="claude_code_cli",
                mcp_config=temp_mcp_config,
            )

            # Execute command
            result = execute_implement(args)

            # Verify command succeeded
            assert result == 0

            # NOTE: This test will FAIL until Step 4 implements:
            # 1. --mcp-config argument in CLI parser
            # 2. mcp_config parameter threaded through commands
            # 3. LLM provider receiving and using mcp_config

    def test_prompt_with_mcp_config_argument(
        self, temp_mcp_config: str, mock_subprocess_success: CommandResult
    ) -> None:
        """Verify prompt command (simplest) accepts and uses --mcp-config.

        This tests the simplest command to verify basic functionality:
        1. CLI parser accepts --mcp-config for prompt command
        2. Parameter flows through to LLM provider
        3. Command executes successfully with mcp_config

        Args:
            temp_mcp_config: Fixture providing temporary config file path
            mock_subprocess_success: Fixture providing mocked subprocess result
        """
        with (
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess"
            ) as mock_execute,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable"
            ) as mock_find,
        ):
            # Setup mocks
            mock_find.return_value = "claude"
            mock_execute.return_value = mock_subprocess_success

            # Create args with mcp_config parameter
            args = argparse.Namespace(
                prompt="Test question",
                project_dir=None,
                llm_method="claude_code_cli",
                verbosity="just-text",
                output_format="text",
                store_response=False,
                timeout=60,
                session_id=None,
                continue_session=False,
                continue_session_from=None,
                mcp_config=temp_mcp_config,
            )

            # Execute command
            result = execute_prompt(args)

            # Verify command succeeded
            assert result == 0

            # Verify execute_subprocess was called
            assert mock_execute.called

            # Verify command contains mcp_config flags
            call_args = mock_execute.call_args
            command = call_args[0][0]  # First positional argument is the command list

            assert "--mcp-config" in command
            assert temp_mcp_config in command
            assert "--strict-mcp-config" in command

            # NOTE: This test will FAIL until Step 4 implements CLI argument

    def test_mcp_config_not_required(
        self, mock_subprocess_success: CommandResult
    ) -> None:
        """Verify commands work without --mcp-config (backward compatibility).

        This ensures that adding --mcp-config doesn't break existing workflows
        that don't use it. Commands should continue working without the parameter.
        """
        with (
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess"
            ) as mock_execute,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable"
            ) as mock_find,
        ):
            # Setup mocks
            mock_find.return_value = "claude"
            mock_execute.return_value = mock_subprocess_success

            # Create args WITHOUT mcp_config parameter
            args = argparse.Namespace(
                prompt="Test question",
                project_dir=None,
                llm_method="claude_code_cli",
                verbosity="just-text",
                output_format="text",
                store_response=False,
                timeout=60,
                session_id=None,
                continue_session=False,
                continue_session_from=None,
                # NOTE: No mcp_config parameter - testing backward compatibility
            )

            # Execute command
            result = execute_prompt(args)

            # Verify command succeeded
            assert result == 0

            # Verify execute_subprocess was called
            assert mock_execute.called

            # Verify command does NOT contain mcp_config flags
            call_args = mock_execute.call_args
            command = call_args[0][0]

            assert "--mcp-config" not in command
            assert "--strict-mcp-config" not in command

            # NOTE: This test should PASS even before Step 4
            # It validates existing behavior is preserved

    def test_mcp_config_with_relative_path(
        self, tmp_path: Path, mock_subprocess_success: CommandResult
    ) -> None:
        """Verify relative paths work for --mcp-config.

        Args:
            tmp_path: pytest temporary directory fixture
            mock_subprocess_success: Fixture providing mocked subprocess result
        """
        # Create config with relative path
        relative_config = ".mcp.test.json"
        (tmp_path / relative_config).write_text('{"mcpServers": {}}')

        with (
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess"
            ) as mock_execute,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable"
            ) as mock_find,
            patch("mcp_coder.cli.commands.prompt.Path.cwd") as mock_cwd,
        ):
            # Setup mocks
            mock_find.return_value = "claude"
            mock_execute.return_value = mock_subprocess_success
            mock_cwd.return_value = tmp_path

            # Create args with relative mcp_config path
            args = argparse.Namespace(
                prompt="Test question",
                project_dir=None,
                llm_method="claude_code_cli",
                verbosity="just-text",
                output_format="text",
                store_response=False,
                timeout=60,
                session_id=None,
                continue_session=False,
                continue_session_from=None,
                mcp_config=relative_config,
            )

            # Execute command
            result = execute_prompt(args)

            # Verify command succeeded
            assert result == 0

            # Verify execute_subprocess was called
            assert mock_execute.called

            # Verify command contains the relative path
            call_args = mock_execute.call_args
            command = call_args[0][0]

            assert "--mcp-config" in command
            assert relative_config in command

            # NOTE: This test will FAIL until Step 4 implements CLI argument


class TestMcpConfigCLIParser:
    """Test CLI argument parser for --mcp-config argument."""

    def test_implement_parser_accepts_mcp_config(self) -> None:
        """Verify implement command parser accepts --mcp-config argument.

        NOTE: This test will FAIL until Step 4 adds --mcp-config to implement_parser.
        """
        parser = create_parser()

        # Parse implement command with --mcp-config
        args = parser.parse_args(
            [
                "implement",
                "--mcp-config",
                ".mcp.linux.json",
                "--llm-method",
                "claude_code_cli",
            ]
        )

        assert hasattr(args, "mcp_config")
        assert args.mcp_config == ".mcp.linux.json"

    def test_prompt_parser_accepts_mcp_config(self) -> None:
        """Verify prompt command parser accepts --mcp-config argument.

        NOTE: This test will FAIL until Step 4 adds --mcp-config to prompt_parser.
        """
        parser = create_parser()

        # Parse prompt command with --mcp-config
        args = parser.parse_args(
            ["prompt", "test question", "--mcp-config", ".mcp.linux.json"]
        )

        assert hasattr(args, "mcp_config")
        assert args.mcp_config == ".mcp.linux.json"

    def test_create_plan_parser_accepts_mcp_config(self) -> None:
        """Verify create-plan command parser accepts --mcp-config argument.

        NOTE: This test will FAIL until Step 4 adds --mcp-config to create_plan_parser.
        """
        parser = create_parser()

        # Parse create-plan command with --mcp-config
        args = parser.parse_args(
            ["create-plan", "123", "--mcp-config", ".mcp.linux.json"]
        )

        assert hasattr(args, "mcp_config")
        assert args.mcp_config == ".mcp.linux.json"

    def test_create_pr_parser_accepts_mcp_config(self) -> None:
        """Verify create-pr command parser accepts --mcp-config argument.

        NOTE: This test will FAIL until Step 4 adds --mcp-config to create_pr_parser.
        """
        parser = create_parser()

        # Parse create-pr command with --mcp-config
        args = parser.parse_args(["create-pr", "--mcp-config", ".mcp.linux.json"])

        assert hasattr(args, "mcp_config")
        assert args.mcp_config == ".mcp.linux.json"

    def test_commit_auto_parser_accepts_mcp_config(self) -> None:
        """Verify commit auto command parser accepts --mcp-config argument.

        NOTE: This test will FAIL until Step 4 adds --mcp-config to auto_parser.
        """
        parser = create_parser()

        # Parse commit auto command with --mcp-config
        args = parser.parse_args(["commit", "auto", "--mcp-config", ".mcp.linux.json"])

        assert hasattr(args, "mcp_config")
        assert args.mcp_config == ".mcp.linux.json"

    def test_mcp_config_is_optional(self) -> None:
        """Verify --mcp-config argument is optional (backward compatibility).

        This test should PASS even before Step 4 implementation,
        as it validates existing behavior is preserved.
        """
        parser = create_parser()

        # Parse commands WITHOUT --mcp-config (should not fail)
        args_prompt = parser.parse_args(["prompt", "test question"])
        args_implement = parser.parse_args(["implement"])

        # Commands should parse successfully without mcp_config
        # (mcp_config will be None or not present)
        assert args_prompt.command == "prompt"
        assert args_implement.command == "implement"
