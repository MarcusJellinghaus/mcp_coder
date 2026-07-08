"""Resolve and load prompt sources.

Provides helpers for locating prompt content, including package-relative
path detection and data-file lookup.
"""

import glob
import os
from pathlib import Path
from typing import Optional

from .utils.data_files import find_data_file


def _is_package_relative_path(source: str) -> bool:
    r"""Detect if source is a package-relative path that should use find_data_file.

    Package-relative paths typically start with a package name (like 'mcp_coder/prompts/...')
    and don't contain '..' or start with '/' or '\' (which would indicate absolute paths
    or relative paths from current directory).

    Args:
        source: Path string to check

    Returns:
        bool: True if this looks like a package-relative path
    """
    if not _is_file_path(source):
        return False

    # Skip if it's a directory, wildcard, or absolute path
    if (
        source.endswith("/")
        or source.endswith("\\")
        or "*" in source
        or "?" in source
        or source.startswith("/")
        or source.startswith("\\")
        or (len(source) > 1 and source[1] == ":")  # Windows drive letter
    ):
        return False

    # Skip relative paths that go up directories
    if ".." in source:
        return False

    # Check if it looks like a package path (contains at least one slash and doesn't start with .)
    return ("/" in source or "\\" in source) and not source.startswith(".")


def _resolve_package_path(source: str) -> Optional[Path]:
    """Resolve a package-relative path using find_data_file.

    This function attempts to parse the source as 'package_name/relative_path'
    and use find_data_file to locate it robustly.

    Args:
        source: Package-relative path like 'mcp_coder/prompts/prompts.md'

    Returns:
        Path: Resolved path to the file, or None if resolution failed
    """
    try:
        # Normalize path separators
        normalized_source = source.replace("\\", "/")
        parts = normalized_source.split("/")

        if len(parts) < 2:
            return None

        # Try different package name combinations
        # First try: first part as package name
        package_name = parts[0]
        relative_path = "/".join(parts[1:])

        try:
            resolved_file = find_data_file(
                package_name=package_name,
                relative_path=relative_path,
            )
            return resolved_file
        except (FileNotFoundError, ImportError):
            pass

        # Second try: first two parts as package name (e.g., 'mcp_coder.prompts')
        if len(parts) >= 3:
            package_name = f"{parts[0]}.{parts[1]}"
            relative_path = "/".join(parts[2:])

            try:
                resolved_file = find_data_file(
                    package_name=package_name,
                    relative_path=relative_path,
                )
                return resolved_file
            except (FileNotFoundError, ImportError):
                pass

    except (
        Exception
    ):  # pylint: disable=broad-exception-caught  # TODO: narrow to specific file/path exceptions
        # If anything goes wrong with package resolution, fall back to normal path handling
        pass

    return None


def _load_content(source: str) -> str:
    """Load content from source (auto-detect file path vs string content).

    For directories/wildcards, concatenate all .md files.

    This is an internal function that handles the complexity of determining
    whether the input is a file path, directory, wildcard pattern, or
    string content, and loads the appropriate content.

    Args:
        source: File path, directory, wildcard, or string content

    Returns:
        str: The loaded content. For directories/wildcards, this is the
             concatenated content of all matching .md files separated by
             double newlines.

    Raises:
        FileNotFoundError: If file/directory doesn't exist or cannot be read
    """
    if _is_file_path(source):
        # First, try to resolve as package-relative path
        if _is_package_relative_path(source):
            resolved_path = _resolve_package_path(source)
            if resolved_path and resolved_path.exists():
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        return f.read()
                except (
                    Exception
                ):  # pylint: disable=broad-exception-caught  # TODO: narrow to specific file/path exceptions
                    # Fall through to normal path handling if package resolution fails
                    pass

        if os.path.isdir(source):
            # Directory - load all .md files
            md_files = glob.glob(os.path.join(source, "*.md"))
            if not md_files:
                return ""

            combined_content = []
            for file_path in sorted(md_files):  # Sort for consistent ordering
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        combined_content.append(content)
                except (
                    Exception
                ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow to specific file/path exceptions
                    raise FileNotFoundError(
                        f"Error reading file {file_path}: {str(e)}"
                    ) from e

            return "\n\n".join(combined_content)

        elif "*" in source or "?" in source:
            # Wildcard pattern
            matched_files = glob.glob(source)
            if not matched_files:
                return ""

            combined_content = []
            for file_path in sorted(matched_files):
                if file_path.endswith(".md"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            combined_content.append(content)
                    except (
                        Exception
                    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow to specific file/path exceptions
                        raise FileNotFoundError(
                            f"Error reading file {file_path}: {str(e)}"
                        ) from e

            return "\n\n".join(combined_content)

        else:
            # Single file
            try:
                with open(source, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"File '{source}' not found") from exc
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow to specific file/path exceptions
                raise FileNotFoundError(
                    f"Error reading file '{source}': {str(e)}"
                ) from e
    else:
        # String content
        return source


def _is_file_path(source: str) -> bool:
    """Detect if source is a file path vs string content using simple heuristics.

    This function uses several heuristics to distinguish between file paths
    and markdown content strings:
    - Presence of newlines or # at start indicates content
    - Path separators, extensions, wildcards indicate file paths
    - Short strings without markdown indicators are assumed to be paths

    Args:
        source: Input string to check

    Returns:
        bool: True if likely a file path, False if likely string content
    """
    # If it contains newlines or starts with #, treat as content
    if "\n" in source or source.strip().startswith("#"):
        return False

    # If it looks like a path (has path separators or file extensions), treat as file path
    if (
        "/" in source
        or "\\" in source
        or "." in source
        or "*" in source
        or "?" in source
    ):
        return True

    # Default to treating short strings as file paths
    return len(source) < 200
