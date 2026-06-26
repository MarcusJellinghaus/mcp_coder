"""Persisted audit trail for vscodeclaude session assessments.

One **global** file (sibling of ``sessions.json``), one **run-block** per command
invocation (spanning all repos), trimmed to the **last 50 runs** as a ring buffer,
written **only** by ``apply()`` runs. Reuses the ``sessions.json`` write discipline:
``mkdir(parents=True, exist_ok=True)`` + ``write_text(json.dumps(..., indent=2))``.

The serializer is NOT re-implemented here: :func:`assessment_to_record` delegates to
the ONE serializer (:meth:`SessionAssessment.to_audit_record`) so the audit trail,
``--explain``, and the enriched VSCode column all read the same source and cannot
drift.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...utils.user_app_data import get_user_app_data_dir
from .types import SessionAssessment, VSCodeClaudeSession

logger = logging.getLogger(__name__)

# Ring-buffer size: keep at most this many run-blocks (newest kept).
MAX_AUDIT_RUNS = 50


def get_audit_file_path() -> Path:
    """Get path to the global audit JSON file.

    Returns:
        Path to ~/.mcp_coder/coordinator_cache/vscodeclaude_audit.json
        (global, a sibling of vscodeclaude_sessions.json).
    """
    return (
        get_user_app_data_dir("mcp_coder")
        / "coordinator_cache"
        / "vscodeclaude_audit.json"
    )


def _load_audit() -> dict[str, Any]:
    """Load the audit file, returning ``{"runs": []}`` on any failure.

    Returns:
        The parsed audit dict with a guaranteed ``runs`` list.
    """
    audit_file = get_audit_file_path()
    if not audit_file.exists():
        return {"runs": []}
    try:
        data: dict[str, Any] = json.loads(audit_file.read_text(encoding="utf-8"))
        if "runs" not in data:
            data["runs"] = []
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load audit file: %s", e)
        return {"runs": []}


def append_run(
    records: list[dict[str, Any]], *, max_runs: int = MAX_AUDIT_RUNS
) -> None:
    """Append one run-block, trim to the last ``max_runs`` runs (ring buffer).

    Reuses the ``sessions.json`` atomic-rewrite discipline: load the whole file,
    append the new run-block (newest last), trim to the last ``max_runs`` runs,
    then rewrite the file in one ``write_text``.

    Args:
        records: One audit record per assessed session for this invocation.
        max_runs: Ring-buffer size; only the newest ``max_runs`` runs are kept.
    """
    data = _load_audit()
    data["runs"].append(
        {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "records": records,
        }
    )
    data["runs"] = data["runs"][-max_runs:]

    audit_file = get_audit_file_path()
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def assessment_to_record(
    a: SessionAssessment, session: VSCodeClaudeSession
) -> dict[str, Any]:
    """Build one audit record by delegating to the ONE serializer.

    Do NOT re-flatten here: the audit trail, ``--explain``, and the VSCode column
    must all read the same source (:meth:`SessionAssessment.to_audit_record`) so
    they cannot drift.

    Args:
        a: The assessment to serialize.
        session: The session backing the assessment (supplies repo/issue/status).

    Returns:
        A JSON-safe audit record dict.
    """
    return a.to_audit_record(session)
