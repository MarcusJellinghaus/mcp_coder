#!/usr/bin/env python3
"""List recent Jenkins builds across all jobs.

Prints time, status, folder, job, build number and display name for the
newest builds. All Jenkins logic lives in ``mcp_coder.utils.jenkins_operations``;
this script only parses arguments, formats output and sets the exit code.

Usage:
    python tools/jenkins_builds.py [--limit N] [--job PATH | --all-jobs] [--status a,b] [--name-pattern REGEX]
"""

import argparse
import re
import sys

from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsClient, JenkinsError
from mcp_coder.utils.jenkins_operations.builds import VALID_STATUSES, validate_statuses
from mcp_coder.utils.jenkins_operations.client import get_jenkins_config
from mcp_coder.utils.user_config import load_config


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


def parse_pattern(value: str) -> re.Pattern[str]:
    """Compile a regex for argparse.

    Args:
        value: Regular expression

    Returns:
        The compiled pattern

    Raises:
        argparse.ArgumentTypeError: If value is not a valid regex
    """
    try:
        return re.compile(value)
    except re.error as e:
        raise argparse.ArgumentTypeError(f"invalid regex '{value}': {e}") from e


def positive_int(value: str) -> int:
    """Parse a positive integer for argparse.

    Args:
        value: Integer string

    Returns:
        The parsed integer

    Raises:
        argparse.ArgumentTypeError: If value is not an integer of at least 1
    """
    try:
        number = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid integer: '{value}'") from e
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {number}")
    return number


def add_selection_args(
    parser: argparse.ArgumentParser, default_status: str | None
) -> None:
    """Add the --limit, --job, --all-jobs, --status and --name-pattern arguments.

    Args:
        parser: Parser to extend
        default_status: Default for --status (comma-separated), None for all
    """
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=100,
        help=(
            "newest N builds across all jobs (default: 100); values above 100 "
            "use allBuilds and may be slow on large servers"
        ),
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--job",
        default=None,
        help=(
            "full job or folder path from the Jenkins root (default: the "
            "executor_job_path shared by all [coordinator.repos.*] in the config, "
            "else the whole server)"
        ),
    )
    scope.add_argument(
        "--all-jobs",
        action="store_true",
        help="list the whole server, ignoring the configured executor job",
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
    parser.add_argument(
        "--name-pattern",
        type=parse_pattern,
        default=None,
        help=(
            "regex searched in the build display name, applied before --limit; "
            "scans up to max(limit, 100) builds per job (default: all builds)"
        ),
    )


def configured_executor_jobs() -> list[str]:
    """Return the distinct executor_job_path values of all coordinator repos.

    Returns:
        Sorted job paths; [] when none are configured
    """
    repos = load_config().get("coordinator", {}).get("repos", {})
    paths = {
        repo.get("executor_job_path")
        for repo in repos.values()
        if isinstance(repo, dict)
    }
    return sorted(p for p in paths if isinstance(p, str) and p.strip())


def resolve_job(args: argparse.Namespace) -> str | None:
    """Pick the job or folder to list from the parsed arguments.

    Args:
        args: Parsed arguments from add_selection_args

    Returns:
        --job if given; None for --all-jobs; else the configured executor job
        when all repos share one, else None (whole server)
    """
    if args.all_jobs:
        return None
    if args.job:
        return str(args.job)
    jobs = configured_executor_jobs()
    if len(jobs) == 1:
        print(f"Using executor job from config: {jobs[0]}", file=sys.stderr)
        return jobs[0]
    if jobs:
        print(
            f"Several executor jobs configured ({', '.join(jobs)}); "
            "listing the whole server. Pass --job to pick one.",
            file=sys.stderr,
        )
    return None


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
    rows = [("TIME", "STATUS", "FOLDER", "JOB", "BUILD", "NAME")]
    rows += [
        (
            b.timestamp.astimezone().strftime("%Y-%m-%d %H:%M"),
            b.status,
            b.folder,
            b.job_name,
            str(b.number),
            b.display_name,
        )
        for b in builds
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]) - 1)]
    lines = []
    for row in rows:
        cells = [cell.ljust(w) for cell, w in zip(row[:-1], widths, strict=True)]
        lines.append("  ".join([*cells, row[-1]]).rstrip())
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
            limit=args.limit,
            path=resolve_job(args),
            statuses=args.status,
            name_pattern=args.name_pattern,
        )
    except JenkinsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(format_table(builds) if builds else "No builds found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
