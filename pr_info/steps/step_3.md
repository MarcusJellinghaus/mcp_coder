# Step 3: CLI Integration

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.
Implement Step 3: Create CLI command handler and integrate into main.py.
Follow TDD - write CLI tests first, then implement the handler.
```

## Objective
Create the CLI command handler and wire it into the main CLI parser.

---

## Task 3.1: Create CLI Command Handler

### WHERE
`src/mcp_coder/cli/commands/check_file_sizes.py`

### WHAT
```python
def execute_check_file_sizes(args: argparse.Namespace) -> int
```

### HOW
- Parse CLI arguments (max_lines, allowlist_file, generate_allowlist)
- Resolve project directory
- Load allowlist if file exists
- Call check_file_sizes()
- Output results (render_output or render_allowlist)
- Return exit code (0=pass, 1=violations)

### ALGORITHM
```
1. Resolve project_dir from args or current directory
2. Load allowlist from args.allowlist_file
3. Call check_file_sizes(project_dir, args.max_lines, allowlist)
4. If args.generate_allowlist:
   a. Print render_allowlist(result.violations)
   b. Return 1 if violations else 0
5. Else:
   a. Print render_output(result, args.max_lines)
   b. Return 0 if passed else 1
```

### DATA
- **Input**: argparse.Namespace with max_lines, allowlist_file, generate_allowlist, project_dir
- **Output**: Exit code (int)

### IMPLEMENTATION
```python
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
```

---

## Task 3.2: Update main.py - Add Check Command Group

### WHERE
`src/mcp_coder/cli/main.py`

### WHAT
Add `check` command group with `file-size` subcommand.

### HOW - Imports
```python
from .commands.check_file_sizes import execute_check_file_sizes
```

### HOW - Parser Setup (add after coordinator_parser section)
```python
# Check commands - Code quality checks
check_parser = subparsers.add_parser(
    "check", help="Code quality check commands"
)
check_subparsers = check_parser.add_subparsers(
    dest="check_subcommand",
    help="Available check commands",
    metavar="SUBCOMMAND",
)

# check file-size command
file_size_parser = check_subparsers.add_parser(
    "file-size", help="Check file sizes against maximum line count"
)
file_size_parser.add_argument(
    "--max-lines",
    type=int,
    default=600,
    help="Maximum lines per file (default: 600)",
)
file_size_parser.add_argument(
    "--allowlist-file",
    type=str,
    default=".large-files-allowlist",
    help="Path to allowlist file (default: .large-files-allowlist)",
)
file_size_parser.add_argument(
    "--generate-allowlist",
    action="store_true",
    help="Output violating paths for piping to allowlist",
)
file_size_parser.add_argument(
    "--project-dir",
    type=str,
    default=None,
    help="Project directory path (default: current directory)",
)
```

### HOW - Command Routing (add in main() routing section)
```python
elif args.command == "check":
    if hasattr(args, "check_subcommand") and args.check_subcommand:
        if args.check_subcommand == "file-size":
            return execute_check_file_sizes(args)
        else:
            logger.error(f"Unknown check subcommand: {args.check_subcommand}")
            print(f"Error: Unknown check subcommand '{args.check_subcommand}'")
            return 1
    else:
        logger.error("Check subcommand required")
        print("Error: Please specify a check subcommand (e.g., 'file-size')")
        return 1
```

---

## Task 3.3: Add CLI Tests

### WHERE
`tests/cli/commands/test_check_file_sizes.py`

### TEST CASES
```python
"""Tests for check file-size CLI command."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCheckFileSizesCommand:
    """Test the check file-size CLI command."""

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_returns_zero_on_pass(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path
    ) -> None:
        """Test exit code 0 when all files pass."""

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_returns_one_on_violations(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path
    ) -> None:
        """Test exit code 1 when violations found."""

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_generate_allowlist_outputs_paths(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path, capsys
    ) -> None:
        """Test --generate-allowlist outputs violation paths."""


class TestCheckFileSizesIntegration:
    """Integration tests for check file-size via CLI parser."""

    @patch("mcp_coder.cli.main.execute_check_file_sizes")
    @patch("sys.argv", ["mcp-coder", "check", "file-size"])
    def test_command_routing(self, mock_execute: MagicMock) -> None:
        """Test that check file-size routes to correct handler."""
```

---

## Verification Checklist
- [ ] `src/mcp_coder/cli/commands/check_file_sizes.py` created
- [ ] `src/mcp_coder/cli/main.py` updated with check command group
- [ ] `tests/cli/commands/test_check_file_sizes.py` created and passes
- [ ] CLI help shows `check file-size` command
- [ ] Manual test: `mcp-coder check file-size --help` works
- [ ] Manual test: `mcp-coder check file-size` runs on project
- [ ] Run pylint, mypy, pytest on all new/modified files
