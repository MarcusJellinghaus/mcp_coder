"""Print uv pip install commands for GitHub dependency overrides.

Bootstrap helper for reinstall_local.bat. Uses sys.path to import
pyproject_config without requiring an installed package.

Output format (one command per line):
    uv pip install "pkg1" "pkg2"
    uv pip install --no-deps "pkg3"
"""

import sys
from pathlib import Path


def main() -> None:
    """Read GitHub install config and print uv pip install commands."""
    project_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_dir / "src"))
    from mcp_coder.utils.pyproject_config import (  # pylint: disable=import-outside-toplevel
        get_github_install_config,
    )

    config = get_github_install_config(project_dir)
    if config.packages:
        quoted = " ".join(f'"{p}"' for p in config.packages)
        print(f"uv pip install {quoted}")
    if config.packages_no_deps:
        quoted = " ".join(f'"{p}"' for p in config.packages_no_deps)
        print(f"uv pip install --no-deps {quoted}")


if __name__ == "__main__":
    main()
