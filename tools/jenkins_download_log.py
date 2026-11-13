#!/usr/bin/env python3
"""Download the console log of one Jenkins build.

Writes the log as UTF-8 to the given file, creating missing parent directories
and overwriting an existing file, then prints the file path. All Jenkins logic
lives in ``mcp_coder.utils.jenkins_operations``; this script only parses
arguments, writes the file and sets the exit code.

Usage:
    python tools/jenkins_download_log.py <job_path> <number> <output_file>
"""

import argparse
import sys
from pathlib import Path

# Sibling script in tools/; resolved at runtime via sys.path[0].
from jenkins_builds import (  # type: ignore[import-not-found]
    make_client,
    positive_int,
)

from mcp_coder.utils.jenkins_operations import JenkinsError


def main(argv: list[str] | None = None) -> int:
    """Run the tool.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code: 0 on success, 1 on configuration, Jenkins or write errors
    """
    parser = argparse.ArgumentParser(
        description="Download the console log of one Jenkins build."
    )
    parser.add_argument(
        "job_path",
        help="full job path from the Jenkins root, e.g. Windows-Agents/Executor",
    )
    parser.add_argument("number", type=positive_int, help="build number")
    parser.add_argument(
        "output_file",
        type=Path,
        help=(
            "file to write; missing parent directories are created, "
            "an existing file is overwritten"
        ),
    )
    args = parser.parse_args(argv)
    client = make_client()
    if client is None:
        return 1
    try:
        text = client.get_console_output(args.job_path, args.number)
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(text, encoding="utf-8")
    except JenkinsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error writing log to '{args.output_file}': {e}", file=sys.stderr)
        return 1
    print(args.output_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
