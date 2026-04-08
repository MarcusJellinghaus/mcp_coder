"""Init command for the MCP Coder CLI."""

import argparse
import logging
import sys
from importlib.resources import files
from pathlib import Path

from ...utils.log_utils import OUTPUT
from ...utils.user_config import create_default_config, get_config_file_path

logger = logging.getLogger(__name__)

DEPLOY_SUBDIRS = ("skills", "knowledge_base", "agents")


def _has_all_subdirs(base: Path) -> bool:
    """Check whether *base* contains all required deploy subdirectories."""
    return all((base / name).is_dir() for name in DEPLOY_SUBDIRS)


def _find_claude_source_dir() -> Path:
    """Locate the Claude resources directory (skills, knowledge_base, agents).

    Tries two locations in order:
    1. Package resources (wheel install): importlib.resources path
    2. Repo root fallback (editable install): walk up from this file

    Returns:
        Path to directory containing skills/, knowledge_base/, agents/.

    Raises:
        SystemExit: If neither location has the expected subdirectories.
    """
    tried: list[Path] = []

    # 1. Try importlib.resources (wheel install)
    pkg_path = Path(str(files("mcp_coder"))) / "resources" / "claude"
    tried.append(pkg_path)
    if pkg_path.is_dir() and _has_all_subdirs(pkg_path):
        return pkg_path

    # 2. Fallback: walk up from this file to find repo-root .claude/
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / ".claude"
        tried.append(candidate)
        if candidate.is_dir() and _has_all_subdirs(candidate):
            return candidate

    # 3. Both failed
    logger.error(
        "Cannot locate packaged Claude resources (skills/, knowledge_base/, agents/).\n"
        "Paths tried:\n%s\n"
        "Try reinstalling: pip install --force-reinstall mcp-coder",
        "\n".join(f"  - {p}" for p in tried),
    )
    sys.exit(1)


def execute_init(args: argparse.Namespace) -> int:
    """Execute init command to create default configuration file.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for write failure).
    """
    _ = (args.just_skills, args.project_dir)  # consumed in step 4
    logger.info("Executing init command")

    path = get_config_file_path()
    try:
        created = create_default_config()
    except OSError as e:
        logger.error("Failed to write config to %s: %s", path, e)
        return 1

    if created:
        logger.log(OUTPUT, "Created default config at: %s", path)
        logger.log(
            OUTPUT, "Please update it with your actual credentials and settings."
        )
        logger.log(OUTPUT, "Next steps:")
        logger.log(OUTPUT, "  mcp-coder verify          Check your setup")
        logger.log(
            OUTPUT,
            "  mcp-coder gh-tool define-labels   Sync workflow labels to your GitHub repo",
        )
    else:
        logger.log(OUTPUT, "Config already exists: %s", path)

    return 0
