#!/usr/bin/env python3
"""Extract permission / tool-use events from Claude Code sessions.

One CLI, two sources (``--source``):

- ``headless`` (default) — mcp-coder's **MLflow** runs. Claude Code runs with a
  restricted MCP tool set and no human, so every call to a non-allow-listed tool
  is auto-denied and recorded as a ``permission_denials`` entry. Native ``Bash``
  is never exposed here. One event per denial.
- ``interactive`` — Claude Code's own **transcripts**
  (``~/.claude/projects/<project>/*.jsonl``). ``Bash`` and native tools *are*
  exposed and the human approves/rejects. One event per tool-use call, with an
  ``outcome`` (executed / denied_by_user / interrupted / error) and
  ``was_allowlisted`` (matched against ``.claude/settings*.json``).

Both sources emit the **same event schema** (with a ``source`` column) to
``permission_events.jsonl`` + ``.csv``, so ``analyze_permission_events.py`` can
consume either. See ``tools/mlflow/README.md`` for the headless-vs-interactive
background.

Implementation is split for readability: shared helpers live in
``_permission_common.py``; the two source readers in ``_source_mlflow.py`` and
``_source_transcripts.py``. This file is just the CLI that dispatches on
``--source``.

Usage:
    python tools/mlflow/extract_permission_events.py                       # headless
    python tools/mlflow/extract_permission_events.py --limit 500
    python tools/mlflow/extract_permission_events.py --source interactive
    python tools/mlflow/extract_permission_events.py --source interactive --project-dir /path/to/repo
"""

import argparse
from pathlib import Path
from typing import Any, Dict, List

# Sibling scripts in this (non-package) dir; resolved at runtime via sys.path[0].
from _permission_common import write_outputs  # type: ignore[import-not-found]
from _source_mlflow import (  # type: ignore[import-not-found]
    collect_headless,
    print_summary_headless,
)
from _source_transcripts import (  # type: ignore[import-not-found]
    collect_interactive,
    print_summary_interactive,
)


def main() -> None:
    """Parse args, run the chosen source reader, write + summarise."""
    parser = argparse.ArgumentParser(
        description="Extract permission / tool-use events (headless MLflow or interactive transcripts)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        choices=["headless", "interactive"],
        default="headless",
        help="Which sessions to read (default: headless)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".ml_flow_analysis",
        help="Output directory (default: .ml_flow_analysis)",
    )
    # headless
    parser.add_argument("--limit", type=int, help="[headless] Max runs to scan")
    parser.add_argument(
        "--db-path", type=str, help="[headless] Path to MLflow SQLite DB (auto-detected)"
    )
    # interactive
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="[interactive] Repo whose transcripts + allow-list to read",
    )
    parser.add_argument(
        "--transcripts-dir",
        type=str,
        help="[interactive] Override the ~/.claude/projects/<project> folder",
    )
    args = parser.parse_args()

    events: List[Dict[str, Any]]
    if args.source == "interactive":
        events = collect_interactive(args)
        write_outputs(events, Path(args.output))
        print_summary_interactive(events)
    else:
        events = collect_headless(args)
        write_outputs(events, Path(args.output))
        print_summary_headless(events)


if __name__ == "__main__":
    main()
