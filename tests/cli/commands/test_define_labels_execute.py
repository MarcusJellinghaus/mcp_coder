"""Tests for define_labels execute function exit codes.

Tests cover:
- Exit code 0 on success
- Exit code 1 on errors
- Exit code 2 on warnings only
- Error precedence over warnings
"""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.cli.commands.define_labels import execute_define_labels


class TestExecuteDefineLabelsExitCodes:
    """Test exit codes from execute_define_labels."""

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_returns_zero_on_success(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful execution returns 0."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "internal_id": "created",
                    "category": "human_action",
                    "color": "10b981",
                    "description": "Test",
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

        # Setup mock issue manager to return no issues
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = []
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        assert result == 0

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_returns_one_on_errors(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test execution with errors returns 1."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "internal_id": "created",
                    "category": "human_action",
                    "color": "10b981",
                    "description": "Test",
                },
                {
                    "name": "status-03:planning",
                    "internal_id": "planning",
                    "category": "bot_busy",
                    "color": "a7f3d0",
                    "description": "Planning",
                    "stale_timeout_minutes": 15,
                },
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created", "status-03:planning"],
        }

        # Setup mock issue manager to return an issue with multiple labels (error)
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = [
            {
                "number": 45,
                "title": "Issue with multiple labels",
                "body": "",
                "state": "open",
                "labels": ["status-01:created", "status-03:planning"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            }
        ]
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        assert result == 1

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_returns_two_on_warnings_only(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test execution with warnings only returns 2."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-06:implementing",
                    "internal_id": "implementing",
                    "category": "bot_busy",
                    "color": "bfdbfe",
                    "description": "Implementing",
                    "stale_timeout_minutes": 120,
                },
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-06:implementing"],
        }

        # Create stale timestamp (150 minutes ago, over 120 min threshold)
        stale_timestamp = (
            datetime.now(timezone.utc) - timedelta(minutes=150)
        ).isoformat()

        # Setup mock issue manager to return an issue with stale bot_busy label
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = [
            {
                "number": 78,
                "title": "Stale implementing issue",
                "body": "",
                "state": "open",
                "labels": ["status-06:implementing"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            }
        ]
        mock_issue_manager.get_issue_events.return_value = [
            {
                "event": "labeled",
                "label": "status-06:implementing",
                "created_at": stale_timestamp,
                "actor": "bot",
            }
        ]
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        assert result == 2

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_errors_take_precedence_over_warnings(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that errors (exit code 1) take precedence over warnings (exit code 2)."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "internal_id": "created",
                    "category": "human_action",
                    "color": "10b981",
                    "description": "Test",
                },
                {
                    "name": "status-03:planning",
                    "internal_id": "planning",
                    "category": "bot_busy",
                    "color": "a7f3d0",
                    "description": "Planning",
                    "stale_timeout_minutes": 15,
                },
                {
                    "name": "status-06:implementing",
                    "internal_id": "implementing",
                    "category": "bot_busy",
                    "color": "bfdbfe",
                    "description": "Implementing",
                    "stale_timeout_minutes": 120,
                },
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": [
                "status-01:created",
                "status-03:planning",
                "status-06:implementing",
            ],
        }

        # Create stale timestamp for warning
        stale_timestamp = (
            datetime.now(timezone.utc) - timedelta(minutes=150)
        ).isoformat()

        # Setup mock issue manager with both error and warning issues
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = [
            # Issue with multiple labels (error)
            {
                "number": 45,
                "title": "Issue with multiple labels",
                "body": "",
                "state": "open",
                "labels": ["status-01:created", "status-03:planning"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            # Stale issue (warning)
            {
                "number": 78,
                "title": "Stale implementing issue",
                "body": "",
                "state": "open",
                "labels": ["status-06:implementing"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        mock_issue_manager.get_issue_events.return_value = [
            {
                "event": "labeled",
                "label": "status-06:implementing",
                "created_at": stale_timestamp,
                "actor": "bot",
            }
        ]
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        # Errors take precedence, so should return 1 not 2
        assert result == 1
