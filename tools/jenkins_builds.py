#!/usr/bin/env python3
"""List recent Jenkins builds across all jobs.

Prints time, status, folder, job and build number for the newest builds.
All Jenkins logic lives in ``mcp_coder.utils.jenkins_operations``; this
script only parses arguments, formats output and sets the exit code.

Usage:
    python tools/jenkins_builds.py [--limit N] [--folder PATH] [--status a,b]
"""

import argparse
import sys

from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsClient, JenkinsError
from mcp_coder.utils.jenkins_operations.builds import VALID_STATUSES, validate_statuses
from mcp_coder.utils.jenkins_operations.client import get_jenkins_config


def parse_statuses(value: str) -> list[str]:
    """Parse a comma-separated status list for argparse.

    Args:
        value: Comma-separated statuses, case-insensitive

    Returns:
        Lowercased statuses

    Raises:
        argparse.ArgumentTypeError: If a status is not in VALID_STATUSES
    """
    statuses = [s.strip().lower() for s in value.split(",") if s.strip()]
    try:
        validate_statuses(statuses)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from e
    return statuses


def add_selection_args(
    parser: argparse.ArgumentParser, default_status: str | None
) -> None:
    """Add the --limit, --folder and --status arguments.

    Args:
        parser: Parser to extend
        default_status: Default for --status (comma-separated), None for all
    """
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help=(
            "newest N builds across all jobs (default: 100); values above 100 "
            "use allBuilds and may be slow on large servers"
        ),
    )
    parser.add_argument(
        "--folder",
        default=None,
        help="full folder path from the Jenkins root (default: whole server)",
    )
    parser.add_argument(
        "--status",
        type=parse_statuses,
        default=default_status,
        help=(
            f"comma-separated list of: {', '.join(VALID_STATUSES)} "
            f"(default: {default_status or 'all statuses'})"
        ),
    )


def make_client() -> JenkinsClient | None:
    """Create a JenkinsClient from the configuration.

    Returns:
        Client, or None after printing the missing settings to stderr
    """
    config = get_jenkins_config()
    names = {
        "server_url": "JENKINS_URL",
        "username": "JENKINS_USER",
        "api_token": "JENKINS_TOKEN",
    }
    missing = [env for key, env in names.items() if config.get(key) is None]
    if missing:
        print(
            f"Jenkins not configured: missing {', '.join(missing)}. "
            "Set the environment variables or ~/.mcp_coder/config.toml [jenkins].",
            file=sys.stderr,
        )
        return None
    return JenkinsClient(
        str(config["server_url"]), str(config["username"]), str(config["api_token"])
    )


def format_table(builds: list[BuildInfo]) -> str:
    """Format builds as an aligned text table.

    Args:
        builds: Builds in display order

    Returns:
        Header line plus one line per build
    """
    rows = [("TIME", "STATUS", "FOLDER", "JOB", "BUILD")]
    rows += [
        (
            b.timestamp.astimezone().strftime("%Y-%m-%d %H:%M"),
            b.status,
            b.folder,
            b.job_name,
            str(b.number),
        )
        for b in builds
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]) - 1)]
    lines = []
    for row in rows:
        cells = [cell.ljust(w) for cell, w in zip(row[:-1], widths, strict=True)]
        lines.append("  ".join([*cells, row[-1]]))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the tool.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code: 0 on success, 1 on configuration or Jenkins errors
    """
    parser = argparse.ArgumentParser(description="List recent Jenkins builds.")
    add_selection_args(parser, default_status=None)
    args = parser.parse_args(argv)
    client = make_client()
    if client is None:
        return 1
    try:
        builds = client.get_recent_builds(
            limit=args.limit, folder=args.folder, statuses=args.status
        )
    except JenkinsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(format_table(builds) if builds else "No builds found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
