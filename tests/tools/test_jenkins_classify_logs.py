"""Tests for tools/jenkins_classify_logs.py and tools/jenkins_issue_patterns.toml."""

from __future__ import annotations

import csv
import importlib
import sys
from pathlib import Path

import pytest

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

jenkins_classify_logs = importlib.import_module("jenkins_classify_logs")

_BLOCKED = "Category: implementation_blocked\nBlocked marker found: {reason}\n"
_VERSIONS_LOG = """\
 + mcp-workspace==0.1.13
 - mcp-workspace==0.1.13
 + mcp-workspace==0.1.14.dev32+g9b084c1fe (from git+https://example.com)
mcp-coder 0.1.21.dev176+gd6e37e8da
mcp-tools-py 0.1.11.dev27+gc46e470a1
> call C:\\Jenkins\\scripts\\run-mcp-command.bat "command.bat"
mcp-coder 0.1.21.dev146+ge89a08dcf
mcp-workspace 0.1.14.dev29+gf43580bc2
mcp-tools-py 0.1.11.dev27+gc46e470a1
mcp-coder 9.9.9
mcp-coder gh-tool set-status status-failed
"""


@pytest.fixture(name="patterns", scope="module")
def fixture_patterns() -> object:
    """The real patterns file, compiled."""
    return jenkins_classify_logs.load_patterns(jenkins_classify_logs.DEFAULT_PATTERNS)


def test_patterns_file_ids_are_unique(patterns: object) -> None:
    ids = [i for i, _ in patterns.signatures] + [i for i, _ in patterns.blocked_reasons]  # type: ignore[attr-defined]
    assert len(ids) == len(set(ids))


def test_classify_signature(patterns: object) -> None:
    text = "ERROR: Maximum checkout retry attempts reached\n"
    assert jenkins_classify_logs.classify(text, patterns) == [
        "PIPE-LOCKED-VENV-BLOCKS-CHECKOUT",
        "PIPE-NO-STATUS-ON-PRE-WORKFLOW-FAILURE",
    ]


def test_classify_no_match(patterns: object) -> None:
    assert jenkins_classify_logs.classify("all good\n", patterns) == []


@pytest.mark.parametrize(
    ("reason", "sub_type"),
    [
        ("move_symbol timed out", "MC-BLOCKED-MOVE-SYMBOL"),
        ("run_format_code reformatted 85 files", "MC-BLOCKED-FORMATTER-CHURN"),
        ("The Bash tool is disabled", "MC-BLOCKED-NO-SHELL"),
        ("Unrelated test fails", "MC-BLOCKED-UNRELATED-TEST-FAIL"),
        ("something new", "MC-BLOCKED-OTHER"),
    ],
)
def test_classify_blocked_reason(patterns: object, reason: str, sub_type: str) -> None:
    text = _BLOCKED.format(reason=reason)
    assert jenkins_classify_logs.classify(text, patterns) == [
        "MC-IMPL-BLOCKED",
        sub_type,
    ]


def test_classify_blocked_first_reason_wins(patterns: object) -> None:
    text = _BLOCKED.format(reason="move_symbol failed, unrelated test also fails")
    assert (
        jenkins_classify_logs.classify(text, patterns)[-1] == "MC-BLOCKED-MOVE-SYMBOL"
    )


def test_extract_versions(patterns: object) -> None:
    assert jenkins_classify_logs.extract_versions(_VERSIONS_LOG, patterns) == {
        "venv_mcp-workspace": "0.1.14.dev32+g9b084c1fe",
        "venv_mcp-coder": "0.1.21.dev176+gd6e37e8da",
        "venv_mcp-tools-py": "0.1.11.dev27+gc46e470a1",
        "tool_mcp-coder": "0.1.21.dev146+ge89a08dcf",
        "tool_mcp-workspace": "0.1.14.dev29+gf43580bc2",
        "tool_mcp-tools-py": "0.1.11.dev27+gc46e470a1",
    }


def test_extract_versions_without_marker(patterns: object) -> None:
    assert jenkins_classify_logs.extract_versions("mcp-coder 1.0\n", patterns) == {
        "venv_mcp-coder": "1.0"
    }


def test_version_mismatch(patterns: object) -> None:
    versions = jenkins_classify_logs.extract_versions(_VERSIONS_LOG, patterns)
    assert (
        jenkins_classify_logs.version_mismatch(versions, patterns.packages)  # type: ignore[attr-defined]
        == "mcp-coder;mcp-workspace"
    )


@pytest.mark.parametrize(
    ("display_name", "repo"),
    [("mcp_coder - #1346 - implement - #2559", "mcp_coder"), ("#5", "")],
)
def test_target_repo(display_name: str, repo: str) -> None:
    assert jenkins_classify_logs.target_repo(display_name) == repo


def _write_index(logdir: Path, logs: dict[str, tuple[str, str]]) -> None:
    """Write logs and an index.csv; logs maps file name to (display_name, text)."""
    with (logdir / "index.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("file", "display_name", "number", "timestamp"))
        for number, (name, (display_name, text)) in enumerate(logs.items(), 1):
            (logdir / name).write_text(text, encoding="utf-8")
            writer.writerow((name, display_name, number, f"2026-10-0{number}T00:00"))


def test_main_tags_index_and_reports(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_index(
        tmp_path,
        {
            "a.txt": ("mcp_coder - #1 - implement - #1", _VERSIONS_LOG),
            "b.txt": (
                "AutoRunner - #2 - create-plan - #2",
                "No `project` table found in pyproject.toml\n",
            ),
        },
    )
    assert jenkins_classify_logs.main(["--logdir", str(tmp_path)]) == 0

    with (tmp_path / "index.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["repo"] == "mcp_coder"
    assert rows[0]["issue_identified"] == ""
    assert rows[0]["tool_mcp-coder"] == "0.1.21.dev146+ge89a08dcf"
    assert rows[0]["version_mismatch"] == "mcp-coder;mcp-workspace"
    assert rows[1]["issue_identified"] == (
        "PIPE-UV-SYNC-NON-PROJECT;PIPE-NO-STATUS-ON-PRE-WORKFLOW-FAILURE"
    )
    out = capsys.readouterr().out
    assert "2 logs, 1 classified" in out
    assert "Unsupported repos: AutoRunner (1 logs):" in out
    assert "Unmatched (1):\n  a.txt" in out


def test_main_rerun_keeps_columns(tmp_path: Path) -> None:
    _write_index(tmp_path, {"a.txt": ("x - #1 - implement - #1", "nothing\n")})
    assert jenkins_classify_logs.main(["--logdir", str(tmp_path)]) == 0
    first = (tmp_path / "index.csv").read_text(encoding="utf-8")
    assert jenkins_classify_logs.main(["--logdir", str(tmp_path)]) == 0
    assert (tmp_path / "index.csv").read_text(encoding="utf-8") == first


def test_main_missing_index(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert jenkins_classify_logs.main(["--logdir", str(tmp_path)]) == 1
    assert "Error reading or writing logs" in capsys.readouterr().err


def test_main_bad_patterns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.toml"
    bad.write_text("[[signature]]\nid = 'X'\nregex = '('\n", encoding="utf-8")
    assert jenkins_classify_logs.main(["--patterns", str(bad)]) == 1
    assert "Error loading patterns" in capsys.readouterr().err
