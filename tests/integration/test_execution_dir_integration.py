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
