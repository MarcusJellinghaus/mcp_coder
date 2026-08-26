"""CLI utility functions for shared parameter handling.

This module provides utilities that are shared across CLI commands
for parameter parsing and conversion.
"""

import argparse
import logging
import os
import warnings
from pathlib import Path

from mcp_coder.mcp_workspace_git import get_repository_identifier

from ..llm.session import parse_llm_method
from ..llm.types import SUPPORTED_PROVIDERS
from ..prompts.prompt_loader import claude_md_paths
from ..utils.log_utils import OUTPUT
from ..utils.user_config import find_repo_section_by_url, get_config_values

logger = logging.getLogger(__name__)

# Worded so it does not claim to be a complete account of Claude's memory
# chain: the walk does not expand @import directives.
_CONTEXT_LABEL = "Project instructions (Claude cwd walk):"

__all__ = [
    "find_context_claude_md",
    "is_outside_project_dir",
    "log_command_startup",
    "parse_llm_method_from_args",
    "report_context_root",
    "resolve_issue_interaction_flags",
    "resolve_llm_method",
    "resolve_mcp_config_path",
    "resolve_claude_settings_path",
    "resolve_execution_dir",
]


def log_command_startup(command_name: str, project_dir: Path | None = None) -> None:
    """Log version, branch, and project dir at command startup.

    Args:
        command_name: CLI command name (e.g. 'implement', 'create-pr')
        project_dir: Resolved project directory path (None for multi-repo commands)
    """
    from .. import __version__

    if project_dir is not None:
        from mcp_coder.mcp_workspace_git import get_current_branch_name

        try:
            branch = get_current_branch_name(project_dir) or "(unknown)"
        except Exception:
            logger.debug("Failed to query branch name", exc_info=True)
            branch = "(unknown)"
        logger.info(
            "mcp-coder v%s — %s, branch: %s, project: %s",
            __version__,
            command_name,
            branch,
            project_dir,
        )
    else:
        logger.info("mcp-coder v%s — %s", __version__, command_name)


def resolve_issue_interaction_flags(
    args: argparse.Namespace, project_dir: Path
) -> tuple[bool, bool]:
    """Resolve update_issue_labels and post_issue_comments settings.

    Priority: CLI flag (if not None) > config.toml repo section > default (False).

    Looks up the local git remote URL, finds matching [coordinator.repos.*]
    section in config.toml, and merges with CLI flags.

    Args:
        args: Parsed CLI args with update_issue_labels and post_issue_comments
              (both bool | None from BooleanOptionalAction)
        project_dir: Project directory for git remote URL detection

    Returns:
        Tuple of (update_issue_labels: bool, post_issue_comments: bool)
    """
    cli_labels: bool | None = getattr(args, "update_issue_labels", None)
    cli_comments: bool | None = getattr(args, "post_issue_comments", None)

    # Get config values (default False)
    cfg_labels = False
    cfg_comments = False
    identifier = get_repository_identifier(project_dir)
    repo_url = identifier.https_url if identifier else None
    if repo_url:
        section = find_repo_section_by_url(repo_url)
        if section:
            config = get_config_values(
                [
                    (section, "update_issue_labels", None),
                    (section, "post_issue_comments", None),
                ]
            )
            cfg_labels = config[(section, "update_issue_labels")] is True
            cfg_comments = config[(section, "post_issue_comments")] is True

    # Merge: CLI wins if not None, else config, else False
    return (
        cli_labels if cli_labels is not None else cfg_labels,
        cli_comments if cli_comments is not None else cfg_comments,
    )


def resolve_llm_method(llm_method: str | None) -> tuple[str, str]:
    """Resolve LLM method from CLI arg, env var, config file, or default.

    Resolution order:
        1. CLI argument
        2. Environment variable MCP_CODER_LLM_PROVIDER
        3. Config [llm] default_provider
        4. Default "claude"

    Args:
        llm_method: CLI --llm-method value, or None if not specified

    Returns:
        Tuple of (provider, source) where source describes where the value came from.
        Source is one of: "cli argument", "env MCP_CODER_LLM_PROVIDER",
        "config default_provider", "default".

    Raises:
        ValueError: If the resolved provider is not a valid value.
    """
    if llm_method is not None:
        provider, source = llm_method, "cli argument"
    elif (env_value := os.environ.get("MCP_CODER_LLM_PROVIDER")) is not None:
        provider, source = env_value, "env MCP_CODER_LLM_PROVIDER"
    else:
        config = get_config_values([("llm", "default_provider", None)])
        raw_provider = config[("llm", "default_provider")]
        if isinstance(raw_provider, str):
            provider, source = raw_provider, "config default_provider"
        else:
            return ("claude", "default")

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Invalid LLM provider {provider!r} from {source}. "
            f"Valid values: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )
    return (provider, source)


