"""Unit tests for tools/mlflow/extract_permission_events.py.

Covers the pure, DB-free helpers: tool-name classification, tool_result
flattening, per-step indexing of tool_use / tool_result blocks, and the
follow-up analysis (what the model did after a denial).

The script lives outside pythonpath = ["src"], so it's loaded by file path
(same approach as tests/tools/test_install_py.py).
"""

# The `extract` namespace below is a synthetic ModuleType assembled at runtime,
# so pylint cannot see its members.
# pylint: disable=no-member

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

import pytest

# The tools live outside pythonpath = ["src"]; put their dir on sys.path so the
# split modules (_permission_common / _source_mlflow / _source_transcripts)
# resolve, then merge them into one namespace for convenient access.
_TOOL_DIR = Path(__file__).resolve().parents[3] / "tools" / "mlflow"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))


def _merged() -> ModuleType:
    merged = ModuleType("permission_events_merged")
    for name in ("_permission_common", "_source_mlflow", "_source_transcripts"):
        module = importlib.import_module(name)
        for key, value in vars(module).items():
            if not key.startswith("__"):
                setattr(merged, key, value)
    return merged


extract = _merged()


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("mcp__mcp-workspace__read_file", "mcp-workspace"),
        ("mcp__workspace__search_files", "workspace"),
        ("mcp__tools-py__run_ruff_check", "tools-py"),
        ("Bash", "(native)"),
        ("", "(native)"),
    ],
)
def test_mcp_server(tool_name: str, expected: str) -> None:
    assert extract.mcp_server(tool_name) == expected


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("mcp__mcp-workspace__read_file", "read"),
        ("mcp__mcp-workspace__search_files", "read"),
        ("mcp__mcp-workspace__save_file", "write"),
        ("mcp__mcp-workspace__edit_file", "write"),
        ("mcp__mcp-workspace__git", "git"),
        ("mcp__mcp-workspace__get_base_branch", "git"),
        ("mcp__mcp-workspace__github_issue_view", "github"),
        ("mcp__mcp-tools-py__run_pytest_check", "exec"),
        ("mcp__mcp-tools-py__sleep", "exec"),
        ("something_unknown", "other"),
    ],
)
def test_tool_category(tool_name: str, expected: str) -> None:
    assert extract.tool_category(tool_name) == expected


def test_result_text_variants() -> None:
    assert extract.result_text("plain") == "plain"
    blocks = [{"type": "text", "text": "hello"}, {"type": "text", "text": "world"}]
    assert extract.result_text(blocks) == "hello world"
    # Non-text blocks are stringified, not dropped.
    assert "image" in extract.result_text([{"type": "image"}])
    assert extract.result_text(42) == "42"


def _conversation() -> List[Dict[str, Any]]:
    return [
        {
            "type": "system",
            "subtype": "init",
            "session_id": "sess-1",
            "model": "claude-opus",
            "permissionMode": "default",
            "tools": ["mcp__mcp-workspace__read_file"],
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "call-1",
                        "name": "mcp__workspace__search_files",
                        "input": {"pattern": "foo"},
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
                        "is_error": True,
                        "content": "Claude requested permissions to use it",
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "call-2",
                        "name": "mcp__mcp-workspace__read_file",
                        "input": {"file_path": "x.py"},
                    }
                ]
            },
        },
        {
            "type": "result",
            "num_turns": 4,
            "total_cost_usd": 0.12,
            "permission_denials": [
                {
                    "tool_name": "mcp__workspace__search_files",
                    "tool_input": {"pattern": "foo"},
                    "tool_use_id": "call-1",
                }
            ],
        },
    ]


def test_index_step_collects_init_result_calls_results() -> None:
    idx = extract.index_step(_conversation())
    assert idx["init"]["session_id"] == "sess-1"
    assert idx["result"]["num_turns"] == 4
    assert [c[1] for c in idx["calls"]] == [
        "mcp__workspace__search_files",
        "mcp__mcp-workspace__read_file",
    ]
    assert idx["results"]["call-1"]["is_error"] is True


def test_analyze_followup_switched_to() -> None:
    idx = extract.index_step(_conversation())
    res = extract.analyze_followup(
        "call-1",
        "mcp__workspace__search_files",
        {"pattern": "foo"},
        idx["calls"],
        idx["results"],
    )
    assert res["followup_action"] == "switched_to:mcp__mcp-workspace__read_file"
    assert res["next_tool"] == "mcp__mcp-workspace__read_file"
    # The denied call never later succeeded in this step.
    assert res["eventually_succeeded"] is False


def test_analyze_followup_retried_same_and_recovered() -> None:
    calls = [
        ("a", "mcp__x__t", {"k": 1}),
        ("b", "mcp__x__t", {"k": 1}),
    ]
    results = {"b": {"is_error": False, "text": "ok"}}
    res = extract.analyze_followup("a", "mcp__x__t", {"k": 1}, calls, results)
    assert res["followup_action"] == "retried_same"
    assert res["eventually_succeeded"] is True


