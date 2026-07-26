"""Per-repo boolean config flag resolution.

Provides ``get_repo_flag``: a ``utils``-level primitive that maps a project's
git remote to its ``[coordinator.repos.*]`` config section and reads a typed
boolean flag. Kept separate from ``user_config`` so that module stays a pure
schema reader, free of the ``mcp_workspace_git`` dependency this lookup pulls in.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import get_repository_identifier

from .user_config import find_repo_section_by_url, get_config_values

logger = logging.getLogger(__name__)

__all__ = ["get_repo_flag"]


def get_repo_flag(project_dir: Path, key: str, default: bool = False) -> bool:
    """Resolve a boolean [coordinator.repos.*] flag for a project's git remote.

    Maps project_dir -> git remote https URL -> matching repo config section ->
    typed bool flag value. Returns ``default`` when the repo has no remote, no
    matching section, or the flag is unset / non-boolean.

    Args:
        project_dir: Project directory for git remote URL detection.
        key: Flag key within the repo config section.
        default: Value returned when the flag cannot be resolved.

    Returns:
        The resolved boolean flag value, or ``default``.
    """
    identifier = get_repository_identifier(project_dir)
    repo_url = identifier.https_url if identifier else None
    if not repo_url:
        logger.debug("No git remote for %s; using default %s", project_dir, default)
        return default

    section = find_repo_section_by_url(repo_url)
    if not section:
        logger.debug("No config section for %s; using default %s", repo_url, default)
        return default

    value = get_config_values([(section, key, None)])[(section, key)]
    return value if isinstance(value, bool) else default