def parse_llm_method_from_args(llm_method: str) -> str:
    """Parse CLI llm_method into provider name for internal APIs.

    Args:
        llm_method: CLI parameter ('claude' or 'langchain')

    Returns:
        Provider name (e.g., "claude" or "langchain")

    Example:
        >>> provider = parse_llm_method_from_args("claude")
        >>> print(provider)
        claude
    """
    return parse_llm_method(llm_method)


def resolve_mcp_config_path(
    mcp_config: str | None,
    project_dir: str | None = None,
) -> str | None:
    """Resolve MCP config path to absolute path.

    Resolution priority:
        1. CLI argument (``mcp_config``)
        2. Environment variable ``MCP_CODER_MCP_CONFIG``
        3. ``[mcp] default_config_path`` from TOML config
        4. Auto-detect ``.mcp.json``

    Relative path semantics (uniform across all four sources):
        - Absolute path → used as-is.
        - Relative path → resolved against ``project_dir``.
        - When ``project_dir`` is ``None`` → relative paths fall back to CWD.

    Error semantics:
        - Source 1 (CLI): strict — missing file raises ``FileNotFoundError``.
        - Sources 2, 3 (env, config): lenient — missing file logs a warning
          and falls through to the next source.

    Args:
        mcp_config: MCP config path (relative or absolute) or None
        project_dir: Project directory used as the base for relative paths
            (defaults to CWD when None)

    Returns:
        Absolute path as string, or None if no config found

    Raises:
        FileNotFoundError: If an explicitly provided MCP config file does not exist
    """
    base_dir = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()

    def _resolve_relative(path_str: str) -> Path:
        path = Path(path_str)
        return path.resolve() if path.is_absolute() else (base_dir / path).resolve()

    if mcp_config is not None:
        # Explicit path: resolve relative to base_dir and validate
        mcp_config_path = _resolve_relative(mcp_config)
        if not mcp_config_path.exists():
            raise FileNotFoundError(
                f"MCP config file not found: {mcp_config_path}\n"
                f"  Original path: {mcp_config}\n"
                f"  Project directory: {base_dir}\n"
                f"  Current directory: {Path.cwd()}"
            )
        logger.info("MCP config (from --mcp-config): %s", mcp_config_path)
        return str(mcp_config_path)

    # Check env var MCP_CODER_MCP_CONFIG
    if (env_path := os.environ.get("MCP_CODER_MCP_CONFIG")) is not None:
        resolved = _resolve_relative(env_path)
        if resolved.exists():
            logger.info("MCP config (from env MCP_CODER_MCP_CONFIG): %s", resolved)
            return str(resolved)
        logger.warning(
            "MCP_CODER_MCP_CONFIG=%s: file not found, falling back to auto-detect",
            env_path,
        )

    # Check config file [mcp] default_config_path
    config = get_config_values([("mcp", "default_config_path", "_NO_ENV_VAR_")])
    cfg_path = config[("mcp", "default_config_path")]
    if isinstance(cfg_path, str):
        resolved = _resolve_relative(cfg_path)
        if resolved.exists():
            logger.info("MCP config (from [mcp] default_config_path): %s", resolved)
            return str(resolved)
        logger.warning(
            "[mcp] default_config_path=%s: file not found, falling back to auto-detect",
            cfg_path,
        )

    # Auto-detect .mcp.json
    candidate = base_dir / ".mcp.json"
    if candidate.exists():
        resolved_path = str(candidate.resolve())
        logger.info("MCP config (auto-detected): %s", resolved_path)
        return resolved_path

    logger.debug(f"No .mcp.json found in {base_dir}")
    return None


