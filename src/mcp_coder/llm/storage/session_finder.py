"""Session file discovery and retrieval functionality.

This module provides functions for finding session files on the filesystem,
particularly for identifying the most recent session for continuation.
"""

import glob
import logging
import os
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "find_latest_session",
]


def find_latest_session(
    responses_dir: str = ".mcp-coder/responses",
) -> Optional[str]:
    """Find the most recent response file by filename timestamp with strict validation.

    Args:
        responses_dir: Directory containing response files

    Returns:
        Path to latest response file, or None if none found

    Example:
        >>> path = find_latest_session()
        >>> print(path)
        .mcp-coder/responses/response_2025-10-02T14-30-00.json
    """
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
