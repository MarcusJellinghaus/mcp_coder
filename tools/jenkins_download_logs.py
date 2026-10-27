#!/usr/bin/env python3
"""Download console logs of recent Jenkins builds.

Writes one UTF-8 file per selected build to the output directory and prints
the written paths. All Jenkins logic lives in
``mcp_coder.utils.jenkins_operations``; this script only parses arguments,
writes files and sets the exit code.

Usage:
    python tools/jenkins_download_logs.py [--limit N] [--folder PATH] [--status a,b] [--outdir DIR]
"""

import argparse
import sys
from pathlib import Path

# Sibling script in tools/; resolved at runtime via sys.path[0].
from jenkins_builds import add_selection_args, make_client  # type: ignore[import-not-found]

from mcp_coder.utils.jenkins_operations import JenkinsError
from mcp_coder.utils.jenkins_operations.builds import log_filename

DEFAULT_STATUS = "failure,aborted,unstable"


def main(argv: list[str] | None = None) -> int:
    """Run the tool.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code: 0 on success, 1 on configuration or Jenkins errors
    """
    parser = argparse.ArgumentParser(
        description="Download console logs of recent Jenkins builds."
    )
    add_selection_args(parser, DEFAULT_STATUS)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("."),
        help=(
            "output directory (default: .); created with parents if missing, "
            "existing files are overwritten"
        ),
    )
    args = parser.parse_args(argv)
    client = make_client()
    if client is None:
        return 1
    try:
        builds = client.get_recent_builds(
            limit=args.limit, folder=args.folder, statuses=args.status
        )
        args.outdir.mkdir(parents=True, exist_ok=True)
        for build in builds:
            path = args.outdir / log_filename(build.job_path, build.number)
            path.write_text(
                client.get_console_output(build.job_path, build.number),
                encoding="utf-8",
            )
            print(path)
    except JenkinsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error writing logs to '{args.outdir}': {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
