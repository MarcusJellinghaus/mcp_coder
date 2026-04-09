"""Init command for the MCP Coder CLI."""

import argparse
import logging
import shutil
from importlib.resources import files
from pathlib import Path

from ...utils.log_utils import OUTPUT
from ...utils.user_config import create_default_config, get_config_file_path

logger = logging.getLogger(__name__)

DEPLOY_SUBDIRS = ("skills", "knowledge_base", "agents")


def _has_all_subdirs(base: Path) -> bool:
    """Check whether *base* contains all required deploy subdirectories.

    Returns:
        True if all required subdirectories exist under *base*.
    """
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

    # 2. Fallback: walk up from this file to find repo-root .claude/.
    # Require a stable mcp-coder-repo marker (src/mcp_coder/__init__.py) at
    # the same ancestor so we don't accidentally accept a foreign project's
    # .claude/ when mcp-coder is installed editable into it.
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / ".claude"
        tried.append(candidate)
        marker = ancestor / "src" / "mcp_coder" / "__init__.py"
        if candidate.is_dir() and _has_all_subdirs(candidate) and marker.is_file():
            return candidate

    # 3. Both failed
    logger.error(
        "Cannot locate packaged Claude resources (skills/, knowledge_base/, agents/).\n"
        "Paths tried:\n%s\n"
        "Try reinstalling: pip install --force-reinstall mcp-coder",
        "\n".join(f"  - {p}" for p in tried),
    )
    raise SystemExit(1)


def _deploy_skills(source_dir: Path, project_dir: Path) -> tuple[int, int]:
    """Deploy Claude skills, knowledge_base, and agents to a project.

    Copies files from source_dir into project_dir/.claude/. Never overwrites
    existing files — skips them with a warning.

    Args:
        source_dir: Path containing skills/, knowledge_base/, agents/ subdirs.
        project_dir: Target project root.

    Returns:
        Tuple of (files_added, files_skipped).
    """
    added, skipped = 0, 0
    target_base = project_dir / ".claude"
    for subdir_name in DEPLOY_SUBDIRS:
        src_sub = source_dir / subdir_name
        if not src_sub.is_dir():
            continue
        for src_file in src_sub.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(source_dir)
            dest = target_base / rel
            if dest.exists():
                logger.warning("Skipped (exists): %s", rel)
                skipped += 1
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)
                added += 1
    return added, skipped


def execute_init(args: argparse.Namespace) -> int:
    """Execute init command to create default configuration and deploy skills.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("Executing init command")

    # 1. Validate --project-dir early
    if args.project_dir is not None:
        project_dir = Path(args.project_dir)
        if not project_dir.exists():
            logger.error("Project directory does not exist: %s", project_dir)
            return 1
    else:
        project_dir = Path.cwd()

    # 2. Resolve source and detect self-deploy
    source_dir = _find_claude_source_dir()
    target_base = project_dir / ".claude"
    if source_dir.resolve() == target_base.resolve():
        logger.info("Skipping deploy: running inside mcp-coder source repo")
    else:
        added, skipped = _deploy_skills(source_dir, project_dir)
        logger.log(OUTPUT, "Skills: %d added, %d skipped", added, skipped)

    # 3. Config creation (skip if --just-skills)
    if not args.just_skills:
        path = get_config_file_path()
        try:
            created = create_default_config()
        except OSError as e:
            logger.error("Failed to write config to %s: %s", path, e)
            return 1

        if created:
            logger.log(OUTPUT, "Created default config at: %s", path)
            logger.log(
                OUTPUT,
                "Please update it with your actual credentials and settings.",
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
