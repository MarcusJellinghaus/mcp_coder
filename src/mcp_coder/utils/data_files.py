"""
Utilities for finding data files in both development and installed environments.

This module provides functions to locate data files that are included with the package
using importlib.resources (Python 3.9+ standard library).
"""

import importlib
import logging
from importlib.resources import files
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def find_data_file(
    package_name: str,
    relative_path: str,
) -> Path:
    """
    Find a data file using importlib.resources (Python 3.9+ standard library).

    This function uses importlib.resources.files() to locate data files in both
    development and installed environments automatically.

    IMPORTANT: Data files must be explicitly declared in pyproject.toml under
    [tool.setuptools.package-data]:

        [tool.setuptools.package-data]
        "*" = ["py.typed"]
        "your_package.resources" = ["script.py", "config.json", "templates/*"]

    Args:
        package_name: Name of the Python package (e.g., "mcp_coder.resources")
        relative_path: Path to the file relative to the package
                      (e.g., "sleep_script.py")

    Returns:
        Path to the data file

    Raises:
        FileNotFoundError: If the package cannot be found or the file doesn't exist.

    Example:
        >>> script_path = find_data_file(
        ...     "mcp_coder.resources",
        ...     "sleep_script.py",
        ... )
    """
    # Log search start with parameters
    logger.debug(
        "SEARCH STARTED: Looking for data file",
        extra={
            "package_name": package_name,
            "relative_path": relative_path,
        },
    )

    # Try to get package resources using importlib.resources.files()
    logger.debug(
        "Using importlib.resources.files() for package lookup",
        extra={"package_name": package_name},
    )

    try:
        logger.debug(
            "Calling importlib.resources.files() for package",
            extra={"package_name": package_name},
        )
        package_resources = files(package_name)
        logger.debug(
            "Resource traversable obtained",
            extra={"package_name": package_name, "resources": str(package_resources)},
        )
    except ModuleNotFoundError as e:
        logger.debug(
            "FAILED: Package not found via importlib.resources",
            extra={"package_name": package_name, "error": str(e)},
        )
        logger.error(
            "SEARCH COMPLETE: Package not found",
            extra={"package_name": package_name, "relative_path": relative_path},
        )
        raise FileNotFoundError(
            f"Data file '{relative_path}' not found for package '{package_name}'. "
            f"Package '{package_name}' could not be found. "
            f"Ensure the package is installed (pip install -e . for development) "
            f"and the file is declared in pyproject.toml under [tool.setuptools.package-data]."
        ) from e

    # Navigate to the relative path
    logger.debug(
        "Joining relative path to resource",
        extra={"relative_path": relative_path},
    )
    resource = package_resources.joinpath(relative_path)
    logger.debug(
        "Resource path joined",
        extra={"resource": str(resource)},
    )

    # Convert Traversable to Path using Path(str(resource))
    logger.debug(
        "Converting Traversable to Path using Path(str(resource))",
        extra={"resource": str(resource)},
    )
    path = Path(str(resource))
    logger.debug(
        "Constructed path from resource",
        extra={"path": str(path)},
    )

    # Check if path exists
    logger.debug(
        "Checking if path exists",
        extra={"path": str(path)},
    )

    if path.exists():
        logger.debug(
            "SUCCESS: Found data file at %s",
            path,
            extra={"path": str(path)},
        )
        return path

    # File not found
    logger.debug(
        "FAILED: Path does not exist",
        extra={"path": str(path)},
    )
    logger.error(
        "SEARCH COMPLETE: Data file not found",
        extra={
            "package_name": package_name,
            "relative_path": relative_path,
            "searched_path": str(path),
        },
    )
    raise FileNotFoundError(
        f"Data file '{relative_path}' not found for package '{package_name}'. "
        f"Searched location: {path}. "
        f"Ensure the package is installed (pip install -e . for development) "
        f"and the file is declared in pyproject.toml under [tool.setuptools.package-data]."
    )


def find_package_data_files(
    package_name: str,
    relative_paths: List[str],
) -> List[Path]:
    """
    Find multiple data files for a package.

    Args:
        package_name: Name of the Python package
        relative_paths: List of relative paths to find

    Returns:
        List of Path objects for found files

    Raises:
        FileNotFoundError: If any file cannot be found

    Example:
        >>> paths = find_package_data_files(
        ...     "mcp_coder",
        ...     ["tools/sleep_script.py", "config/defaults.json"],
        ... )
    """
    found_files = []

    for relative_path in relative_paths:
        file_path = find_data_file(
            package_name=package_name,
            relative_path=relative_path,
        )
        found_files.append(file_path)

    return found_files


def get_package_directory(package_name: str) -> Path:
    """
    Get the directory where a package is installed.

    Args:
        package_name: Name of the Python package

    Returns:
        Path to the package directory

    Raises:
        ImportError: If the package cannot be found

    Example:
        >>> package_dir = get_package_directory("mcp_coder")
        >>> print(package_dir)  # /path/to/site-packages/mcp_coder
    """
    try:
        # First try using importlib.util.find_spec
        spec = importlib.util.find_spec(package_name)
        if spec and spec.origin:
            return Path(spec.origin).parent
    except Exception as e:
        logger.debug(
            "Error finding package directory via importlib.util.find_spec",
            extra={"error": str(e), "package_name": package_name},
        )

    try:
        # Fallback to importing the module and using __file__
        package_module = importlib.import_module(package_name)
        if hasattr(package_module, "__file__") and package_module.__file__:
            return Path(package_module.__file__).parent
    except Exception as e:
        logger.debug(
            "Error finding package directory via __file__",
            extra={"error": str(e), "package_name": package_name},
        )

    raise ImportError(f"Cannot find package directory for '{package_name}'")
