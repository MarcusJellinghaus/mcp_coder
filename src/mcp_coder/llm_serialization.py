"""Serialization utilities for LLM responses.

This module provides functions to serialize and deserialize LLMResponseDict
objects to/from JSON files with versioning support for future compatibility.
"""

import json
from pathlib import Path

from .llm_types import LLMResponseDict

__all__ = [
    "to_json_string",
    "from_json_string",
    "serialize_llm_response",
    "deserialize_llm_response",
]

# Note: All four functions are exported (including pure functions)
# to allow advanced users to use them directly for custom workflows


def to_json_string(response: LLMResponseDict) -> str:
    """Convert LLMResponseDict to JSON string (pure function).

    This pure function handles serialization logic without file I/O,
    making it easy to test and reuse.

    Args:
        response: LLMResponseDict to convert to JSON

    Returns:
        Formatted JSON string with proper encoding

    Example:
        >>> response = {"version": "1.0", "text": "Hello", ...}
        >>> json_str = to_json_string(response)
        >>> print(json_str)
    """
    return json.dumps(
        response,
        indent=2,
        ensure_ascii=False,  # Allow Unicode characters
        default=str,  # Convert non-serializable types to strings
    )


def from_json_string(json_str: str) -> LLMResponseDict:
    """Parse JSON string and validate version (pure function).

    This pure function handles deserialization and validation logic
    without file I/O, making it easy to test.

    Args:
        json_str: JSON string to parse

    Returns:
        LLMResponseDict with available fields

    Raises:
        ValueError: If version is incompatible or missing
        json.JSONDecodeError: If JSON is invalid

    Example:
        >>> json_str = '{"version": "1.0", "text": "Hello", ...}'
        >>> response = from_json_string(json_str)
    """
    data = json.loads(json_str)

    # Validate version compatibility
    version = data.get("version")
    if not version:
        raise ValueError(
            "Missing 'version' field. This may not be a valid LLM response."
        )

    if not isinstance(version, str) or not version.startswith("1."):
        raise ValueError(
            f"Incompatible version: {version}. Expected version 1.x. "
            "This may require a newer version of the software."
        )

    # Return data as-is (best effort - no strict field validation)
    # We validate version but don't strictly validate all fields
    return data  # type: ignore[no-any-return]


def serialize_llm_response(response: LLMResponseDict, filepath: Path | str) -> None:
    """Write LLM response to JSON file (I/O wrapper).

    Thin wrapper that handles file I/O, delegating serialization logic
    to the pure to_json_string() function.

    Args:
        response: LLMResponseDict to serialize
        filepath: Path to save JSON file (will be created or overwritten)

    Raises:
        OSError: If file cannot be written (permissions, disk space, etc.)

    Example:
        >>> response = {"version": "1.0", "text": "Hello", ...}
        >>> serialize_llm_response(response, "logs/abc-123.json")
    """
    filepath = Path(filepath)

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Use pure function for serialization
    json_str = to_json_string(response)

    # Write to file
    filepath.write_text(json_str, encoding="utf-8")


def deserialize_llm_response(filepath: Path | str) -> LLMResponseDict:
    """Load LLM response from JSON file (I/O wrapper).

    Thin wrapper that handles file I/O, delegating parsing and validation
    logic to the pure from_json_string() function.

    Args:
        filepath: Path to JSON file to load

    Returns:
        LLMResponseDict with available fields

    Raises:
        ValueError: If version is incompatible or missing
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON

    Example:
        >>> response = deserialize_llm_response("logs/abc-123.json")
        >>> print(response["text"])
    """
    filepath = Path(filepath)

    # Read file content
    json_str = filepath.read_text(encoding="utf-8")

    # Use pure function for parsing and validation
    return from_json_string(json_str)
