"""Unit tests for tools/mlflow/extract_interactive_events.py.

Covers the pure helpers: project-dir sanitisation, tool classification, Bash
verb/allow-list matching, outcome classification, transcript indexing, and the
follow-up analysis. Loaded by file path (tools/ is outside pythonpath).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

import pytest

_TOOL_PY = (
    Path(__file__).resolve().parents[3]
    / "tools"
    / "mlflow"
    / "extract_interactive_events.py"
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "extract_interactive_events", _TOOL_PY
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load()


def test_sanitize_project_dir() -> None:
    assert (
        mod.sanitize_project_dir(Path(r"C:\Users\Marcus\Documents\GitHub\mcp_coder"))
        == "C--Users-Marcus-Documents-GitHub-mcp-coder"
    )


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("Bash", "bash"),
        ("mcp__mcp-workspace__read_file", "read"),
        ("mcp__mcp-workspace__save_file", "write"),
        ("mcp__mcp-workspace__github_issue_view", "github"),
        ("mcp__mcp-tools-py__run_pytest_check", "exec"),
        ("AskUserQuestion", "other"),
    ],
)
def test_tool_category(tool_name: str, expected: str) -> None:
    assert mod.tool_category(tool_name) == expected


def test_bash_verb() -> None:
    assert mod.bash_verb("Bash", {"command": "gh issue create --title x"}) == "gh"
    assert mod.bash_verb("Bash", {"command": "  git status "}) == "git"
    assert mod.bash_verb("Bash", {}) == ""
    assert mod.bash_verb("mcp__x__y", {"command": "gh"}) == ""


def test_load_allowlist_and_matching(tmp_path: Path) -> None:
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "settings.local.json").write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": [
                        "mcp__mcp-tools-py__run_pytest_check",
                        "Bash(git rebase:*)",
                        "Bash(tach check)",
                        "WebFetch(domain:*)",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    allow = mod.load_allowlist(tmp_path)
    assert allow["mcp"] == {"mcp__mcp-tools-py__run_pytest_check"}
    assert allow["bash_prefixes"] == ["git rebase"]
    assert allow["bash_exact"] == {"tach check"}

    # mcp tool: exact membership
    assert mod.was_allowlisted("mcp__mcp-tools-py__run_pytest_check", {}, allow) is True
    assert mod.was_allowlisted("mcp__mcp-tools-py__sleep", {}, allow) is False
    # bash: prefix + exact
    assert (
        mod.was_allowlisted("Bash", {"command": "git rebase --continue"}, allow) is True
    )
    assert mod.was_allowlisted("Bash", {"command": "tach check"}, allow) is True
    assert mod.was_allowlisted("Bash", {"command": "gh issue create"}, allow) is False
    # unknown native tool -> None
    assert mod.was_allowlisted("Edit", {}, allow) is None


def test_classify_outcome() -> None:
    assert mod.classify_outcome(None) == "no_result"
    assert mod.classify_outcome({"is_error": False, "text": "ok"}) == "executed"
    assert (
        mod.classify_outcome(
            {
                "is_error": True,
                "text": "The user doesn't want to proceed with this tool use",
            }
        )
        == "denied_by_user"
    )
    assert (
        mod.classify_outcome({"is_error": False, "text": "x", "interrupted": True})
        == "interrupted"
    )
    assert mod.classify_outcome({"is_error": True, "text": "boom"}) == "error"


def _transcript() -> List[Dict[str, Any]]:
    return [
        {"type": "queue-operation", "operation": "enqueue"},
        {
            "type": "assistant",
            "timestamp": "2026-07-06T20:18:39.482Z",
            "gitBranch": "main",
            "version": "2.1.193",
            "sessionId": "sess-1",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "call-1",
                        "name": "Bash",
                        "input": {"command": "gh issue create"},
                    }
                ]
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "call-1",
                        "is_error": False,
                        "content": "https://github.com/x/y/issues/1",
                    }
                ]
            },
            "toolUseResult": {"stdout": "...", "interrupted": False},
        },
    ]


def test_index_transcript() -> None:
    calls, results = mod.index_transcript(_transcript())
    assert len(calls) == 1
    call_id, name, inp, env = calls[0]
    assert (call_id, name) == ("call-1", "Bash")
    assert env["branch"] == "main"
    assert results["call-1"]["is_error"] is False


def test_analyze_followup_switch_and_recover() -> None:
    calls: List[Any] = [
        ("a", "Bash", {"command": "x"}, {}),
        ("b", "Edit", {"file": "y"}, {}),
    ]
    results = {"b": {"is_error": False, "text": "ok"}}
    res = mod.analyze_followup(0, calls, results)
    assert res["followup_action"] == "switched_to:Edit"
    assert res["next_tool"] == "Edit"

    calls2: List[Any] = [
        ("a", "Bash", {"command": "x"}, {}),
        ("b", "Bash", {"command": "x"}, {}),
    ]
    results2 = {"b": {"is_error": False, "text": "ok"}}
    res2 = mod.analyze_followup(0, calls2, results2)
    assert res2["followup_action"] == "retried_same"
    assert res2["eventually_succeeded"] is True


def test_extract_session_events_end_to_end(tmp_path: Path) -> None:
    transcript = tmp_path / "sess-1.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(line) for line in _transcript()), encoding="utf-8"
    )
    allow = {"mcp": set(), "bash_prefixes": ["git rebase"], "bash_exact": set()}
    events = mod.extract_session_events(transcript, allow)
    assert len(events) == 1
    e = events[0]
    assert e["source"] == "interactive"
    assert e["tool_name"] == "Bash"
    assert e["bash_verb"] == "gh"
    assert e["outcome"] == "executed"
    assert e["was_allowlisted"] is False  # `gh` not covered by `git rebase`
    assert e["branch_name"] == "main"
    assert e["date"] == "2026-07-06"
