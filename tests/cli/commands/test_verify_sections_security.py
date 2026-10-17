"""Tests for the GITHUB SECURITY section's local-file checks.

Split from the orchestration tests: these exercise the deterministic
local-file checks directly, with no CLI wiring or mocked HTTP calls.
"""

from pathlib import Path

from mcp_coder.cli.commands.verify_sections import (
    _check_codeql_workflow,
    _check_dependabot_config,
    _derive_code_scanning_alerts,
)
from mcp_coder.mcp_workspace_github import CheckResult


def _write_dependabot(project_dir: Path, content: str) -> None:
    github_dir = project_dir / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    (github_dir / "dependabot.yml").write_text(content, encoding="utf-8")


class TestCheckDependabotConfig:
    """``_check_dependabot_config`` reads ``.github/dependabot.yml``."""

    def test_missing_file_returns_false(self, tmp_path: Path) -> None:
        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is False
        assert result["value"] == "not present"
        assert result["severity"] == "warning"

    def test_invalid_yaml_returns_false(self, tmp_path: Path) -> None:
        _write_dependabot(tmp_path, "updates: [unterminated")

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is False
        assert "invalid YAML" in result["value"]

    def test_no_updates_key_returns_false(self, tmp_path: Path) -> None:
        _write_dependabot(tmp_path, "version: 2\n")

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is False
        assert result["value"] == "no ecosystems configured"

    def test_empty_updates_list_returns_false(self, tmp_path: Path) -> None:
        _write_dependabot(tmp_path, "version: 2\nupdates: []\n")

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is False
        assert result["value"] == "no ecosystems configured"

    def test_single_ecosystem(self, tmp_path: Path) -> None:
        _write_dependabot(
            tmp_path,
            "version: 2\n"
            "updates:\n"
            '  - package-ecosystem: "pip"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n',
        )

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is True
        assert "pip: weekly" in result["value"]

    def test_multi_ecosystem_uniform_schedule(self, tmp_path: Path) -> None:
        _write_dependabot(
            tmp_path,
            "version: 2\n"
            "updates:\n"
            '  - package-ecosystem: "pip"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n'
            '  - package-ecosystem: "npm"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n',
        )

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is True
        assert "pip, npm: weekly" in result["value"]

    def test_multi_ecosystem_mixed_schedule(self, tmp_path: Path) -> None:
        _write_dependabot(
            tmp_path,
            "version: 2\n"
            "updates:\n"
            '  - package-ecosystem: "pip"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n'
            '  - package-ecosystem: "npm"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "daily"\n',
        )

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is True
        assert "pip: weekly, npm: daily" in result["value"]

    def test_unreadable_file_returns_false(self, tmp_path: Path) -> None:
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "dependabot.yml").write_bytes(b"\xff\xfe\x00bad\x80")

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is False
        assert result["value"] == "unreadable"

    def test_yaml_extension_accepted(self, tmp_path: Path) -> None:
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "dependabot.yaml").write_text(
            "version: 2\nupdates:\n"
            '  - package-ecosystem: "pip"\n'
            "    schedule:\n"
            '      interval: "weekly"\n',
            encoding="utf-8",
        )

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is True
        assert ".github/dependabot.yaml (pip: weekly)" in result["value"]

    def test_yml_preferred_over_yaml(self, tmp_path: Path) -> None:
        _write_dependabot(
            tmp_path,
            "version: 2\nupdates:\n"
            '  - package-ecosystem: "pip"\n'
            "    schedule:\n"
            '      interval: "weekly"\n',
        )
        (tmp_path / ".github" / "dependabot.yaml").write_text(
            "version: 2\n", encoding="utf-8"
        )

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is True
        assert "dependabot.yml (pip" in result["value"]

    def test_updates_without_valid_entries_returns_false(self, tmp_path: Path) -> None:
        _write_dependabot(tmp_path, "version: 2\nupdates:\n  - foo\n  - 42\n")

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is False
        assert result["value"] == "no ecosystems configured"

    def test_null_schedule_does_not_crash(self, tmp_path: Path) -> None:
        _write_dependabot(
            tmp_path,
            "version: 2\n"
            "updates:\n"
            '  - package-ecosystem: "pip"\n'
            '    directory: "/"\n'
            "    schedule:\n",
        )

        result = _check_dependabot_config(tmp_path)

        assert result["ok"] is True
        assert "pip: ?" in result["value"]


