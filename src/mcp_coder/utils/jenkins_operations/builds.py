"""Pure functions for listing recent Jenkins builds.

All functions here are I/O-free: they build the ``tree=`` query, flatten the
JSON response into BuildInfo objects, and select, validate and name builds.

Jenkins has no recursive ``tree`` syntax, so build_tree_query spells out the
nested ``jobs[...]`` levels down to MAX_DEPTH. Jobs nested deeper than
MAX_DEPTH (counting folders and multibranch projects) are not reported.
"""

import re
from collections.abc import Collection, Iterable
from datetime import datetime, timezone
from typing import Any

from .models import BuildInfo

VALID_STATUSES: tuple[str, ...] = (
    "running",
    "success",
    "unstable",
    "failure",
    "aborted",
    "not_built",
    "unknown",
)
MAX_DEPTH = 4
BUILDS_CAP = 100  # Jenkins returns at most the newest 100 builds per job via `builds`

_BUILD_FIELDS = "number,building,result,timestamp,duration,url"
_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def map_status(build: dict[str, Any]) -> str:
    """Map a raw Jenkins build dict to one of VALID_STATUSES.

    Args:
        build: Build dict with ``building`` and ``result`` keys

    Returns:
        "running" while building, else the lowercased result or "unknown"
    """
    if build.get("building"):
        return "running"
    result = build.get("result")
    return str(result).lower() if result else "unknown"


def split_job_path(job_path: str) -> tuple[str, str]:
    """Split a Jenkins fullName into folder and job name.

    Args:
        job_path: Jenkins fullName, e.g. "A/B/job"

    Returns:
        Tuple of (folder, job_name); folder is "" at top level
    """
    folder, _, name = job_path.rpartition("/")
    return folder, name


def build_tree_query(limit: int) -> str:
    """Build the ``?tree=`` query for recent builds of all jobs.

    Args:
        limit: Maximum number of builds requested per job

    Returns:
        Query string starting with "?tree=jobs[", nested MAX_DEPTH levels deep
    """
    field = "builds" if limit <= BUILDS_CAP else "allBuilds"
    level = f"fullName,url,{field}[{_BUILD_FIELDS}]{{0,{limit}}}"
    inner = level
    for _ in range(MAX_DEPTH - 1):
        inner = f"{level},jobs[{inner}]"
    return f"?tree=jobs[{inner}]"


def flatten_builds(tree: dict[str, Any]) -> list[BuildInfo]:
    """Flatten a ``tree=`` response into BuildInfo objects.

    Args:
        tree: JSON response containing nested ``jobs`` lists

    Returns:
        Builds in tree order (unsorted); [] when the tree has no jobs
    """
    result: list[BuildInfo] = []
    for job in tree.get("jobs") or []:
        job_path = job["fullName"]
        folder, job_name = split_job_path(job_path)
        for build in job.get("builds") or job.get("allBuilds") or []:
            status = map_status(build)
            result.append(
                BuildInfo(
                    job_path=job_path,
                    folder=folder,
                    job_name=job_name,
                    number=build["number"],
                    status=status,
                    timestamp=datetime.fromtimestamp(
                        build["timestamp"] / 1000, tz=timezone.utc
                    ),
                    duration_ms=(
                        None
                        if status in ("running", "unknown")
                        else build.get("duration")
                    ),
                    url=build["url"],
                )
            )
        result.extend(flatten_builds(job))
    return result


def validate_statuses(statuses: Iterable[str] | None) -> None:
    """Check that every status is one of VALID_STATUSES.

    Args:
        statuses: Statuses to check, or None

    Raises:
        ValueError: If a status is not in VALID_STATUSES
    """
    for status in statuses or ():
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Unknown status '{status}'. Valid values: {', '.join(VALID_STATUSES)}"
            )


def select_builds(
    builds: list[BuildInfo], limit: int, statuses: Collection[str] | None
) -> list[BuildInfo]:
    """Keep the newest ``limit`` builds, then filter by status.

    Args:
        builds: Builds from all jobs, in any order
        limit: Number of newest builds to keep before filtering
        statuses: Statuses to keep, or None/empty for all

    Returns:
        New list, newest first
    """
    newest = sorted(builds, key=lambda b: b.timestamp, reverse=True)[:limit]
    if not statuses:
        return newest
    return [b for b in newest if b.status in statuses]


def log_filename(job_path: str, number: int) -> str:
    """Return a filesystem-safe filename for a build's console log.

    Args:
        job_path: Jenkins fullName (URL-encoded segments are kept as-is)
        number: Build number

    Returns:
        Filename like "A_B_job_5.txt"
    """
    return _INVALID_FILENAME_CHARS.sub("_", job_path) + f"_{number}.txt"
