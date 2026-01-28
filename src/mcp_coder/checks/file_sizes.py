"""File size checking functionality."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    path: Path
    line_count: int


@dataclass
class CheckResult:
    """Result of file size check."""

    passed: bool
    violations: list[FileMetrics]
    total_files_checked: int
    allowlisted_count: int
    stale_entries: list[str]


def count_lines(file_path: Path) -> int:
    """Count lines in a file.

    Args:
        file_path: Path to file to count lines in.

    Returns:
        Line count, or -1 if file is binary/non-UTF-8.
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            return sum(1 for _ in f)
    except UnicodeDecodeError:
        return -1


def load_allowlist(allowlist_path: Path) -> set[str]:
    """Load allowlist from file.

    Args:
        allowlist_path: Path to allowlist file.

    Returns:
        Set of normalized path strings.
    """
    if not allowlist_path.exists():
        return set()

    result: set[str] = set()
    with allowlist_path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue
            # Normalize path separators to OS-native format
            normalized = stripped.replace("/", os.sep).replace("\\", os.sep)
            result.add(normalized)

    return result


def get_file_metrics(files: list[Path], project_dir: Path) -> list[FileMetrics]:
    """Get file metrics for a list of files.

    Args:
        files: List of relative file paths.
        project_dir: Project directory.

    Returns:
        List of FileMetrics (excludes binary files).
    """
    result: list[FileMetrics] = []
    for file_path in files:
        absolute_path = project_dir / file_path
        line_count = count_lines(absolute_path)
        if line_count >= 0:
            result.append(FileMetrics(path=file_path, line_count=line_count))
    return result


def check_file_sizes(
    project_dir: Path,
    max_lines: int,
    allowlist: set[str],
) -> CheckResult:
    """Check file sizes against maximum line limit.

    Args:
        project_dir: Project directory.
        max_lines: Maximum allowed lines per file.
        allowlist: Set of allowlisted file paths.

    Returns:
        CheckResult with violations, counts, and stale entries.
    """
    raise NotImplementedError("To be implemented in Task 2.6")


def render_output(result: CheckResult, max_lines: int) -> str:
    """Render check result for terminal output.

    Args:
        result: CheckResult to render.
        max_lines: Maximum lines threshold for display.

    Returns:
        Formatted string for terminal output.
    """
    raise NotImplementedError("To be implemented in Task 2.7")


def render_allowlist(violations: list[FileMetrics]) -> str:
    """Render violations as allowlist entries.

    Args:
        violations: List of FileMetrics violations.

    Returns:
        Newline-separated paths for allowlist file.
    """
    raise NotImplementedError("To be implemented in Task 2.8")
