# copied from mcp_code_checker
"""
Utilities for finding data files in both development and installed environments.

This module provides functions to locate data files that are included with the package
but kept outside the main package structure (e.g., scripts, configuration files).
"""

import importlib.util
import logging
import os
import site
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def find_data_file(  # pylint: disable=too-many-statements
    package_name: str,
    relative_path: str,
    development_base_dir: Optional[Path] = None,
) -> Path:
    """
    Find a data file in both development and installed environments.

    This function searches for data files using multiple strategies:
    1. Development environment: Look relative to development_base_dir
    2. Installed package: Look in the package installation directory
    3. Alternative package location: Using package __file__ attribute
    4. Site-packages search: Search current Python environment's site-packages directories
    5. Virtual environment search: Search current virtual environment's site-packages directory

    IMPORTANT: For installed packages to work (methods 2 and 3), data files must be
    explicitly declared in pyproject.toml under [tool.setuptools.package-data]:

        [tool.setuptools.package-data]
        "*" = ["py.typed"]
        "your_package.resources" = ["script.py", "config.json", "templates/*"]

    Without this configuration, data files will only be found in development mode.

    Args:
        package_name: Name of the Python package (e.g., "mcp_coder.resources")
        relative_path: Path to the file relative to the package/development root
                      (e.g., "sleep_script.py")
        development_base_dir: Base directory for development environment.
                             If None, development lookup is skipped.

    Returns:
        Path to the data file

    Raises:
        FileNotFoundError: If the file cannot be found in any expected location.
                          For installed packages, this often means the file is not
                          declared in pyproject.toml package-data configuration.

    Example:
        >>> # Find sleep_script.py in development or installed environment
        >>> script_path = find_data_file(
        ...     "mcp_coder.resources",
        ...     "sleep_script.py",
        ...     development_base_dir=Path("/project/root")
        ... )

        # Requires this in pyproject.toml:
        # [tool.setuptools.package-data]
        # "mcp_coder.resources" = ["sleep_script.py"]
    """
    # Start with logging of the search parameters
    logger.debug(
        "SEARCH STARTED: Looking for data file using 5 methods",
        extra={
            "package_name": package_name,
            "relative_path": relative_path,
            "development_base_dir": (
                str(development_base_dir) if development_base_dir else None
            ),
            "methods": "1=Development, 2=ImportLib, 3=Module __file__, 4=Site-packages, 5=Virtual Env",
        },
    )

    search_locations = []
    search_results = []  # Track results for each method

    # Option 1: Development environment
    method_1_result = "SKIPPED"
    method_1_path = None
    if development_base_dir is not None:
        logger.debug(
            "METHOD 1/5: Searching development environment",
            extra={"method": "development", "base_dir": str(development_base_dir)},
        )

        # Try new structure: src/{package_name}/{relative_path}
        # Handle dotted package names (e.g., "mcp_coder.data")
        package_path = package_name.replace(".", "/")
        dev_file = development_base_dir / "src" / package_path / relative_path
        method_1_path = str(dev_file)
        search_locations.append(str(dev_file))

        logger.debug(
            "METHOD 1/5: Development path constructed",
            extra={
                "method": "development",
                "path": str(dev_file),
                "exists": dev_file.exists(),
            },
        )

        if dev_file.exists():
            method_1_result = "SUCCESS"
            logger.info(
                "Found data file in development environment",
                extra={"method": "development", "path": str(dev_file)},
            )
            search_results.append(
                {
                    "method": "1/5 Development",
                    "result": method_1_result,
                    "path": method_1_path or "",
                }
            )
            return dev_file
        else:
            method_1_result = "FAILED"
            logger.debug(
                "METHOD 1/5: Development path not found",
                extra={"method": "development", "path": str(dev_file)},
            )
    else:
        logger.debug(
            "METHOD 1/5: SKIPPED - No development base directory provided",
            extra={"method": "development"},
        )

    search_results.append(
        {
            "method": "1/5 Development",
            "result": method_1_result,
            "path": method_1_path or "",
        }
    )

    # Option 2: Installed package - using importlib.util.find_spec
    method_2_result = "FAILED"
    method_2_path = None
    logger.debug(
        "METHOD 2/5: Searching installed package via importlib",
        extra={"method": "importlib_spec"},
    )
    try:
        logger.debug(
            "METHOD 2/5: Attempting to find spec for package",
            extra={"method": "importlib_spec", "package_name": package_name},
        )
        spec = importlib.util.find_spec(package_name)

        if spec:
            logger.debug(
                "METHOD 2/5: Package spec found",
                extra={
                    "method": "importlib_spec",
                    "origin": spec.origin,
                    "name": spec.name,
                },
            )
            if spec.origin:
                package_dir = Path(spec.origin).parent
                package_dir_absolute = package_dir.resolve()
                installed_file = package_dir / relative_path
                installed_file_absolute = package_dir_absolute / relative_path
                method_2_path = str(installed_file_absolute)
                search_locations.append(str(installed_file_absolute))

                logger.debug(
                    "METHOD 2/5: Installed package path constructed",
                    extra={
                        "method": "importlib_spec",
                        "path": str(installed_file_absolute),
                        "exists": installed_file.exists(),
                    },
                )

                if installed_file.exists():
                    method_2_result = "SUCCESS"
                    logger.debug(
                        "Found data file in installed package (via importlib)",
                        extra={
                            "method": "importlib_spec",
                            "path": str(installed_file_absolute),
                        },
                    )
                    search_results.append(
                        {
                            "method": "2/5 ImportLib",
                            "result": method_2_result,
                            "path": method_2_path or "",
                        }
                    )
                    return installed_file
                else:
                    method_2_result = "FAILED"
                    logger.debug(
                        "METHOD 2/5: Installed package path not found",
                        extra={
                            "method": "importlib_spec",
                            "path": str(installed_file_absolute),
                        },
                    )
            else:
                method_2_result = "FAILED"
                logger.debug(
                    "METHOD 2/5: Spec found but origin is None",
                    extra={"method": "importlib_spec"},
                )
        else:
            method_2_result = "FAILED"
            logger.debug(
                "METHOD 2/5: No spec found for package",
                extra={"method": "importlib_spec", "package_name": package_name},
            )
    except Exception as e:
        method_2_result = "ERROR"
        logger.debug(
            "METHOD 2/5: Exception in importlib.util.find_spec",
            extra={
                "method": "importlib_spec",
                "error": str(e),
                "package_name": package_name,
            },
        )

    search_results.append(
        {
            "method": "2/4 ImportLib",
            "result": method_2_result,
            "path": method_2_path or "",
        }
    )

    # Option 3: Alternative installed location - using __file__ attribute
    method_3_result = "FAILED"
    method_3_path = None
    logger.debug(
        "METHOD 3/5: Searching alternative installed location via __file__",
        extra={"method": "module_file"},
    )
    try:
        logger.debug(
            "METHOD 3/5: Attempting to import module",
            extra={"method": "module_file", "package_name": package_name},
        )
        package_module = importlib.import_module(package_name)

        logger.debug(
            "METHOD 3/5: Module imported successfully",
            extra={
                "method": "module_file",
                "has_file": hasattr(package_module, "__file__"),
            },
        )

        if hasattr(package_module, "__file__") and package_module.__file__:
            module_file_absolute = str(Path(package_module.__file__).resolve())
            logger.debug(
                "METHOD 3/5: Module __file__ found",
                extra={"method": "module_file", "module_file": package_module.__file__},
            )
            package_dir = Path(package_module.__file__).parent
            package_dir_absolute = package_dir.resolve()
            alt_file = package_dir / relative_path
            alt_file_absolute = package_dir_absolute / relative_path
            method_3_path = str(alt_file_absolute)
            search_locations.append(str(alt_file_absolute))

            logger.debug(
                "METHOD 3/5: Alternative package path constructed",
                extra={
                    "method": "module_file",
                    "path": str(alt_file_absolute),
                    "exists": alt_file.exists(),
                },
            )

            if alt_file.exists():
                method_3_result = "SUCCESS"
                logger.info(
                    "Found data file in installed package (via __file__)",
                    extra={"method": "module_file", "path": str(alt_file_absolute)},
                )
                search_results.append(
                    {
                        "method": "3/5 Module __file__",
                        "result": method_3_result,
                        "path": method_3_path or "",
                    }
                )
                return alt_file
            else:
                method_3_result = "FAILED"
                logger.debug(
                    "METHOD 3/5: Alternative package path not found",
                    extra={"method": "module_file", "path": str(alt_file_absolute)},
                )
        else:
            method_3_result = "FAILED"
            logger.debug(
                "METHOD 3/5: Module does not have __file__ attribute or it's None",
                extra={"method": "module_file"},
            )
    except Exception as e:
        method_3_result = "ERROR"
        logger.debug(
            "METHOD 3/5: Exception in __file__ attribute method",
            extra={
                "method": "module_file",
                "error": str(e),
                "package_name": package_name,
            },
        )

    search_results.append(
        {
            "method": "3/4 Module __file__",
            "result": method_3_result,
            "path": method_3_path or "",
        }
    )

    # Option 4: Site-packages directory search
    method_4_result = "FAILED"
    method_4_path = None
    logger.debug(
        "METHOD 4/5: Searching current Python environment site-packages",
        extra={"method": "site_packages"},
    )
    try:
        # Get all site-packages directories for current Python environment
        site_packages_dirs = []

        # Add user site-packages
        try:
            user_site = site.getusersitepackages()
            if user_site:
                site_packages_dirs.append(Path(user_site))
        except (AttributeError, TypeError):
            pass

        # Add global site-packages directories
        try:
            global_sites = site.getsitepackages()
            if global_sites:
                site_packages_dirs.extend([Path(p) for p in global_sites])
        except (AttributeError, TypeError):
            pass

        # Add sys.path directories that look like site-packages
        for path_str in sys.path:
            if path_str and "site-packages" in path_str:
                path_obj = Path(path_str)
                if path_obj not in site_packages_dirs and path_obj.exists():
                    site_packages_dirs.append(path_obj)

        logger.debug(
            "METHOD 4/5: Found site-packages directories",
            extra={"method": "site_packages", "count": len(site_packages_dirs)},
        )

        # Search in each site-packages directory
        for site_dir in site_packages_dirs:
            try:
                # Convert package name to directory path (e.g., mcp_coder.resources -> mcp_coder/resources)
                package_path = package_name.replace(".", "/")
                potential_file = site_dir / package_path / relative_path
                potential_file_absolute = potential_file.resolve()

                logger.debug(
                    "METHOD 4/5: Checking site-packages location",
                    extra={
                        "method": "site_packages",
                        "site_dir": str(site_dir),
                        "potential_file": str(potential_file_absolute),
                        "exists": potential_file.exists(),
                    },
                )

                if potential_file.exists():
                    method_4_result = "SUCCESS"
                    method_4_path = str(potential_file_absolute)
                    search_locations.append(str(potential_file_absolute))

                    logger.info(
                        "Found data file in site-packages",
                        extra={
                            "method": "site_packages",
                            "path": str(potential_file_absolute),
                        },
                    )

                    search_results.append(
                        {
                            "method": "4/5 Site-packages",
                            "result": method_4_result,
                            "path": method_4_path,
                        }
                    )
                    return potential_file
                else:
                    # Add to search locations even if not found for complete logging
                    search_locations.append(str(potential_file_absolute))

            except Exception as e:
                logger.debug(
                    "METHOD 4/5: Error checking site-packages directory",
                    extra={
                        "method": "site_packages",
                        "site_dir": str(site_dir),
                        "error": str(e),
                    },
                )
                continue

        if method_4_result != "SUCCESS":
            method_4_result = "FAILED"
            logger.debug(
                "METHOD 4/5: No data file found in any site-packages directory",
                extra={
                    "method": "site_packages",
                    "searched_directories": [str(d) for d in site_packages_dirs],
                },
            )

    except Exception as e:
        method_4_result = "ERROR"
        logger.debug(
            "METHOD 4/5: Exception in site-packages search",
            extra={"method": "site_packages", "error": str(e)},
        )

    search_results.append(
        {
            "method": "4/5 Site-packages",
            "result": method_4_result,
            "path": method_4_path or "",
        }
    )

    # Option 5: Virtual Environment specific search
    method_5_result = "FAILED"
    method_5_path = None
    logger.debug(
        "METHOD 5/5: Searching current virtual environment site-packages",
        extra={"method": "virtual_env"},
    )
    try:
        # Detect if we're in a virtual environment and get its path
        venv_path = None
        venv_site_packages = None

        # Method 1: Check VIRTUAL_ENV environment variable
        if "VIRTUAL_ENV" in os.environ:
            venv_path = Path(os.environ["VIRTUAL_ENV"])
            logger.debug(
                "METHOD 5/5: Found VIRTUAL_ENV environment variable",
                extra={"method": "virtual_env", "venv_path": str(venv_path)},
            )

        # Method 2: Check if sys.prefix != sys.base_prefix (indicates virtual env)
        elif hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            venv_path = Path(sys.prefix)
            logger.debug(
                "METHOD 5/5: Detected virtual environment via sys.prefix",
                extra={"method": "virtual_env", "venv_path": str(venv_path)},
            )

        if venv_path and venv_path.exists():
            # Construct the site-packages path for this virtual environment
            if os.name == "nt":  # Windows
                venv_site_packages = venv_path / "Lib" / "site-packages"
            else:  # Unix-like systems
                # Find the correct Python version directory
                lib_dir = venv_path / "lib"
                if lib_dir.exists():
                    python_dirs = [
                        d
                        for d in lib_dir.iterdir()
                        if d.is_dir() and d.name.startswith("python")
                    ]
                    if python_dirs:
                        # Use the first (and usually only) python directory
                        venv_site_packages = python_dirs[0] / "site-packages"
                    else:
                        venv_site_packages = lib_dir / "python" / "site-packages"

            logger.debug(
                "METHOD 5/5: Virtual environment site-packages path constructed",
                extra={
                    "method": "virtual_env",
                    "venv_site_packages": (
                        str(venv_site_packages) if venv_site_packages else None
                    ),
                    "exists": (
                        venv_site_packages.exists() if venv_site_packages else False
                    ),
                },
            )

            if venv_site_packages and venv_site_packages.exists():
                # Convert package name to directory path
                package_path = package_name.replace(".", "/")
                venv_file = venv_site_packages / package_path / relative_path
                venv_file_absolute = venv_file.resolve()
                method_5_path = str(venv_file_absolute)
                search_locations.append(str(venv_file_absolute))

                logger.debug(
                    "METHOD 5/5: Virtual environment target file path constructed",
                    extra={
                        "method": "virtual_env",
                        "venv_file": str(venv_file_absolute),
                        "exists": venv_file.exists(),
                    },
                )

                if venv_file.exists():
                    method_5_result = "SUCCESS"
                    logger.info(
                        "Found data file in virtual environment",
                        extra={
                            "method": "virtual_env",
                            "path": str(venv_file_absolute),
                        },
                    )

                    search_results.append(
                        {
                            "method": "5/5 Virtual Environment",
                            "result": method_5_result,
                            "path": method_5_path,
                        }
                    )
                    return venv_file
                else:
                    method_5_result = "FAILED"
                    logger.debug(
                        "METHOD 5/5: File not found in virtual environment",
                        extra={
                            "method": "virtual_env",
                            "venv_file": str(venv_file_absolute),
                        },
                    )
            else:
                method_5_result = "FAILED"
                logger.debug(
                    "METHOD 5/5: Virtual environment site-packages directory not found",
                    extra={
                        "method": "virtual_env",
                        "venv_site_packages": (
                            str(venv_site_packages) if venv_site_packages else None
                        ),
                    },
                )
        else:
            method_5_result = "SKIPPED"
            logger.debug(
                "METHOD 5/5: SKIPPED - No virtual environment detected",
                extra={"method": "virtual_env"},
            )

    except Exception as e:
        method_5_result = "ERROR"
        logger.debug(
            "METHOD 5/5: Exception in virtual environment search",
            extra={"method": "virtual_env", "error": str(e)},
        )

    search_results.append(
        {
            "method": "5/5 Virtual Environment",
            "result": method_5_result,
            "path": method_5_path or "",
        }
    )

    # If we get here, the file wasn't found anywhere
    logger.error(
        "SEARCH COMPLETE: Data file not found in any location",
        extra={
            "package_name": package_name,
            "relative_path": relative_path,
            "search_locations": search_locations,
            "search_results": search_results,
            "development_base_dir": (
                str(development_base_dir) if development_base_dir else None
            ),
        },
    )

    # Log a clear summary of what was tried
    logger.debug(
        "SEARCH SUMMARY - All methods failed",
        extra={"search_results": search_results},
    )

    raise FileNotFoundError(
        f"Data file '{relative_path}' not found for package '{package_name}'. "
        f"Searched locations: {search_locations}. "
        f"Make sure the package is properly installed or you're running in development mode. "
        f"For installed packages, ensure the file is declared in pyproject.toml under "
        f"[tool.setuptools.package-data] with '{package_name}' = ['{relative_path}'] or ['{relative_path.split('/')[-1]}']."
    )