def test_analyze_followup_last_call_in_step() -> None:
    calls = [("a", "mcp__x__t", {"k": 1})]
    res = extract.analyze_followup("a", "mcp__x__t", {"k": 1}, calls, {})
    assert res["followup_action"] == "none (last call in step)"
    assert res["next_tool"] == ""


def test_analyze_followup_ignores_earlier_success() -> None:
    # A success BEFORE the denial must not count as recovery.
    calls = [
        ("a", "mcp__x__t", {"k": 1}),
        ("b", "mcp__x__t", {"k": 1}),
    ]
    results = {
        "a": {"is_error": False, "text": "ok"},
        "b": {"is_error": True, "text": "denied"},
    }
    res = extract.analyze_followup("b", "mcp__x__t", {"k": 1}, calls, results)
    assert res["eventually_succeeded"] is False


def test_analyze_followup_ignores_self_match() -> None:
    # An executed call must not trivially recover via its own result
    # (interactive source builds an event for every call, not just denials).
    calls = [("a", "mcp__x__t", {"k": 1})]
    results = {"a": {"is_error": False, "text": "ok"}}
    res = extract.analyze_followup("a", "mcp__x__t", {"k": 1}, calls, results)
    assert res["eventually_succeeded"] is False


# ---------------------------------------------------------------------------
# Interactive-source helpers (same module, --source interactive)
# ---------------------------------------------------------------------------


def test_sanitize_project_dir() -> None:
    assert (
        extract.sanitize_project_dir(
            Path(r"C:\Users\Marcus\Documents\GitHub\mcp_coder")
        )
        == "C--Users-Marcus-Documents-GitHub-mcp-coder"
    )


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("Bash", "bash"),
        ("AskUserQuestion", "other"),
        ("mcp__mcp-workspace__read_file", "read"),
    ],
)
def test_tool_category_bash_and_native(tool_name: str, expected: str) -> None:
    assert extract.tool_category(tool_name) == expected


def test_bash_verb() -> None:
    assert extract.bash_verb("Bash", {"command": "gh issue create --title x"}) == "gh"
    assert extract.bash_verb("Bash", {"command": "  git status "}) == "git"
    assert extract.bash_verb("Bash", {}) == ""
    assert extract.bash_verb("mcp__x__y", {"command": "gh"}) == ""


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
    allow = extract.load_allowlist(tmp_path)
    assert allow["mcp"] == {"mcp__mcp-tools-py__run_pytest_check"}
    assert allow["bash_prefixes"] == ["git rebase"]
    assert allow["bash_exact"] == {"tach check"}

    assert (
        extract.was_allowlisted("mcp__mcp-tools-py__run_pytest_check", {}, allow)
        is True
    )
    assert extract.was_allowlisted("mcp__mcp-tools-py__sleep", {}, allow) is False
    assert (
        extract.was_allowlisted("Bash", {"command": "git rebase --continue"}, allow)
        is True
    )
    assert extract.was_allowlisted("Bash", {"command": "tach check"}, allow) is True
    assert (
        extract.was_allowlisted("Bash", {"command": "gh issue create"}, allow) is False
    )
    assert extract.was_allowlisted("Edit", {}, allow) is None


def test_classify_outcome() -> None:
    assert extract.classify_outcome(None) == "no_result"
    assert extract.classify_outcome({"is_error": False, "text": "ok"}) == "executed"
    assert (
        extract.classify_outcome(
            {
                "is_error": True,
                "text": "The user doesn't want to proceed with this tool use",
            }
        )
        == "denied_by_user"
    )
    assert (
        extract.classify_outcome({"is_error": False, "text": "x", "interrupted": True})
        == "interrupted"
    )
    assert extract.classify_outcome({"is_error": True, "text": "boom"}) == "error"


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
    calls, results = extract.index_transcript(_transcript())
    assert len(calls) == 1
    call_id, name, _inp, env = calls[0]
    assert (call_id, name) == ("call-1", "Bash")
    assert env["branch"] == "main"
    assert results["call-1"]["is_error"] is False


def test_extract_session_events_end_to_end(tmp_path: Path) -> None:
    transcript = tmp_path / "sess-1.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(line) for line in _transcript()), encoding="utf-8"
    )
    allow = {"mcp": set(), "bash_prefixes": ["git rebase"], "bash_exact": set()}
    events = extract.extract_session_events(transcript, allow)
    assert len(events) == 1
    e = events[0]
    assert e["source"] == "interactive"
    assert e["tool_name"] == "Bash"
    assert e["bash_verb"] == "gh"
    assert e["outcome"] == "executed"
    assert e["was_allowlisted"] is False  # `gh` not covered by `git rebase`
    assert e["branch_name"] == "main"
    assert e["date"] == "2026-07-06"
