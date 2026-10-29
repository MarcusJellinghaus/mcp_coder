#!/usr/bin/env python3
"""Download console logs of recent Jenkins builds.

Writes one UTF-8 file per selected build to the output directory, named after
the build's display name when it set one, plus an ``index.csv`` listing the
builds. Prints the written log paths. All Jenkins logic lives in
``mcp_coder.utils.jenkins_operations``; this script only parses arguments,
writes files and sets the exit code.

Usage:
    python tools/jenkins_download_logs.py [--limit N] [--job PATH | --all-jobs] [--status a,b] [--name-pattern REGEX] [--outdir DIR]
"""

import argparse
import csv
import sys
from pathlib import Path

# Sibling script in tools/; resolved at runtime via sys.path[0].
from jenkins_builds import (  # type: ignore[import-not-found]
    add_selection_args,
    make_client,
    resolve_job,
)

from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsError
from mcp_coder.utils.jenkins_operations.builds import log_filename

DEFAULT_STATUS = "failure,aborted,unstable"
INDEX_FILENAME = "index.csv"
INDEX_COLUMNS = (
    "file",
    "display_name",
    "job_path",
    "number",
    "status",
    "timestamp",
    "duration_ms",
    "url",
)


def assign_filenames(builds: list[BuildInfo]) -> list[str]:
    """Pick a unique log filename per build.

    Display-name filenames that would repeat fall back to the job path and
    build number, which are unique.

    Args:
        builds: Builds in download order

    Returns:
        Filenames, one per build, same order
    """
    names = [log_filename(b.job_path, b.number, b.display_name) for b in builds]
    return [
        name if names.count(name) == 1 else log_filename(b.job_path, b.number)
        for name, b in zip(names, builds, strict=True)
    ]


def write_index(path: Path, builds: list[BuildInfo], filenames: list[str]) -> None:
    """Write the CSV index of downloaded logs.

    Args:
        path: CSV file to write
        builds: Downloaded builds
        filenames: Log filename per build, same order
    """
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(INDEX_COLUMNS)
        for name, b in zip(filenames, builds, strict=True):
            writer.writerow(
                (
                    name,
                    b.display_name,
                    b.job_path,
                    b.number,
                    b.status,
                    b.timestamp.isoformat(),
                    "" if b.duration_ms is None else b.duration_ms,
                    b.url,
                )
            )


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
            limit=args.limit,
            path=resolve_job(args),
            statuses=args.status,
            name_pattern=args.name_pattern,
        )
        filenames = assign_filenames(builds)
        args.outdir.mkdir(parents=True, exist_ok=True)
        for build, name in zip(builds, filenames, strict=True):
            path = args.outdir / name
            path.write_text(
                client.get_console_output(build.job_path, build.number),
                encoding="utf-8",
            )
            print(path)
        write_index(args.outdir / INDEX_FILENAME, builds, filenames)
    except JenkinsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error writing logs to '{args.outdir}': {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