def resolve_claude_settings_path(
    settings_file: str | None,
    project_dir: str | None = None,
) -> str | None:
    """Resolve Claude Code settings file path to absolute path.

    Resolution priority:
        1. CLI argument (``settings_file``)
        2. Environment variable ``MCP_CODER_CLAUDE_SETTINGS``
        3. ``[claude] default_settings_path`` from TOML config
        4. Auto-detect ``<project_dir>/.claude/settings.local.json``
        5. Auto-detect ``<project_dir>/.claude/settings.json``

    Relative path semantics (uniform across sources 1-3):
        - Absolute path → used as-is.
        - Relative path → resolved against ``project_dir`` (or CWD when None).

    Error semantics:
        - Source 1 (CLI): strict — missing file raises ``FileNotFoundError``.
        - Sources 2, 3 (env, config): lenient — missing file logs a warning
          and falls through.
        - Sources 4, 5 (auto-detect): silent — fall through if absent.

    Args:
        settings_file: Settings file path (relative or absolute) or None.
        project_dir: Project directory used as the base for relative paths
            (defaults to CWD when None).

    Returns:
        Absolute path as string, or None if no settings file found.

    Raises:
        FileNotFoundError: If an explicitly provided settings file does not exist.
    """
    base_dir = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()

    def _resolve_relative(path_str: str) -> Path:
        path = Path(path_str)
        return path.resolve() if path.is_absolute() else (base_dir / path).resolve()

    if settings_file is not None:
        # Explicit path: resolve relative to base_dir and validate
        settings_path = _resolve_relative(settings_file)
        if not settings_path.exists():
            raise FileNotFoundError(
                f"Claude settings file not found: {settings_path}\n"
                f"  Original path: {settings_file}\n"
                f"  Project directory: {base_dir}\n"
                f"  Current directory: {Path.cwd()}"
            )
        logger.info("Claude settings (from --settings): %s", settings_path)
        return str(settings_path)

    # Check env var MCP_CODER_CLAUDE_SETTINGS
    if (env_path := os.environ.get("MCP_CODER_CLAUDE_SETTINGS")) is not None:
        resolved = _resolve_relative(env_path)
        if resolved.exists():
            logger.info(
                "Claude settings (from env MCP_CODER_CLAUDE_SETTINGS): %s", resolved
            )
            return str(resolved)
        logger.warning(
            "MCP_CODER_CLAUDE_SETTINGS=%s: file not found, falling back to auto-detect",
            env_path,
        )

    # Check config file [claude] default_settings_path
    config = get_config_values([("claude", "default_settings_path", "_NO_ENV_VAR_")])
    cfg_path = config[("claude", "default_settings_path")]
    if isinstance(cfg_path, str):
        resolved = _resolve_relative(cfg_path)
        if resolved.exists():
            logger.info(
                "Claude settings (from [claude] default_settings_path): %s",
                resolved,
            )
            return str(resolved)
        logger.warning(
            "[claude] default_settings_path=%s: file not found, falling back to auto-detect",
            cfg_path,
        )

    # Auto-detect <project_dir>/.claude/settings.local.json first, then settings.json
    local_candidate = base_dir / ".claude" / "settings.local.json"
    if local_candidate.exists():
        resolved_path = str(local_candidate.resolve())
        logger.info("Claude settings (auto-detected): %s", resolved_path)
        return resolved_path

    shared_candidate = base_dir / ".claude" / "settings.json"
    if shared_candidate.exists():
        resolved_path = str(shared_candidate.resolve())
        logger.info("Claude settings (auto-detected): %s", resolved_path)
        return resolved_path

    logger.debug(f"No Claude settings file found in {base_dir / '.claude'}")
    return None


def find_context_claude_md(start: Path, stop_at: Path | None = None) -> list[Path]:
    """Find the CLAUDE.md files Claude's cwd-upward walk would load.

    Walks from ``start`` upward and returns every existing candidate at EVERY
    ancestor level, because Claude Code loads the whole chain rather than the
    nearest file. Reporting only the nearest level would hide ancestor files
    that are equally in effect.

    The user-level ``~/.claude/CLAUDE.md`` is therefore included whenever
    ``start`` sits under the home directory - which is the normal case, and
    matches what Claude actually loads. Still not a complete account of
    Claude's memory chain: ``@import`` directives are not expanded.

    Args:
        start: Directory to start the walk from.
        stop_at: Last directory to examine, inclusive. ``None`` (production
            default) walks to the filesystem root. A test-only boundary, so
            "found nothing" can be asserted without depending on directories
            above a temporary path.

    Returns:
        Resolved paths, nearest level first, or [] if none exist. Within one
        level the candidate order is a membership list, not a precedence rule.
    """
    hits: list[Path] = []
    try:
        current = start.resolve()
        boundary = stop_at.resolve() if stop_at is not None else None

        while True:
            hits.extend(p.resolve() for p in claude_md_paths(current) if p.exists())

            # Checked after collecting, so the boundary is examined inclusively.
            if boundary is not None and current == boundary:
                break
            if current.parent == current:
                break
            current = current.parent
    except OSError:
        # A permission error mid-walk must not crash a workflow - report what
        # was found below it rather than nothing.
        pass

    return hits


