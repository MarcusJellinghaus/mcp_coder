"""Unit tests for tools/mlflow/analyze_permission_events.py.

Covers the pure analysis functions over event dicts: tool-name era,
denial-cause classification, clustering, waste aggregation, the summary
builder, and JSONL round-tripping.
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
    / "analyze_permission_events.py"
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("analyze_permission_events", _TOOL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyze = _load()


def _event(**overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "run_id": "run-1",
        "step": 1,
        "tool_name": "mcp__workspace__search_files",
        "mcp_server": "workspace",
        "tool_category": "read",
        "branch_name": "branch-a",
        "date": "2026-07-01",
        "was_available": True,
        "retry_count": 1,
        "followup_action": "retried_same",
        "eventually_succeeded": False,
        "step_total_cost_usd": 0.10,
        "step_num_turns": 5,
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "tool_name, mcp_servers, expected",
    [
        # Data-driven: server segment matched against the run's connected servers.
        ("mcp__mcp-workspace__read_file", "mcp-workspace,mcp-tools-py", "current"),
        ("mcp__workspace__search_files", "mcp-workspace,mcp-tools-py", "legacy"),
        # A server that is neither connected nor a legacy rename is NOT "legacy"
        # (regression: non-mcp-* servers used to be misclassified by prefix).
        ("mcp__obsidian-wiki__read-note", "mcp-workspace", "unknown_server"),
        ("Bash", "mcp-workspace", "native"),
        # Fallback prefix heuristic for datasets without mcp_servers.
        ("mcp__mcp-workspace__read_file", "", "current"),
        ("mcp__tools-py__run_ruff_check", "", "legacy"),
        ("Bash", "", "native"),
    ],
)
def test_name_era(tool_name: str, mcp_servers: str, expected: str) -> None:
    event = _event(tool_name=tool_name, mcp_servers=mcp_servers)
    assert analyze.name_era(event) == expected


def test_gap_class() -> None:
    # Connected but not permitted -> real allow-list gap.
    assert analyze.gap_class(_event(was_available=True)) == "allowlist_gap"
    # Not connected + legacy name for a connected mcp-* server -> naming mismatch.
    assert (
        analyze.gap_class(
            _event(
                was_available=False,
                tool_name="mcp__workspace__search_files",
                mcp_servers="mcp-workspace",
            )
        )
        == "naming_mismatch"
    )
    # Not connected + current/native name -> not_connected.
    assert (
        analyze.gap_class(_event(was_available=False, tool_name="Bash"))
        == "not_connected"
    )
    # A denial for a server that isn't connected at all is not a naming mismatch.
    assert (
        analyze.gap_class(
            _event(
                was_available=False,
                tool_name="mcp__obsidian-wiki__read-note",
                mcp_servers="mcp-workspace",
            )
        )
        == "not_connected"
    )
    # Interactive events are human rejections, not config gaps.
    assert (
        analyze.gap_class(_event(source="interactive", was_available=None))
        == "user_rejection"
    )


def test_denial_events_filters_interactive_non_denials() -> None:
    events = [
        _event(),  # headless: a denial by construction
        _event(source="interactive", outcome="executed"),
        _event(source="interactive", outcome="denied_by_user"),
        _event(source="interactive", outcome="error"),
    ]
    kept = analyze.denial_events(events)
    assert len(kept) == 2
    assert {e.get("outcome") for e in kept} == {None, "denied_by_user"}


def test_cluster_by_handles_missing() -> None:
    events = [
        _event(branch_name="a"),
        _event(branch_name="a"),
        _event(branch_name=None),
    ]
    counter = analyze.cluster_by(events, "branch_name")
    assert counter["a"] == 2
    assert counter["(none)"] == 1


def test_waste_stats_dedupes_cost_per_step() -> None:
    # Two denial events in the SAME (run, step), both in a loop: cost counted once.
    events = [
        _event(retry_count=5, step_total_cost_usd=0.20, step_num_turns=8),
        _event(retry_count=4, step_total_cost_usd=0.20, step_num_turns=8),
        # A different step, not in a loop (retry_count < 3): excluded from loop cost.
        _event(run_id="run-2", step=2, retry_count=1, step_total_cost_usd=9.0),
    ]
    stats = analyze.waste_stats(events)
    assert stats["events_in_loop"] == 2
    assert stats["loop_steps"] == 1
    assert stats["loop_step_cost_usd"] == pytest.approx(0.20)
    assert stats["loop_step_turns"] == 8
    assert stats["max_retry_count"] == 5
    assert stats["retried_same_events"] == 3


def test_summarize_shape() -> None:
    events = [
        _event(),
        _event(tool_name="mcp__mcp-workspace__read_file", was_available=True),
        _event(eventually_succeeded=True),
    ]
    summary = analyze.summarize(events)
    assert summary["total_events"] == 3
    assert summary["total_runs"] == 1
    assert summary["recovered"] == 1
    assert summary["by_name_era"]["legacy"] == 2
    assert summary["by_name_era"]["current"] == 1
    assert summary["by_gap_class"]["allowlist_gap"] == 3


def test_load_events_roundtrip(tmp_path: Path) -> None:
    events: List[Dict[str, Any]] = [_event(), _event(run_id="run-2")]
    dataset = tmp_path / "permission_events.jsonl"
    dataset.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
    )
    # Accepts both a direct file path and a containing directory.
    assert len(analyze.load_events(dataset)) == 2
    loaded = analyze.load_events(tmp_path)
    assert len(loaded) == 2
    assert loaded[1]["run_id"] == "run-2"


def test_group_by_arbitrary_field() -> None:
    # The --group-by path clusters events directly by any field name.
    events = [_event(), _event(branch_name="b"), _event(mcp_server="tools-py")]
    assert analyze.cluster_by(events, "branch_name")["branch-a"] == 2
    assert analyze.cluster_by(events, "mcp_server")["tools-py"] == 1
    # Unknown field -> everything falls into "(none)", not a crash.
    assert analyze.cluster_by(events, "nonexistent")["(none)"] == 3
