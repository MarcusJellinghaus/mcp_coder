"""Tests for _format_section output formatting (Decision 10)."""

from typing import Any

import pytest

from mcp_coder.cli.commands.verify_formatting import (
    _VALUE_COLUMN_INDENT,
    _format_row,
    _format_section,
)


class TestFormatSection:
    """Tests for _format_section output formatting (Decision 10)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_ok_entry_formatted_with_success_symbol(self) -> None:
        """Entries with ok=True show [OK] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": True, "value": "YES"},
            "overall_ok": True,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert _format_row("Claude CLI Found", "[OK]", "YES", indent=2) in output

    def test_failed_entry_formatted_with_failure_symbol(self) -> None:
        """Entries with ok=False show [ERR] symbol and value."""
        result: dict[str, Any] = {
            "cli_found": {"ok": False, "value": "NO"},
            "overall_ok": False,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        assert _format_row("Claude CLI Found", "[ERR]", "NO", indent=2) in output

    def test_skipped_entry_formatted(self) -> None:
        """Entries with ok=None show warning indicator."""
        result: dict[str, Any] = {
            "test_prompt": {"ok": None, "value": "skipped (no API key)", "error": None},
            "overall_ok": True,
        }
        output = _format_section("TEST", result, self._symbols())
        assert "[WARN]" in output
        assert "skipped (no API key)" in output

    def test_error_shown_on_failure(self) -> None:
        """Error message appended when ok=False and error is present."""
        result: dict[str, Any] = {
            "api_integration": {"ok": False, "value": "FAILED", "error": "not found"},
            "overall_ok": False,
        }
        output = _format_section("TEST", result, self._symbols())
        assert (
            _format_row("API Integration", "[ERR]", "FAILED (not found)", indent=2)
            in output
        )

    def test_section_title_in_header(self) -> None:
        """Section header contains the title."""
        result: dict[str, Any] = {"overall_ok": True}
        output = _format_section("MY SECTION", result, self._symbols())
        assert "=== MY SECTION " in output

    def test_install_hint_rendered_inline(self) -> None:
        """When entry has install_hint and ok=False, hint appears indented below."""
        result: dict[str, Any] = {
            "backend_package": {
                "ok": False,
                "value": "not installed",
                "install_hint": "pip install langchain-openai",
            },
            "overall_ok": False,
        }
        output = _format_section("TEST", result, self._symbols())
        assert (
            _format_row("Backend package", "[ERR]", "not installed", indent=2) in output
        )
        # Continuation line aligned under value column
        expected_hint_line = (
            f"{' ' * _VALUE_COLUMN_INDENT}-> pip install langchain-openai"
        )
        assert expected_hint_line in output


class TestBranchProtectionNesting:
    """Tests for branch protection nested rendering in _format_section (#899)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_children_indented_when_parent_ok(self) -> None:
        """Children render at 4-space indent under parent when ok=True."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": True, "value": "main protected"},
            "ci_checks_required": {"ok": True, "value": "8 checks configured"},
            "strict_mode": {"ok": True, "value": "enabled"},
            "force_push": {"ok": True, "value": "disabled"},
            "branch_deletion": {"ok": True, "value": "disabled"},
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        lines = output.split("\n")
        # Parent at 2-space indent
        parent_lines = [l for l in lines if "Branch protection" in l]
        assert len(parent_lines) == 1
        assert parent_lines[0].startswith("  ")
        assert "[OK]" in parent_lines[0]
        # Children at 4-space indent
        for child_label in ("CI checks required", "Force push", "Branch deletion"):
            child_lines = [l for l in lines if child_label in l]
            assert len(child_lines) == 1, f"Expected 1 line for {child_label}"
            assert child_lines[0].startswith(
                "    "
            ), f"{child_label} should be at 4-space indent"

    def test_children_suppressed_when_parent_fails(self) -> None:
        """Only parent line appears when branch_protection ok=False."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": False, "value": "main is not protected"},
            "ci_checks_required": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "strict_mode": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "force_push": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "branch_deletion": {
                "ok": False,
                "value": "unknown",
                "error": "no protection",
            },
            "overall_ok": False,
        }
        output = _format_section("GITHUB", result, self._symbols())
        # Parent line present
        assert "Branch protection" in output
        # Children suppressed
        assert "CI checks required" not in output
        assert "Strict mode" not in output
        assert "Force push" not in output
        assert "Branch deletion" not in output

    def test_strict_mode_no_symbol(self) -> None:
        """strict_mode renders value only — no [OK]/[ERR]/[WARN] symbol."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": True, "value": "main protected"},
            "ci_checks_required": {"ok": True, "value": "8 checks configured"},
            "strict_mode": {"ok": True, "value": "enabled"},
            "force_push": {"ok": True, "value": "disabled"},
            "branch_deletion": {"ok": True, "value": "disabled"},
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        lines = output.split("\n")
        strict_lines = [l for l in lines if "Strict mode" in l]
        assert len(strict_lines) == 1
        strict_line = strict_lines[0]
        assert "enabled" in strict_line
        assert "[OK]" not in strict_line
        assert "[ERR]" not in strict_line
        assert "[WARN]" not in strict_line

    def test_non_github_section_unaffected(self) -> None:
        """Claude section entries remain flat at 2-space indent."""
        result: dict[str, Any] = {
            "cli_found": {"ok": True, "value": "YES"},
            "cli_version": {"ok": True, "value": "1.0.0"},
            "overall_ok": True,
        }
        output = _format_section("BASIC VERIFICATION", result, self._symbols())
        lines = output.split("\n")
        content_lines = [l for l in lines if l.strip() and not l.startswith("===")]
        for line in content_lines:
            assert line.startswith("  "), f"Expected 2-space indent: {line!r}"
            assert not line.startswith(
                "    "
            ), f"Non-GitHub entry should not be at 4-space indent: {line!r}"