def is_outside_project_dir(path: Path, project_dir: str | Path | None) -> bool:
    """Return True when ``path`` does not lie inside ``project_dir``.

    The single definition of "outside" shared by the run-time report and the
    verify report. Always False when project_dir is None - with no anchor there
    is nothing to be outside of.
    """
    if project_dir is None:
        return False

    try:
        return not path.resolve().is_relative_to(Path(project_dir).resolve())
    except OSError:
        # Do not warn about a path we could not resolve.
        return False


def report_context_root(execution_dir: Path, project_dir: str | Path | None) -> None:
    """Log the Claude working directory and the project instructions in effect.

    Logs at OUTPUT level. Warns when no resolved file lies inside project_dir.
    """
    logger.log(OUTPUT, "Claude working directory: %s", execution_dir)

    hits = find_context_claude_md(execution_dir)
    if not hits:
        logger.log(OUTPUT, "%s none found", _CONTEXT_LABEL)
        return

    for hit in hits:
        logger.log(OUTPUT, "%s %s", _CONTEXT_LABEL, hit)

    # One warning per run, keyed on the absence of an inside hit rather than on
    # each outside one. The walk reaches every ancestor and every ancestor is
    # outside project_dir by definition, so a per-hit warning fires on almost
    # every run. Having no inside hit at all is the December drift itself.
    if all(is_outside_project_dir(hit, project_dir) for hit in hits):
        logger.warning(
            "No project instructions file lies inside the project directory "
            "(project: %s) — the agent's rules come only from outside it: %s. "
            "Either the driven project has no CLAUDE.md of its own, or Claude "
            "is not running inside it.",
            project_dir,
            ", ".join(str(hit) for hit in hits),
        )


def resolve_execution_dir(
    execution_dir: str | None,
    project_dir: str | Path | None = None,
) -> Path:
    """Resolve execution directory path to absolute Path object.

    Args:
        execution_dir: Optional execution directory path (deprecated, see #1132)
                      - None: Falls back to project_dir, or CWD if not given
                      - Absolute path: Validates and returns as Path
                      - Relative path: Resolves relative to CWD
        project_dir: Optional project directory, used as the default execution
                     directory. Resolved but deliberately NOT existence-checked -
                     each command validates its own project_dir and owns the
                     error message for a bad one.

    Returns:
        Path: Absolute path to execution directory

    Raises:
        ValueError: If a specified execution_dir doesn't exist

    Examples:
        >>> resolve_execution_dir(None, project_dir='/my/project')
        PosixPath('/my/project')

        >>> resolve_execution_dir(None)
        PosixPath('/current/working/dir')

        >>> resolve_execution_dir('/absolute/path')
        PosixPath('/absolute/path')

        >>> resolve_execution_dir('./relative')
        PosixPath('/current/working/dir/relative')
    """
    if execution_dir is None:
        resolved = Path.cwd() if project_dir is None else Path(project_dir).resolve()
        report_context_root(resolved, project_dir)
        return resolved

    deprecation_message = (
        "--execution-dir is deprecated; the project directory is used as the "
        "execution directory by default. Removal is tracked in #1132."
    )
    warnings.warn(deprecation_message, DeprecationWarning, stacklevel=2)
    logger.warning(deprecation_message)

    path = Path(execution_dir)

    # Convert relative paths to absolute
    if not path.is_absolute():
        path = Path.cwd() / path

    # Validate that the directory exists
    if not path.exists():
        raise ValueError(
            f"Execution directory does not exist: {path}\n"
            f"  Original path: {execution_dir}\n"
            f"  Current directory: {Path.cwd()}"
        )

    logger.debug(f"Resolved execution directory: {execution_dir} -> {path}")
    resolved = path.resolve()
    report_context_root(resolved, project_dir)
    return resolved
