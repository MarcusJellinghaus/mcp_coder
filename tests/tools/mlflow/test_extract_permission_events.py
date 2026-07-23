"""Unit tests for tools/mlflow/extract_permission_events.py.

Covers the pure, DB-free helpers: tool-name classification, tool_result
flattening, per-step indexing of tool_use / tool_result blocks, and the
follow-up analysis (what the model did after a denial).

The script lives outside pythonpath = ["src"], so it's loaded by file path
(same approach as tests/tools/test_install_py.py).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

import pytest

_TOOL_PY = (
    Path(__file__).resolve().parents[3]
    / "tools"
    / "mlflow"
    / "extract_permission_events.py"
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("extract_permission_events", _TOOL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extract = _load()


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