class TestGitHubLabelMappings:
    """Tests for GitHub label mappings in _format_section (Step 2)."""

    _GITHUB_KEYS = (
        "api_base_url",
        "network_proxy",
        "token_configured",
        "authenticated_user",
        "repo_url",
        "repo_accessible",
        "branch_protection",
        "ci_checks_required",
        "strict_mode",
        "force_push",
        "branch_deletion",
        "auto_delete_branches",
        "perm_contents_read",
        "perm_administration_read",
        "perm_pull_requests_read",
        "perm_issues_read",
        "perm_workflows_read",
        "perm_statuses_read",
    )

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_all_github_keys_in_label_map(self) -> None:
        """All GitHub check keys exist in _LABEL_MAP."""
        from mcp_coder.cli.commands.verify_formatting import _LABEL_MAP

        for key in self._GITHUB_KEYS:
            assert key in _LABEL_MAP, f"Missing key: {key}"

    def test_format_section_renders_github_labels(self) -> None:
        """_format_section renders human-readable labels for GitHub entries."""
        result: dict[str, Any] = {
            "token_configured": {"ok": True, "value": "YES"},
            "repo_accessible": {"ok": True, "value": "owner/repo"},
            "network_proxy": {
                "ok": False,
                "value": "api=api.x.ghe.com:443 tcp=timeout proxy_env=HTTPS_PROXY pac=present",
            },
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert "Token configured" in output
        assert "Repo accessible" in output
        assert "Network / proxy" in output  # labeled row present
        assert "network_proxy" not in output  # raw key does not leak
        assert "[OK]" in output
        assert "[ERR]" in output  # failed probe renders [ERR] (ok=False)

    def test_format_section_github_error_entry(self) -> None:
        """Entry with ok=False renders [ERR] symbol."""
        result: dict[str, Any] = {
            "token_configured": {
                "ok": False,
                "value": "not set",
                "error": "GITHUB_TOKEN not found",
            },
            "overall_ok": False,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert "Token configured" in output
        assert "[ERR]" in output
        assert "GITHUB_TOKEN not found" in output


class TestGitLabelMappings:
    """Tests for GIT section label mappings and rendering."""

    _GIT_KEYS = (
        "git_binary",
        "git_repo",
        "user_identity",
        "signing_intent",
        "signing_consistency",
        "signing_format",
        "signing_key",
        "signing_binary",
        "signing_key_accessible",
        "agent_reachable",
        "allowed_signers",
        "verify_head",
        "actual_signature",
    )

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def test_all_git_keys_in_label_map(self) -> None:
        from mcp_coder.cli.commands.verify_formatting import _LABEL_MAP

        for key in self._GIT_KEYS:
            assert key in _LABEL_MAP, f"Missing key: {key}"

    def test_format_section_renders_git_section(self) -> None:
        result: dict[str, Any] = {
            "git_binary": {"ok": True, "value": "git 2.45.0"},
            "signing_intent": {"ok": True, "value": "not configured"},
            "signing_key": {
                "ok": False,
                "value": "missing",
                "error": "user.signingkey unset",
            },
            "overall_ok": False,
        }
        output = _format_section("GIT", result, self._symbols())
        assert "=== GIT " in output
        assert "Git binary" in output
        assert "Signing enabled" in output
        assert "Signing key" in output
        assert "[OK]" in output
        assert "[ERR]" in output
        assert "user.signingkey unset" in output


class TestAutoDeleteBranches:
    """Tests for auto_delete_branches rendering at top level of GITHUB section (#917)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    @pytest.mark.parametrize(
        "entry, marker, value",
        [
            ({"ok": True, "value": "enabled"}, "[OK]", "enabled"),
            ({"ok": False, "value": "disabled"}, "[ERR]", "disabled"),
            (
                {
                    "ok": False,
                    "value": "unknown",
                    "error": "repository not accessible",
                },
                "[ERR]",
                "unknown (repository not accessible)",
            ),
        ],
    )
    def test_auto_delete_branches_value_cases(
        self, entry: dict[str, Any], marker: str, value: str
    ) -> None:
        """Top-level rendering: 2-space indent, symbol from ok, value, optional error suffix."""
        result: dict[str, Any] = {
            "auto_delete_branches": entry,
            "overall_ok": entry["ok"] is True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        expected_line = _format_row("Auto-delete branches", marker, value, indent=2)
        assert expected_line in output

    def test_renders_when_branch_protection_failed(self) -> None:
        """auto_delete_branches must NOT be suppressed when branch_protection.ok=False."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": False, "value": "main is not protected"},
            "auto_delete_branches": {"ok": True, "value": "enabled"},
            "overall_ok": False,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert (
            _format_row("Auto-delete branches", "[OK]", "enabled", indent=2) in output
        )


class TestApiBaseUrlRendering:
    """Tests for api_base_url row rendering in GITHUB section (#933)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    @pytest.mark.parametrize(
        "entry, marker, value",
        [
            pytest.param(
                {"ok": True, "value": "https://api.example.ghe.com"},
                "[OK]",
                "https://api.example.ghe.com",
                id="success-renders-ok",
            ),
            pytest.param(
                {
                    "ok": False,
                    "severity": "warning",
                    "value": "https://api.github.com (fallback - identifier unresolved)",
                    "error": "Could not determine repository URL from git remote",
                },
                "[ERR]",
                "https://api.github.com (fallback - identifier unresolved) "
                "(Could not determine repository URL from git remote)",
                id="fallback-severity-warning-renders-err",
            ),
        ],
    )
    def test_api_base_url_value_cases(
        self, entry: dict[str, Any], marker: str, value: str
    ) -> None:
        """api_base_url renders symbol from ok and precedes Token configured."""
        result: dict[str, Any] = {
            "api_base_url": entry,
            "token_configured": {"ok": True, "value": "configured"},
            "overall_ok": entry["ok"] is True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        expected_line = _format_row("API base URL", marker, value, indent=2)
        assert expected_line in output
        api_idx = output.find("API base URL")
        token_idx = output.find("Token configured")
        assert 0 <= api_idx < token_idx


class TestTokenFingerprintSuffix:
    """Tests for token_fingerprint suffix in GITHUB section (#933)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    @pytest.mark.parametrize(
        "fingerprint, expected_in_suffix",
        [
            pytest.param(
                "ghp_...a3f9",
                "from ~/.mcp_coder/config.toml (ghp_...a3f9)",
                id="normal-token",
            ),
            pytest.param(
                "****",
                "from ~/.mcp_coder/config.toml (****)",
                id="short-token-sentinel",
            ),
            pytest.param(
                None,
                None,
                id="fingerprint-absent",
            ),
        ],
    )
    def test_fingerprint_appended_when_present(
        self, fingerprint: str | None, expected_in_suffix: str | None
    ) -> None:
        """Fingerprint is appended in parens to the 'from <source>' suffix."""
        entry: dict[str, Any] = {
            "ok": True,
            "value": "configured (scopes: repo)",
            "token_source": "config",
        }
        if fingerprint is not None:
            entry["token_fingerprint"] = fingerprint
        result: dict[str, Any] = {
            "token_configured": entry,
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert "from ~/.mcp_coder/config.toml" in output
        if expected_in_suffix is None:
            assert "from ~/.mcp_coder/config.toml (" not in output
        else:
            assert expected_in_suffix in output


_PERM_LABELS: tuple[str, ...] = (
    "Contents: Read",
    "Administration: Read",
    "Pull requests: Read",
    "Issues: Read",
    "Actions: Read",
    "Commit statuses: Read",
)


class TestPermissionProbes:
    """Tests for [Permissions] subsection rendering (#946)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    def _all_ok_result(self) -> dict[str, Any]:
        return {
            "auto_delete_branches": {"ok": True, "value": "enabled"},
            "perm_contents_read": {"ok": True, "value": "granted"},
            "perm_administration_read": {"ok": True, "value": "granted"},
            "perm_pull_requests_read": {"ok": True, "value": "granted"},
            "perm_issues_read": {"ok": True, "value": "granted"},
            "perm_workflows_read": {"ok": True, "value": "granted"},
            "perm_statuses_read": {"ok": True, "value": "granted"},
            "overall_ok": True,
        }

    @pytest.mark.parametrize(
        "scenario",
        ["all-ok", "one-missing", "repo-inaccessible"],
    )
    def test_perm_rows_rendered(self, scenario: str) -> None:
        """Each parametrized scenario renders the 6 perm_* rows correctly."""
        if scenario == "all-ok":
            result = self._all_ok_result()
            output = _format_section("GITHUB", result, self._symbols())
            for label in _PERM_LABELS:
                assert (
                    _format_row(label, "[OK]", "granted", indent=4) in output
                ), f"Missing OK row for {label}"
        elif scenario == "one-missing":
            result = self._all_ok_result()
            result["perm_workflows_read"] = {
                "ok": False,
                "value": "denied",
                "error": "https://docs.github.com/...#workflows",
            }
            output = _format_section("GITHUB", result, self._symbols())
            assert "[ERR]" in output
            assert "https://docs.github.com/...#workflows" in output
            for label in _PERM_LABELS:
                if label == "Actions: Read":
                    continue
                assert (
                    _format_row(label, "[OK]", "granted", indent=4) in output
                ), f"Missing OK row for {label}"
        else:
            assert scenario == "repo-inaccessible"
            err = "repository not accessible"
            result = {
                "auto_delete_branches": {"ok": True, "value": "enabled"},
                "perm_contents_read": {
                    "ok": False,
                    "value": "not checked",
                    "error": err,
                },
                "perm_administration_read": {
                    "ok": False,
                    "value": "not checked",
                    "error": err,
                },
                "perm_pull_requests_read": {
                    "ok": False,
                    "value": "not checked",
                    "error": err,
                },
                "perm_issues_read": {
                    "ok": False,
                    "value": "not checked",
                    "error": err,
                },
                "perm_workflows_read": {
                    "ok": False,
                    "value": "not checked",
                    "error": err,
                },
                "perm_statuses_read": {
                    "ok": False,
                    "value": "not checked",
                    "error": err,
                },
                "overall_ok": False,
            }
            output = _format_section("GITHUB", result, self._symbols())
            for label in _PERM_LABELS:
                expected = _format_row(label, "[ERR]", f"not checked ({err})", indent=4)
                assert expected in output, f"Missing ERR row for {label}"

    def test_header_appears_once_and_after_auto_delete_branches(self) -> None:
        """[Permissions] header appears exactly once and after Auto-delete branches."""
        result = self._all_ok_result()
        output = _format_section("GITHUB", result, self._symbols())
        assert output.count("[Permissions]") == 1
        auto_idx = output.find("Auto-delete branches")
        header_idx = output.find("[Permissions]")
        assert auto_idx >= 0
        assert header_idx > auto_idx
        last_perm_idx = max(output.find(label) for label in _PERM_LABELS)
        assert last_perm_idx > auto_idx

    def test_perm_workflows_read_label_aligns_at_label_width(self) -> None:
        """perm_* rows are rendered at indent=4 with the standard label width."""
        result = self._all_ok_result()
        output = _format_section("GITHUB", result, self._symbols())
        expected_line = _format_row("Actions: Read", "[OK]", "granted", indent=4)
        assert expected_line in output
        for line in output.split("\n"):
            if "Actions: Read" in line:
                assert line == expected_line
                break
        else:
            raise AssertionError("Actions: Read row not found in output")
