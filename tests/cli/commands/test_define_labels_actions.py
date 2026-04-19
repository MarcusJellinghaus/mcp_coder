"""Tests for GitHub Action workflow generation in define_labels_actions.

Tests cover:
- build_promotions() function
- generate_label_new_issues_yml() function
- generate_approve_command_yml() function
- write_github_actions() function
"""

import logging
from pathlib import Path
from typing import Any

import pytest
import yaml

from mcp_coder.cli.commands.define_labels_actions import (
    build_promotions,
    generate_approve_command_yml,
    generate_label_new_issues_yml,
    write_github_actions,
)


class TestBuildPromotions:
    """Test build_promotions() function."""

    def test_builds_from_promotable_labels(self) -> None:
        """Extracts (current, next) pairs from promotable: true labels."""
        config: dict[str, Any] = {
            "workflow_labels": [
                {"name": "status-01:created", "promotable": True},
                {"name": "status-02:awaiting-planning"},
                {"name": "status-03:planning"},
                {"name": "status-04:plan-review", "promotable": True},
                {"name": "status-05:plan-ready"},
                {"name": "status-06:implementing"},
                {"name": "status-07:code-review", "promotable": True},
                {"name": "status-08:ready-pr"},
            ]
        }
        result = build_promotions(config)
        assert result == [
            ("status-01:created", "status-02:awaiting-planning"),
            ("status-04:plan-review", "status-05:plan-ready"),
            ("status-07:code-review", "status-08:ready-pr"),
        ]

    def test_empty_when_no_promotable(self) -> None:
        """Returns empty list when no labels are promotable."""
        config: dict[str, Any] = {
            "workflow_labels": [
                {"name": "status-01:created"},
                {"name": "status-02:awaiting-planning"},
            ]
        }
        result = build_promotions(config)
        assert result == []

    def test_last_label_promotable_ignored(self) -> None:
        """Last label with promotable: true has no next, so it's skipped."""
        config: dict[str, Any] = {
            "workflow_labels": [
                {"name": "status-01:created"},
                {"name": "status-02:awaiting-planning", "promotable": True},
            ]
        }
        result = build_promotions(config)
        assert result == []


class TestGenerateLabelNewIssuesYml:
    """Test generate_label_new_issues_yml() function."""

    def test_contains_default_label(self) -> None:
        """Generated YAML references the default label name."""
        content = generate_label_new_issues_yml("status-01:created")
        assert "status-01:created" in content

    def test_valid_yaml_structure(self) -> None:
        """Generated content is valid YAML with expected structure."""
        content = generate_label_new_issues_yml("status-01:created")
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "Label New Issues"
        # YAML parses 'on' as boolean True
        assert "issues" in parsed[True]
        assert "add-label" in parsed["jobs"]

    def test_uses_github_script_action(self) -> None:
        """Generated YAML uses actions/github-script."""
        content = generate_label_new_issues_yml("status-01:created")
        assert "actions/github-script@" in content

    def test_different_default_label(self) -> None:
        """Works with a non-standard default label name."""
        content = generate_label_new_issues_yml("my-custom-label")
        assert "my-custom-label" in content
        assert "status-01:created" not in content


class TestGenerateApproveCommandYml:
    """Test generate_approve_command_yml() function."""

    def test_contains_promotion_paths(self) -> None:
        """Generated YAML includes all promotion source/target pairs."""
        promotions = [
            ("status-01:created", "status-02:awaiting-planning"),
            ("status-04:plan-review", "status-05:plan-ready"),
        ]
        content = generate_approve_command_yml(promotions)
        assert "status-01:created" in content
        assert "status-02:awaiting-planning" in content
        assert "status-04:plan-review" in content
        assert "status-05:plan-ready" in content

    def test_valid_yaml_structure(self) -> None:
        """Generated content is valid YAML with expected structure."""
        promotions = [
            ("status-01:created", "status-02:awaiting-planning"),
        ]
        content = generate_approve_command_yml(promotions)
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "Approve Command"
        # YAML parses 'on' as boolean True
        assert "issue_comment" in parsed[True]
        assert "handle-approve" in parsed["jobs"]

    def test_empty_promotions(self) -> None:
        """Works with empty promotions list."""
        content = generate_approve_command_yml([])
        parsed = yaml.safe_load(content)
        assert parsed is not None


class TestWriteGithubActions:
    """Test write_github_actions() function."""

    def _make_config(self) -> dict[str, Any]:
        """Build a minimal config with default and promotable labels."""
        return {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "default": True,
                    "promotable": True,
                },
                {"name": "status-02:awaiting-planning"},
            ]
        }

    def test_writes_two_files(self, tmp_path: Path) -> None:
        """Writes label-new-issues.yml and approve-command.yml."""
        config = self._make_config()
        result = write_github_actions(tmp_path, config)

        assert len(result) == 2
        workflows_dir = tmp_path / ".github" / "workflows"
        assert (workflows_dir / "label-new-issues.yml").exists()
        assert (workflows_dir / "approve-command.yml").exists()

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """With dry_run=True, no files are created."""
        config = self._make_config()
        result = write_github_actions(tmp_path, config, dry_run=True)

        assert len(result) == 2
        workflows_dir = tmp_path / ".github" / "workflows"
        assert not workflows_dir.exists()

    def test_overwrites_existing_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Existing files are overwritten with a warning logged."""
        config = self._make_config()
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "label-new-issues.yml").write_text("old content")

        with caplog.at_level(logging.WARNING):
            write_github_actions(tmp_path, config)

        assert "Overwriting" in caplog.text
        # File should have new content
        content = (workflows_dir / "label-new-issues.yml").read_text()
        assert "old content" not in content

    def test_creates_workflows_directory(self, tmp_path: Path) -> None:
        """Creates .github/workflows/ if it doesn't exist."""
        config = self._make_config()
        assert not (tmp_path / ".github").exists()

        write_github_actions(tmp_path, config)

        assert (tmp_path / ".github" / "workflows").is_dir()

    def test_returns_file_paths(self, tmp_path: Path) -> None:
        """Returns list of written file paths as strings."""
        config = self._make_config()
        result = write_github_actions(tmp_path, config)

        assert any("label-new-issues.yml" in p for p in result)
        assert any("approve-command.yml" in p for p in result)
