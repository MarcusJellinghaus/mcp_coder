"""Session storage and retrieval functionality.

This module provides functions for storing and loading LLM session data
to/from the filesystem for conversation continuity.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from ..types import LLMResponseDict

# Import MLflow logger with graceful fallback
try:
    from ..mlflow_logger import get_mlflow_logger

    _mlflow_available = True
except ImportError:
    _mlflow_available = False
    get_mlflow_logger = None  # type: ignore

logger = logging.getLogger(__name__)

__all__ = [
    "store_session",
    "extract_session_id",
]


def store_session(
    response_data: LLMResponseDict,
    prompt: str,
    store_path: Optional[str] = None,
    step_name: Optional[str] = None,
    branch_name: Optional[str] = None,
) -> str:
    """Store complete session data to .mcp-coder/responses/ directory.

    Args:
        response_data: Response dictionary from prompt_llm()
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

    # Extract model from LLMResponseDict
    raw_response = response_data["raw_response"]
    session_info = raw_response.get("session_info")
    model = (
        session_info.get("model") if isinstance(session_info, dict) else None
    ) or response_data["provider"]

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

    # Log complete conversation to MLflow if enabled
    if _mlflow_available and get_mlflow_logger:
        try:
            mlflow_logger = get_mlflow_logger()
            mlflow_logger.log_conversation(prompt, response_data, metadata)
        except Exception as e:
            logger.debug(f"Failed to log conversation to MLflow: {e}")

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

        # Extract session_id from LLMResponseDict format: response_data.session_id
        session_id: Optional[str] = session_data.get("response_data", {}).get(
            "session_id"
        )
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
