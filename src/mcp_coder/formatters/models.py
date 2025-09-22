"""Data models for code formatters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class FormatterConfig:
    """Configuration for a code formatter.

    Attributes:
        tool_name: Name of the formatter tool (e.g., "black", "isort")
        settings: Tool-specific configuration settings
        target_directories: List of directories to format
        project_root: Root directory of the project
    """

    tool_name: str
    settings: Dict[str, Any]
    target_directories: List[Path]
    project_root: Path


@dataclass
class FileChange:
    """Simple record of file changes during formatting.

    Attributes:
        file_path: Path to the file that was processed
        had_changes: Whether the file was actually modified
    """

    file_path: Path
    had_changes: bool


@dataclass
class FormatterResult:
    """Result of running a formatter.

    Attributes:
        success: Whether formatting completed successfully
        files_changed: List of files that were processed, with change status
        execution_time_ms: Time taken to complete formatting in milliseconds
        formatter_name: Name of formatter used ("black" or "isort")
        error_message: Error details if formatting failed
    """

    success: bool
    files_changed: List[FileChange]
    execution_time_ms: int
    formatter_name: str
    error_message: Optional[str]