def _write_workflow(project_dir: Path, filename: str, content: str) -> None:
    workflows_dir = project_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / filename).write_text(content, encoding="utf-8")


class TestCheckCodeqlWorkflow:
    """``_check_codeql_workflow`` scans workflow files for a CodeQL step."""

    def test_no_workflows_dir_returns_false(self, tmp_path: Path) -> None:
        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is False
        assert result["value"] == "no workflow step uses github/codeql-action"
        assert result["severity"] == "warning"

    def test_workflow_with_unrelated_content_returns_false(
        self, tmp_path: Path
    ) -> None:
        _write_workflow(
            tmp_path,
            "ci.yml",
            "name: CI\non: push\njobs:\n  build:\n    steps:\n      - uses: actions/checkout@v4\n",
        )

        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is False
        assert result["value"] == "no workflow step uses github/codeql-action"

    def test_codeql_step_in_non_obvious_filename(self, tmp_path: Path) -> None:
        _write_workflow(
            tmp_path,
            "build.yml",
            "name: Build\non: push\njobs:\n  build:\n    steps:\n      - uses: github/codeql-action/analyze@v3\n",
        )

        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is True
        assert result["value"] == "found in build.yml"

    def test_quoted_uses_value(self, tmp_path: Path) -> None:
        _write_workflow(
            tmp_path,
            "build.yml",
            'name: Build\non: push\njobs:\n  build:\n    steps:\n      - uses: "github/codeql-action/analyze@v3"\n',
        )

        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is True
        assert result["value"] == "found in build.yml"

    def test_commented_out_uses_not_detected(self, tmp_path: Path) -> None:
        _write_workflow(
            tmp_path,
            "build.yml",
            "name: Build\non: push\njobs:\n  build:\n    steps:\n"
            "      # - uses: github/codeql-action/analyze@v3\n"
            "      - uses: actions/checkout@v4\n",
        )

        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is False

    def test_uses_text_inside_run_not_detected(self, tmp_path: Path) -> None:
        _write_workflow(
            tmp_path,
            "build.yml",
            "name: Build\non: push\njobs:\n  build:\n    steps:\n"
            "      - run: |\n"
            "          echo uses: github/codeql-action/analyze@v3\n",
        )

        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is False

    def test_invalid_yaml_workflow_skipped(self, tmp_path: Path) -> None:
        _write_workflow(tmp_path, "a.yml", "jobs: [unterminated")
        _write_workflow(tmp_path, "b.yml", "- just\n- a list\n")
        _write_workflow(tmp_path, "c.yml", "jobs:\n  x: null\n  y:\n    steps: 3\n")

        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is False

    def test_non_utf8_file_skipped_and_others_scanned(self, tmp_path: Path) -> None:
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "a.yml").write_bytes(b"\xff\xfe\x00bad\x80")
        _write_workflow(
            tmp_path,
            "b.yml",
            "jobs:\n  build:\n    steps:\n      - uses: github/codeql-action/analyze@v3\n",
        )

        result = _check_codeql_workflow(tmp_path)

        assert result["ok"] is True
        assert result["value"] == "found in b.yml"


class TestDeriveCodeScanningAlerts:
    """``_derive_code_scanning_alerts`` reflects the CodeQL row's ``ok`` only."""

    def test_codeql_present_yields_configured(self) -> None:
        codeql_result = CheckResult(
            ok=True, value="found in ci.yml", severity="warning"
        )

        result = _derive_code_scanning_alerts(codeql_result)

        assert result["ok"] is None
        assert "configured" in result["value"]

    def test_codeql_absent_yields_not_configured(self) -> None:
        codeql_result = CheckResult(
            ok=False,
            value="no workflow step uses github/codeql-action",
            severity="warning",
        )

        result = _derive_code_scanning_alerts(codeql_result)

        assert result["ok"] is None
        assert result["value"] == "not configured (no CodeQL workflow)"
