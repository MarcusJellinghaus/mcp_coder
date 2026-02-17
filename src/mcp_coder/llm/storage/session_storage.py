"""Session storage and retrieval functionality.

This module provides functions for storing and loading LLM session data
to/from the filesystem for conversation continuity.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Union

from ..types import LLMResponseDict

logger = logging.getLogger(__name__)

__all__ = [
    "store_session",
    "extract_session_id",
]


def store_session(
    response_data: Union[LLMResponseDict, Dict[str, Any]],
    prompt: str,
    store_path: Optional[str] = None,
    step_name: Optional[str] = None,
    branch_name: Optional[str] = None,
) -> str:
    """Store complete session data to .mcp-coder/responses/ directory.

    Args:
        response_data: Response dictionary (LLMResponseDict or legacy dict format)
        prompt: Original user prompt
        store_path: Optional custom path for storage directory
        step_name: Optional step name; if provided, filename uses {timestamp}_{step_name}.json
        branch_name: Optional branch name added to metadata

    Returns:
        File path of stored session for potential user reference

    Example:
        >>> data = {"text": "Hello", "session_info": {"session_id": "abc"}}
        >>> path = store_session(data, "What is Python?")
        >>> print(path)
        .mcp-coder/responses/response_2025-10-02T14-30-00.json
    """
    # Determine storage directory
    if store_path is None:
        storage_dir = ".mcp-coder/responses"
    else:
        storage_dir = store_path

    # Create storage directory if it doesn't exist
    os.makedirs(storage_dir, exist_ok=True)

    # Generate timestamp-based filename
    timestamp = datetime.now().isoformat().replace(":", "-").split(".")[0]
    if step_name:
        filename = f"{timestamp}_{step_name}.json"
    else:
        filename = f"response_{timestamp}.json"
    file_path = os.path.join(storage_dir, filename)

    # Extract model using triple-fallback to support both LLMResponseDict and old dict formats
    model = (
        response_data.get("raw_response", {}).get("session_info", {}).get("model")  # type: ignore[union-attr]
        or response_data.get("session_info", {}).get("model")  # type: ignore[union-attr]
        or response_data.get("provider", "claude")
    )

    metadata: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat() + "Z",
        "working_directory": os.getcwd(),
        "model": model,
    }
    if branch_name is not None:
        metadata["branch_name"] = branch_name
    if step_name is not None:
        metadata["step_name"] = step_name

    # Create complete session JSON structure
    session_data = {
        "prompt": prompt,
        "response_data": response_data,
        "metadata": metadata,
    }

    # Write JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, default=str)

    return file_path


def extract_session_id(file_path: str) -> Optional[str]:
    """Extract session_id from a stored response file.

    Args:
        file_path: Path to the stored session JSON file

    Returns:
        Session ID string if found, None otherwise

    Example:
        >>> session_id = extract_session_id(".mcp-coder/responses/response_123.json")
        >>> print(session_id)
        '550e8400-e29b-41d4-a716-446655440000'
    """
    logger.info("Extracting session_id from: %s", file_path)

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning("Response file not found: %s", file_path)
            return None

        # Read and parse JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Try multiple paths to find session_id
        # Path 1: response_data.session_info.session_id (detailed API response)
        session_id: Optional[str] = (
            session_data.get("response_data", {})
            .get("session_info", {})
            .get("session_id")
        )
        if session_id and isinstance(session_id, str):
            logger.debug(
                "Found session_id in response_data.session_info: %s", session_id
            )
            return session_id

        # Path 2: Direct session_id field (simple response format)
        session_id = session_data.get("session_id")
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id at root level: %s", session_id)
            return session_id

        # Path 3: metadata.session_id (alternative storage location)
        session_id = session_data.get("metadata", {}).get("session_id")
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id in metadata: %s", session_id)
            return session_id

        # Path 4: response_data.session_id (LLMResponseDict format)
        session_id = session_data.get("response_data", {}).get("session_id")
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id in response_data: %s", session_id)
            return session_id

        logger.warning("No session_id found in file: %s", file_path)
        return None

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in file %s: %s", file_path, e)
        return None
    except Exception as e:
        logger.error("Error reading session file %s: %s", file_path, e)
        return None
