"""Version management utilities for MCP Coder.

This module provides utilities for version validation and management,
particularly for ensuring consistency between git tags and package versions.
"""

import re
from pathlib import Path
from typing import Tuple


class VersionError(Exception):
    """Base exception for version-related errors."""


class InvalidVersionFormatError(VersionError):
    """Raised when a version string has an invalid format."""


class VersionMismatchError(VersionError):
    """Raised when versions don't match (e.g., tag vs package version)."""


def parse_version(version_str: str) -> Tuple[int, int, int, str]:
    """Parse a semantic version string into its components.

    Args:
        version_str: Version string in format "MAJOR.MINOR.PATCH[-PRERELEASE]"
                    Examples: "1.0.0", "2.1.3-rc1", "1.2.0-alpha", "3.0.0-beta.2"

    Returns:
        Tuple of (major, minor, patch, prerelease) where prerelease is empty
        string for stable releases

    Raises:
        InvalidVersionFormatError: If version string format is invalid
    """
    # Remove 'v' prefix if present (common in git tags)
    version_str = version_str.lstrip("v")

    # Pattern for semantic versioning with optional prerelease
    # Supports: X.Y.Z, X.Y.Z-rc1, X.Y.Z-alpha, X.Y.Z-beta.2, etc.
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$"
    match = re.match(pattern, version_str)

    if not match:
        raise InvalidVersionFormatError(
            f"Invalid version format: '{version_str}'. "
            f"Expected format: MAJOR.MINOR.PATCH[-PRERELEASE]"
        )

    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), prerelease or ""


def validate_tag_version(tag: str, package_version: str) -> None:
    """Validate that a git tag matches the package version.

    Args:
        tag: Git tag string (e.g., "v1.0.0", "1.0.0-rc1")
        package_version: Package version from __init__.py or pyproject.toml

    Raises:
        InvalidVersionFormatError: If either version has invalid format
        VersionMismatchError: If versions don't match
    """
    # Parse both versions
    tag_parts = parse_version(tag)
    pkg_parts = parse_version(package_version)

    # Compare versions
    if tag_parts != pkg_parts:
        tag_ver = format_version(*tag_parts)
        pkg_ver = format_version(*pkg_parts)
        raise VersionMismatchError(
            f"Tag version '{tag_ver}' does not match package version '{pkg_ver}'"
        )


def format_version(major: int, minor: int, patch: int, prerelease: str = "") -> str:
    """Format version components into a version string.

    Args:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
        prerelease: Optional prerelease identifier (e.g., "rc1", "alpha")

    Returns:
        Formatted version string (e.g., "1.0.0", "2.1.3-rc1")
    """
    version = f"{major}.{minor}.{patch}"
    if prerelease:
        version += f"-{prerelease}"
    return version


def is_prerelease(version_str: str) -> bool:
    """Check if a version string represents a prerelease.

    Args:
        version_str: Version string to check

    Returns:
        True if version is a prerelease (contains prerelease identifier)

    Raises:
        InvalidVersionFormatError: If version string format is invalid
    """
    _, _, _, prerelease = parse_version(version_str)
    return bool(prerelease)


def get_package_version(package_root: Path = Path.cwd()) -> str:
    """Get the package version from __init__.py.

    Args:
        package_root: Root directory of the package (defaults to current working dir)

    Returns:
        Package version string

    Raises:
        FileNotFoundError: If __init__.py cannot be found
        ValueError: If version cannot be extracted
    """
    init_file = package_root / "src" / "mcp_coder" / "__init__.py"

    if not init_file.exists():
        raise FileNotFoundError(f"Cannot find __init__.py at {init_file}")

    content = init_file.read_text(encoding="utf-8")

    # Look for __version__ = "X.Y.Z" pattern
    pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
    match = re.search(pattern, content)

    if not match:
        raise ValueError(f"Cannot find __version__ in {init_file}")

    return match.group(1)
