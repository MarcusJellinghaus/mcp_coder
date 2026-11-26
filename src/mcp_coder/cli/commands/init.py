"""Init command for the MCP Coder CLI."""

import argparse
import logging
import shutil
from importlib.resources import files
from pathlib import Path

from ...utils.log_utils import OUTPUT
from ...utils.text_io import write_lf_text
from ...utils.toolkit_runner import PYTHON_TOOLKIT, load_toolkit_config
from ...utils.user_config import create_default_config, get_config_file_path
from ...workflows.vscodeclaude.workspace import update_gitignore
from .init_file_access import ensure_file_access_rules, ensure_scratch_gitignored

logger = logging.getLogger(__name__)

DEPLOY_SUBDIRS = ("skills", "knowledge_base", "agents")

# Deployed only with the mcp-tools-py toolkit; relative to the source dir
PYTHON_ONLY_FILE = Path("knowledge_base") / "python.md"
_ADAPT_URL = (
    "https://github.com/MarcusJellinghaus/mcp_coder/blob/main/"
    "docs/repository-setup/README.md#adapting-deployed-files-non-python-repos"
)
_GENERIC_REMINDER = (
    "The deployed skills, agents and knowledge base are generic: map the checks, tests "
    "and formatting to your tools in .claude/CLAUDE.md, and adapt the agents' tools: "
    "and the skills' allowed-tools.",
    "Files that already existed were kept; delete them to get the new versions.",
    f"See {_ADAPT_URL}",
)


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


def _is_python_toolkit(project_dir: Path) -> bool:
    """Check whether the project's configured toolkit is mcp-tools-py.

    A missing or invalid toolkit table is logged as a warning and counts as
    not Python, so the toolkit never makes init fail.

    Args:
        project_dir: Project root containing pyproject.toml / mcp-coder.toml.

    Returns:
        True if [tool.mcp-coder.toolkit] names the mcp-tools-py toolkit.
    """
    try:
        name = load_toolkit_config(project_dir).toolkit
    except ValueError as exc:
        logger.warning("%s", exc)
        return False
    return name == PYTHON_TOOLKIT


def _deploy_skills(
    source_dir: Path, project_dir: Path, skip_python: bool = False
) -> tuple[int, int]:
    """Deploy Claude skills, knowledge_base, and agents to a project.

    Copies files from source_dir into project_dir/.claude/. Never overwrites
    existing files — skips them with a warning.

    Args:
        source_dir: Path containing skills/, knowledge_base/, agents/ subdirs.
        project_dir: Target project root.
        skip_python: Leave out knowledge_base/python.md; it counts as
            neither added nor skipped.

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
            if skip_python and rel == PYTHON_ONLY_FILE:
                continue
            dest = target_base / rel
            if dest.exists():
                logger.warning("Skipped (exists): %s", rel)
                skipped += 1
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)
                added += 1
    return added, skipped


def _write_gitignore_entries(project_dir: Path) -> bool:
    """Ensure the VSCodeClaude entries are present in the project .gitignore.

    Args:
        project_dir: Target project root.

    Returns:
        True on success (including "already up to date"), False if the
        .gitignore could not be read or written. A failure is logged and never
        aborts init.
    """
    try:
        added = update_gitignore(project_dir)
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Failed to update .gitignore in %s: %s", project_dir, e)
        return False

    logger.log(OUTPUT, "Gitignore: %d entries added", len(added))
    if added and not (project_dir / ".git").exists():
        logger.warning(
            "Wrote .gitignore entries but %s has no .git/ directory", project_dir
        )
    return True


SESSION_LOGS_GITIGNORE_HEADER = "# mcp-coder session logs\n"


def _spellings(name: str) -> frozenset[str]:
    """Exact .gitignore lines that ignore the whole folder *name*.

    Returns:
        The eight combinations of an optional leading ``/`` and a trailing
        ``""``, ``/``, ``/*`` or ``/**``.
    """
    return frozenset(
        f"{lead}{name}{tail}" for lead in ("", "/") for tail in ("", "/", "/*", "/**")
    )


# Line written by init -> lines that count as already present
SESSION_LOG_LINES: dict[str, frozenset[str]] = {
    "/.mcp-coder/*": _spellings(".mcp-coder"),
    "/logs/": _spellings("logs"),
}


def _missing_session_log_lines(text: str) -> list[str]:
    """Find the session-log lines a .gitignore text lacks.

    A narrower line such as ``logs/claude-sessions/`` does not count, since
    it leaves the rest of the folder committable.

    Args:
        text: Decoded .gitignore content.

    Returns:
        The missing lines among ``SESSION_LOG_LINES``, in its order.
    """
    present = {line.strip() for line in text.splitlines()}
    return [
        line for line, spellings in SESSION_LOG_LINES.items() if not spellings & present
    ]


def _write_session_log_entries(project_dir: Path) -> tuple[bool, bool]:
    """Gitignore the folders mcp-coder writes session logs to.

    Separate from ``update_gitignore``: the VSCodeClaude session launch
    re-appends that block in every session folder. An undecodable .gitignore
    is read before any write, so it is left untouched.

    Args:
        project_dir: Target project root.

    Returns:
        ``(ok, changed)``: ok is False when the .gitignore could not be read
        or written; changed is True when lines were appended.
    """
    gitignore = project_dir / ".gitignore"
    try:
        existing = (
            gitignore.read_text(encoding="utf-8-sig") if gitignore.exists() else ""
        )
        missing = _missing_session_log_lines(existing)
        if not missing:
            logger.log(OUTPUT, "Gitignore: %s present", ", ".join(SESSION_LOG_LINES))
            return True, False
        addition = SESSION_LOGS_GITIGNORE_HEADER + "".join(
            f"{line}\n" for line in missing
        )
        if existing:
            addition = "\n" + addition  # blank line before the new block
            if not existing.endswith("\n"):
                addition = "\n" + addition
        write_lf_text(gitignore, addition, append=True)
    except (OSError, ValueError) as e:  # UnicodeDecodeError is a ValueError
        logger.warning(
            "Failed to add session log entries to .gitignore in %s: %s",
            project_dir,
            e,
        )
        return False, False

    logger.log(OUTPUT, "Gitignore: %s added", ", ".join(missing))
    return True, True


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
        python = _is_python_toolkit(project_dir)
        added, skipped = _deploy_skills(source_dir, project_dir, skip_python=not python)
        logger.log(OUTPUT, "Skills: %d added, %d skipped", added, skipped)
        if not python:
            for line in _GENERIC_REMINDER:
                logger.log(OUTPUT, line)

    # 3. Gitignore entries: VSCodeClaude session files, then the session-log
    # folders (both modes: project-scoped, like the .claude/ deploy)
    gitignore_ok = _write_gitignore_entries(project_dir)
    logs_ok, logs_added = _write_session_log_entries(project_dir)

    # 4. .mcp-file-access rules, then .scratch/ gitignored (both modes)
    rules = ensure_file_access_rules(project_dir)
    scratch_ok, scratch_added = ensure_scratch_gitignored(project_dir, rules)
    if rules.changed or scratch_added or logs_added:
        logger.log(
            OUTPUT,
            "Commit .gitignore and .mcp-file-access so every clone gets them.",
        )
    files_ok = gitignore_ok and logs_ok and rules.ok and scratch_ok

    # 5. Config creation (skip if --just-skills)
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

    return 0 if files_ok else 1
