#!/usr/bin/env python3
"""Analyse the permission-event dataset produced by extract_permission_events.py.

``extract_permission_events.py`` harvests raw denial events into
``permission_events.jsonl``. This companion tool *reads* that dataset (no MLflow
access needed) and answers the analysis questions the raw dump can't:

- **Why was it denied?** Split events into a *naming mismatch* (the model called
  a tool that isn't even connected — almost always a legacy ``mcp__workspace__*``
  prefix vs the current ``mcp__mcp-workspace__*``) versus a real *allow-list gap*
  (the tool is connected/available but not permitted).
- **What did it cost?** Aggregate the wasted ``retried_same`` loops and the
  step cost/turns that went with them.
- **Where / when?** Cluster by tool, mcp_server, category, branch and day.

Everything here is pure functions over a list of event dicts, so the logic is
unit-testable without a database or artifacts on disk.

Usage:
    python tools/mlflow/analyze_permission_events.py
    python tools/mlflow/analyze_permission_events.py --input .ml_flow_analysis
    python tools/mlflow/analyze_permission_events.py --group-by branch_name
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Event = Dict[str, Any]

# Current tool names are ``mcp__mcp-<server>__<tool>``; older sessions called
# ``mcp__<server>__<tool>`` (no ``mcp-`` in the server segment), which no longer
# resolves to a connected tool.
_CURRENT_PREFIX = "mcp__mcp-"


def load_events(path: Path) -> List[Event]:
    """Load events from a permission_events.jsonl file (or a dir containing it)."""
    if path.is_dir():
        path = path / "permission_events.jsonl"
    events: List[Event] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def prefix_era(tool_name: str) -> str:
    """Classify a tool name as current / legacy naming, or native."""
    if tool_name.startswith(_CURRENT_PREFIX):
        return "current"
    if tool_name.startswith("mcp__"):
        return "legacy"
    return "native"


def gap_class(event: Event) -> str:
    """Classify *why* a denial happened.

    - ``naming_mismatch``: the tool was not connected (``was_available`` false)
      and used a legacy prefix — the model guessed an outdated tool name.
    - ``allowlist_gap``: the tool was connected/available but not permitted — a
      genuine ``permissions.allow`` gap.
    - ``not_connected``: not available and not a recognisable legacy name.
    """
    available = bool(event.get("was_available"))
    if available:
        return "allowlist_gap"
    if prefix_era(event.get("tool_name", "")) == "legacy":
        return "naming_mismatch"
    return "not_connected"


def cluster_by(events: List[Event], key: str) -> "Counter[str]":
    """Count events grouped by an arbitrary field (missing values -> '(none)')."""
    return Counter(str(e.get(key) or "(none)") for e in events)


def waste_stats(events: List[Event], loop_threshold: int = 3) -> Dict[str, Any]:
    """Aggregate retry loops and the step cost/turns spent on them."""
    retried_same = sum(1 for e in events if e.get("followup_action") == "retried_same")
    in_loop = [e for e in events if (e.get("retry_count") or 1) >= loop_threshold]
    max_retry = max((e.get("retry_count") or 1 for e in events), default=0)
    # Sum step cost once per (run, step) so a step with N denials isn't counted N times.
    seen_steps: set[Tuple[Any, Any]] = set()
    loop_cost = 0.0
    loop_turns = 0
    for e in in_loop:
        step_key = (e.get("run_id"), e.get("step"))
        if step_key in seen_steps:
            continue
        seen_steps.add(step_key)
        loop_cost += float(e.get("step_total_cost_usd") or 0.0)
        loop_turns += int(e.get("step_num_turns") or 0)
    return {
        "retried_same_events": retried_same,
        "events_in_loop": len(in_loop),
        "max_retry_count": max_retry,
        "loop_steps": len(seen_steps),
        "loop_step_cost_usd": round(loop_cost, 4),
        "loop_step_turns": loop_turns,
    }


def summarize(events: List[Event]) -> Dict[str, Any]:
    """Build a structured summary of the event set."""
    runs = {e.get("run_id") for e in events}
    return {
        "total_events": len(events),
        "total_runs": len(runs),
        "recovered": sum(1 for e in events if e.get("eventually_succeeded")),
        "by_gap_class": Counter(gap_class(e) for e in events),
        "by_prefix_era": Counter(prefix_era(e.get("tool_name", "")) for e in events),
        "by_tool": cluster_by(events, "tool_name"),
        "by_mcp_server": cluster_by(events, "mcp_server"),
        "by_category": cluster_by(events, "tool_category"),
        "by_followup": cluster_by(events, "followup_action"),
        "by_branch": cluster_by(events, "branch_name"),
        "by_date": cluster_by(events, "date"),
        "waste": waste_stats(events),
    }


def _print_counter(
    title: str, counter: "Counter[str]", top: Optional[int] = None
) -> None:
    print(f"\n{title}:")
    items = counter.most_common(top) if top else counter.most_common()
    for name, count in items:
        print(f"  {count:6d}  {name}")


def print_report(
    summary: Dict[str, Any], extra_group: Optional[Tuple[str, "Counter[str]"]] = None
) -> None:
    """Print a human-readable report from a summary dict.

    ``extra_group`` is an optional ``(label, counter)`` for an extra
    ``--group-by`` breakdown.
    """
    print("=" * 60)
    print(
        f"ANALYSIS: {summary['total_events']} events across "
        f"{summary['total_runs']} runs"
    )
    print("=" * 60)
    waste = summary["waste"]
    print(f"eventually recovered:        {summary['recovered']}")
    print(f"retried_same events:         {waste['retried_same_events']}")
    print(f"events in a loop (>=3):       {waste['events_in_loop']}")
    print(f"max retry_count:             {waste['max_retry_count']}")
    print(
        f"cost on looping steps:       "
        f"${waste['loop_step_cost_usd']} over {waste['loop_steps']} steps, "
        f"{waste['loop_step_turns']} turns"
    )

    _print_counter("Denial cause (gap class)", summary["by_gap_class"])
    _print_counter("Tool-name era", summary["by_prefix_era"])
    _print_counter("Top tools denied", summary["by_tool"], top=12)
    _print_counter("By mcp server", summary["by_mcp_server"])
    _print_counter("By category", summary["by_category"])
    _print_counter("Follow-up action", summary["by_followup"], top=10)
    _print_counter("Top branches", summary["by_branch"], top=10)

    if extra_group:
        label, counter = extra_group
        _print_counter(f"Grouped by {label}", counter)
    print(f"\nDistinct days: {len(summary['by_date'])}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyse the permission_events.jsonl dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input",
        type=str,
        default=".ml_flow_analysis",
        help="Dataset dir or .jsonl file (default: .ml_flow_analysis)",
    )
    parser.add_argument(
        "--group-by",
        type=str,
        help="Extra breakdown by a field (e.g. branch_name, date, mcp_server)",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Only events with date >= this YYYY-MM-DD (ISO dates sort lexically)",
    )
    args = parser.parse_args()

    path = Path(args.input)
    if path.is_dir():
        path = path / "permission_events.jsonl"
    if not path.exists():
        print(f"Error: dataset not found at {path}")
        print("Run extract_permission_events.py first.")
        return

    events = load_events(path)
    if args.since:
        events = [e for e in events if str(e.get("date") or "") >= args.since]
        print(f"Filtered to {len(events)} events since {args.since}\n")
    summary = summarize(events)
    extra_group = (
        (args.group_by, cluster_by(events, args.group_by)) if args.group_by else None
    )
    print_report(summary, extra_group=extra_group)


if __name__ == "__main__":
    main()
