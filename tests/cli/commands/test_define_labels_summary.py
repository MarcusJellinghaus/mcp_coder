"""Tests for define-labels CLI summary output.

Tests cover:
- Summary shows 'skipped' for operations not requested
- Summary shows actual counts when operations are enabled
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.define_labels import execute_define_labels


def _make_namespace(
    project_dir: str | None = None,
    dry_run: bool = False,
    init: bool = False,
    validate: bool = False,
    all_ops: bool = False,
    config: str | None = None,
    generate_github_actions: bool = False,
) -> argparse.Namespace:
    """Build an argparse.Namespace with all define-labels flags."""
    return argparse.Namespace(
        project_dir=project_dir,
        dry_run=dry_run,
        init=init,
        validate=validate,
        all=all_ops,
        config=config,
        generate_github_actions=generate_github_actions,
    )


class TestSummarySkipped:
    """Test that summary shows 'skipped' for operations not requested."""

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_no_flags_shows_skipped(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When no flags set, summary shows 'skipped' for init and validate."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

        args = _make_namespace(project_dir=str(project_dir))
        execute_define_labels(args)

        output = capsys.readouterr().out
        assert "Issues initialized: skipped" in output

    @patch("mcp_coder.cli.commands.define_labels.validate_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_init_flag_shows_count(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager: MagicMock,
        mock_validate_config: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With --init, summary shows actual count instead of skipped."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "internal_id": "created",
                    "name": "status-01:created",
                    "color": "10b981",
                    "description": "Test",
                    "category": "human_action",
                    "default": True,
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        mock_instance = MagicMock()
        mock_instance.list_issues.return_value = []
        mock_issue_manager.return_value = mock_instance

        args = _make_namespace(project_dir=str(project_dir), init=True)
        execute_define_labels(args)

        output = capsys.readouterr().out
        assert "Issues initialized: 0" in output
        assert "skipped" not in output.split("Issues initialized:")[1].split("\n")[0]
