"""File size checking functionality."""

import os
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.mcp_server_filesystem import list_files


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
    # Get all project files
    files = list_files(".", project_dir)

    # Get metrics for all files
    metrics = get_file_metrics([Path(f) for f in files], project_dir)

    # Track which files exist and their metrics
    file_paths_set = {
        str(m.path).replace("/", os.sep).replace("\\", os.sep) for m in metrics
    }
    metrics_by_path = {
        str(m.path).replace("/", os.sep).replace("\\", os.sep): m for m in metrics
    }

    # Separate violations from passing files
    violations: list[FileMetrics] = []
    allowlisted_count = 0

    for metric in metrics:
        normalized_path = str(metric.path).replace("/", os.sep).replace("\\", os.sep)
        if metric.line_count > max_lines:
            if normalized_path in allowlist:
                allowlisted_count += 1
            else:
                violations.append(metric)

    # Detect stale allowlist entries
    stale_entries: list[str] = []
    for entry in allowlist:
        if entry not in file_paths_set:
            # File doesn't exist
            stale_entries.append(entry)
        elif entry in metrics_by_path:
            # File exists but is under the limit
            if metrics_by_path[entry].line_count <= max_lines:
                stale_entries.append(entry)

    # Sort violations by line_count descending
    violations.sort(key=lambda m: m.line_count, reverse=True)

    # Determine if check passed (no unallowlisted violations)
    passed = len(violations) == 0

    return CheckResult(
        passed=passed,
        violations=violations,
        total_files_checked=len(metrics),
        allowlisted_count=allowlisted_count,
        stale_entries=stale_entries,
    )


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
