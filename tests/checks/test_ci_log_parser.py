"""Tests for CI log parser with real GitHub Actions log structure.

Tests verify that _parse_groups() and _extract_failed_step_log() correctly
capture command output that appears OUTSIDE groups (between ##[endgroup]
and the next ##[group] or ##[error] marker).

Test data sourced from CI run 23438818570 (timestamps stripped).
"""

from mcp_coder.checks.ci_log_parser import _extract_failed_step_log, _parse_groups

# ---------------------------------------------------------------------------
# Realistic log fragments from CI run 23438818570
# ---------------------------------------------------------------------------

VULTURE_LOG = (
    "##[group]Run vulture --version && ./tools/vulture_check.sh\n"
    "vulture --version && ./tools/vulture_check.sh\n"
    "shell: /usr/bin/bash -e {0}\n"
    "env:\n"
    "  UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache\n"
    "##[endgroup]\n"
    "vulture 2.15\n"
    "Checking for dead code...\n"
    "tests/cli/commands/test_verify_exit_codes.py:120: "
    "unused function '_mcp_fail' (60% confidence)\n"
    "##[error]Process completed with exit code 3."
)

FILE_SIZE_LOG = (
    "##[group]Run mcp-coder check file-size --max-lines 750 "
    "--allowlist-file .large-files-allowlist\n"
    "mcp-coder check file-size --max-lines 750 "
    "--allowlist-file .large-files-allowlist\n"
    "shell: /usr/bin/bash -e {0}\n"
    "env:\n"
    "  UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache\n"
    "##[endgroup]\n"
    "Checking file sizes in /home/runner/work/mcp_coder/mcp_coder\n"
    "File size check failed: 1 file(s) exceed 750 lines\n"
    "\n"
    "Violations:\n"
    "  - src/mcp_coder/llm/mlflow_logger.py: 774 lines\n"
    "\n"
    "Consider refactoring these files or adding them to the allowlist.\n"
    "##[error]Process completed with exit code 1."
)


class TestParseGroupsCapturesOutput:
    """Tests for _parse_groups() capturing lines outside group markers."""

    def test_captures_output_between_endgroup_and_next_group(self) -> None:
        """Lines between ##[endgroup] and ##[group] attach to preceding group."""
        log = (
            "##[group]Step A\n"
            "setup line\n"
            "##[endgroup]\n"
            "output line 1\n"
            "output line 2\n"
            "##[group]Step B\n"
            "other setup\n"
            "##[endgroup]"
        )
        groups = _parse_groups(log)

        assert len(groups) == 2
        label_a, lines_a = groups[0]
        assert label_a == "Step A"
        assert "output line 1" in lines_a
        assert "output line 2" in lines_a

    def test_captures_output_between_endgroup_and_error(self) -> None:
        """Lines between ##[endgroup] and ##[error] attach to preceding group."""
        groups = _parse_groups(VULTURE_LOG)

        assert len(groups) == 1
        label, lines = groups[0]
        assert label.startswith("Run vulture")
        assert "vulture 2.15" in lines
        assert "Checking for dead code..." in lines
        assert any("unused function" in ln for ln in lines)
        assert any(ln.startswith("##[error]") for ln in lines)

    def test_captures_blank_lines_in_output(self) -> None:
        """Blank lines in command output are preserved."""
        groups = _parse_groups(FILE_SIZE_LOG)

        assert len(groups) == 1
        _, lines = groups[0]
        # The file-size log has blank lines between output sections
        assert "" in lines

    def test_output_attaches_to_correct_group(self) -> None:
        """With multiple groups, outside lines attach to the preceding group only."""
        log = (
            "##[group]First\n"
            "inside first\n"
            "##[endgroup]\n"
            "after first\n"
            "##[group]Second\n"
            "inside second\n"
            "##[endgroup]\n"
            "after second\n"
        )
        groups = _parse_groups(log)

        assert len(groups) == 2
        _, lines_first = groups[0]
        _, lines_second = groups[1]

        assert "after first" in lines_first
        assert "after first" not in lines_second
        assert "after second" in lines_second
        assert "after second" not in lines_first


class TestExtractFailedStepLogRealStructure:
    """Tests for _extract_failed_step_log() with real CI log structure."""

    def test_vulture_real_log_structure(self) -> None:
        """Vulture failure log includes command output from outside the group."""
        result = _extract_failed_step_log(
            VULTURE_LOG,
            "Run vulture --version && ./tools/vulture_check.sh",
        )

        assert "vulture 2.15" in result
        assert "Checking for dead code..." in result
        assert "unused function '_mcp_fail'" in result
        assert "##[error]Process completed with exit code 3." in result

    def test_file_size_real_log_structure(self) -> None:
        """File-size failure log includes command output from outside the group."""
        result = _extract_failed_step_log(
            FILE_SIZE_LOG,
            "Run mcp-coder check file-size",
        )

        assert "File size check failed" in result
        assert "Violations:" in result
        assert "mlflow_logger.py: 774 lines" in result
        assert "Consider refactoring" in result
        assert "##[error]Process completed with exit code 1." in result

    def test_error_fallback_with_outside_output(self) -> None:
        """Unknown step name falls back to error-group matching with output."""
        # Combine both logs to have multiple groups
        combined = VULTURE_LOG + "\n" + FILE_SIZE_LOG

        result = _extract_failed_step_log(combined, "nonexistent-step")

        # Fallback collects groups that contain ##[error] lines
        assert "vulture 2.15" in result
        assert "File size check failed" in result
