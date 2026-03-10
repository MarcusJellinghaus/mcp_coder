"""Session file discovery and retrieval functionality.

This module provides functions for finding session files on the filesystem,
particularly for identifying the most recent session for continuation.
"""

import glob
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "find_latest_session",
]


def _find_latest_langchain_session() -> Optional[str]:
    """Find the most recent langchain session file by modification time.

    Searches ~/.mcp_coder/sessions/langchain/ for JSON files and returns
    the most recently modified one. Filenames are UUIDs, so mtime is used
    for ordering.

    Returns:
        Path to latest langchain session file, or None if none found
    """
    session_dir = Path.home() / ".mcp_coder" / "sessions" / "langchain"
    logger.debug("Searching for langchain sessions in: %s", session_dir)

    if not session_dir.exists():
        logger.debug("Langchain sessions directory does not exist: %s", session_dir)
        return None

    try:
        json_files = list(session_dir.glob("*.json"))
        if not json_files:
            logger.debug("No langchain session files found in: %s", session_dir)
            return None

        # Sort by modification time, newest first
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest = json_files[0]

        num_sessions = len(json_files)
        print(
            f"Found {num_sessions} previous langchain sessions, "
            f"continuing from: {latest.name}"
        )

        logger.debug("Selected latest langchain session: %s", latest)
        return str(latest)

    except OSError as e:
        logger.debug("Error accessing langchain sessions directory: %s", e)
        return None


def find_latest_session(
    responses_dir: str = ".mcp-coder/responses",
    provider: str = "claude",
) -> Optional[str]:
    """Find the most recent session file.

    For claude provider: searches responses_dir for timestamp-named response files.
    For langchain provider: searches ~/.mcp_coder/sessions/langchain/ by mtime.

    Args:
        responses_dir: Directory containing response files (used for claude)
        provider: LLM provider ("claude" or "langchain")

    Returns:
        Path to latest session file, or None if none found

    Example:
        >>> path = find_latest_session()
        >>> print(path)
        .mcp-coder/responses/response_2025-10-02T14-30-00.json
    """
    if provider == "langchain":
        return _find_latest_langchain_session()
    logger.debug("Searching for response files in: %s", responses_dir)

    # Check if responses directory exists
    if not os.path.exists(responses_dir):
        logger.debug("Responses directory does not exist: %s", responses_dir)
        return None

    try:
        # Use glob to find response files with the expected pattern
        pattern = os.path.join(responses_dir, "response_*.json")
        response_files = glob.glob(pattern)

        if not response_files:
            logger.debug("No response files found in: %s", responses_dir)
            return None

        # ISO timestamp pattern: response_YYYY-MM-DDTHH-MM-SS.json
        timestamp_pattern = r"^response_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})\.json$"

        # Validate each file matches strict ISO timestamp pattern
        valid_files = []
        for file_path in response_files:
            filename = os.path.basename(file_path)
            match = re.match(timestamp_pattern, filename)
            if match:
                timestamp_str = match.group(1)  # Extract the timestamp part
                try:
                    # Use datetime.strptime for robust validation
                    datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
                    valid_files.append(file_path)
                except ValueError:
                    logger.debug("Invalid timestamp in filename: %s", filename)
            else:
                logger.debug("Skipping invalid filename format: %s", filename)

        if not valid_files:
            logger.debug("No valid response files found with ISO timestamp format")
            return None

        # Sort validated filenames by timestamp (lexicographic sort works for ISO format)
        valid_files.sort()
        latest_file = valid_files[-1]  # Last file after sorting is the latest

        # Provide user feedback showing count and selected file
        num_sessions = len(valid_files)
        selected_filename = os.path.basename(latest_file)
        print(
            f"Found {num_sessions} previous sessions, continuing from: {selected_filename}"
        )

        logger.debug("Selected latest response file: %s", latest_file)
        return latest_file

    except (OSError, IOError) as e:
        logger.debug("Error accessing response directory %s: %s", responses_dir, e)
        return None
    except Exception as e:
        logger.debug("Unexpected error finding response files: %s", e)
        return None
