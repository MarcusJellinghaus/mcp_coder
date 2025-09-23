"""Data models for formatter results based on Step 0 analysis patterns."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FormatterResult:
    """Ultra-simplified result based on Step 0 analysis patterns.

    Designed around exit code patterns:
    - success: Whether formatting completed successfully (based on exit codes)
    - files_changed: Files modified (detected via exit codes or tool output)
    - formatter_name: Name of formatter used ("black" or "isort")
    - error_message: Error details if subprocess failed (None for success)
    """

    success: bool
    files_changed: List[str]
    formatter_name: str
    error_message: Optional[str] = None
