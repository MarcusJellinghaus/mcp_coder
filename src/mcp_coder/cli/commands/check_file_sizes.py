"""CLI command handler for file size checking."""

import argparse
import logging
from pathlib import Path

from mcp_coder.checks.file_sizes import (
    check_file_sizes,
    load_allowlist,
    render_allowlist,
    render_output,
)

logger = logging.getLogger(__name__)


def execute_check_file_sizes(args: argparse.Namespace) -> int:
    """Execute file size check command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code: 0 for pass, 1 for violations
    """
    # Resolve project directory
    project_dir = Path(args.project_dir) if args.project_dir else Path.cwd()
    project_dir = project_dir.resolve()

    logger.info(f"Checking file sizes in {project_dir}")
    logger.debug(f"Max lines: {args.max_lines}, Allowlist: {args.allowlist_file}")

    # Load allowlist
    allowlist_path = project_dir / args.allowlist_file
    allowlist = load_allowlist(allowlist_path)

    # Run check
    result = check_file_sizes(project_dir, args.max_lines, allowlist)

    # Output results
    if args.generate_allowlist:
        output = render_allowlist(result.violations)
        if output:
            print(output)
        return 1 if result.violations else 0

    output = render_output(result, args.max_lines)
    print(output)
    return 0 if result.passed else 1
