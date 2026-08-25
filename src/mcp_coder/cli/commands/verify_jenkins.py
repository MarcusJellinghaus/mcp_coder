"""Jenkins verification sections for the ``mcp-coder verify`` command.

``verify`` already validates the config file that holds the ``[jenkins]``
credentials, but never tested them: a wrong API token or a missing
``Overall/Read`` permission only surfaced later, as a wall of Jenkins HTML from
a coordinator run.

This module probes the server and every configured executor job using the same
helpers the error path uses (``jenkins_operations.diagnostics``), so a verify
run and a failed dispatch produce the same diagnosis.

A deliberate departure from the convention that domain verify functions live in
their domain package: the probes belong to ``jenkins_operations``, but the
section assembly is CLI presentation, and ``verify.py`` is already close to the
repo file-size limit.
"""

import logging
from typing import Any

from ...utils.jenkins_operations.client import JenkinsClient, _get_jenkins_config
from ...utils.jenkins_operations.diagnostics import (
    DOCS_POINTER,
    diagnose_403,
    diagnose_404,
    job_url_path,
    probe,
)
from ...utils.user_config import load_config

logger = logging.getLogger(__name__)

# diagnostics owns the docs path; a section renders it as a bare pointer.
_INSTALL_HINT = DOCS_POINTER.removeprefix("See ")

_NOT_CHECKED: dict[str, Any] = {"ok": None, "value": "not checked"}


def _build_server_result(session: Any, base_url: str, username: str) -> dict[str, Any]:
    """Derive the three JENKINS rows from a single ``/api/json`` probe.

    Args:
        session: python-jenkins' own requests session (see
            ``JenkinsClient._http``). Annotated ``Any`` so this module need not
            import ``requests``, which the ``requests_library_isolation``
            contract confines to ``jenkins_operations``.
        base_url: Server URL without a trailing slash.
        username: API user, shown on the authentication row.

    Returns:
        ``_format_section``-shaped dict with ``server``, ``authentication``,
        ``overall_read`` and ``overall_ok``.
    """
    root = probe(session, base_url, "/api/json")
    reachable: dict[str, Any] = {"ok": True, "value": f"{base_url} reachable"}
    authenticated: dict[str, Any] = {
        "ok": True,
        "value": f"{username} (API token valid)",
    }
    result: dict[str, Any] = {}

    if root.status == 200:
        result["server"] = reachable
        result["authentication"] = authenticated
        result["overall_read"] = {"ok": True, "value": "granted"}
    elif root.status == 401:
        result["server"] = reachable
        result["authentication"] = {
            "ok": False,
            "value": username,
            "error": root.error_text
            or "401 Unauthorized - check the username and API token",
            "install_hint": _INSTALL_HINT,
        }
        # Authorization is unknowable while authentication fails.
        result["overall_read"] = dict(_NOT_CHECKED)
    elif root.status == 403:
        result["server"] = reachable
        result["authentication"] = authenticated
        result["overall_read"] = {
            "ok": False,
            "value": "denied",
            "error": diagnose_403(session, base_url, root.error_text),
            "install_hint": _INSTALL_HINT,
        }
    else:
        # status is None for a transport failure; anything else is unmodelled.
        error = (
            (root.error_text or "unreachable")
            if root.status is None
            else f"unexpected HTTP {root.status}"
        )
        result["server"] = {
            "ok": False,
            "value": base_url,
            "error": error,
            "install_hint": _INSTALL_HINT,
        }
        result["authentication"] = dict(_NOT_CHECKED)
        result["overall_read"] = dict(_NOT_CHECKED)

    result["overall_ok"] = all(row.get("ok") is not False for row in result.values())
    return result


def _probe_job(session: Any, base_url: str, job_path: str) -> dict[str, Any]:
    """Check Job/Read on one executor job path.

    Args:
        session: python-jenkins' own requests session.
        base_url: Server URL without a trailing slash.
        job_path: Slash-separated job path, e.g. "Windows-Agents/Executor".

    Returns:
        ``_format_section``-shaped row for the job.
    """
    result = probe(session, base_url, job_url_path(job_path) + "/api/json")
    if result.status == 200:
        return {"ok": True, "value": job_path}

    if result.status == 404:
        error = diagnose_404(session, base_url, job_path)
    elif result.status == 403:
        error = diagnose_403(session, base_url, result.error_text)
    elif result.status is None:
        error = result.error_text or "unreachable"
    else:
        error = f"unexpected HTTP {result.status}"
    return {
        "ok": False,
        "value": job_path,
        "error": error,
        "install_hint": _INSTALL_HINT,
    }


def _build_jobs_result(
    session: Any, base_url: str, repos: dict[str, Any]
) -> dict[str, Any]:
    """Build one row per coordinator repo that names an executor job.

    Args:
        session: python-jenkins' own requests session.
        base_url: Server URL without a trailing slash.
        repos: ``[coordinator.repos.*]`` sub-tables, keyed by repo name.

    Returns:
        ``_format_section``-shaped dict keyed by repo name plus ``overall_ok``,
        or ``{}`` when no repo names a job path (nothing to report).
    """
    result: dict[str, Any] = {}
    for repo_name, repo_config in repos.items():
        if not isinstance(repo_config, dict):
            continue
        job_path = repo_config.get("executor_job_path")
        if not isinstance(job_path, str) or not job_path.strip():
            continue
        result[repo_name] = _probe_job(session, base_url, job_path)

    if not result:
        return {}
    result["overall_ok"] = all(row["ok"] for row in result.values())
    return result


def verify_jenkins() -> tuple[dict[str, Any], dict[str, Any]]:
    """Probe Jenkins connectivity/permissions and per-repo Job/Read access.

    Credentials come from ``_get_jenkins_config()`` rather than
    ``load_config()``: only the former applies the ``JENKINS_URL`` /
    ``JENKINS_USER`` / ``JENKINS_TOKEN`` env overrides, so it is the same
    resolution the coordinator dispatches with. The repo list comes from
    ``load_config()`` directly, because no env overrides exist for
    ``[coordinator.repos.*]``.

    Returns:
        ``(server_result, jobs_result)``. Each is a ``_format_section``-shaped
        dict - ``{key: {"ok": bool | None, "value": str, "error"?: str,
        "install_hint"?: str}}`` plus ``"overall_ok"``. Both are ``{}``
        (skipped, exit-neutral) when ``[jenkins]`` is unconfigured;
        ``jobs_result`` is also ``{}`` when the server section failed or no
        coordinator repos name an executor job.
    """
    try:
        credentials = _get_jenkins_config()
    except ValueError:
        # Malformed TOML - the CONFIG section already reports it.
        logger.debug("Skipping Jenkins verification: config could not be read")
        return {}, {}

    server_url = credentials.get("server_url")
    username = credentials.get("username")
    api_token = credentials.get("api_token")
    if not (server_url and username and api_token):
        return {}, {}

    try:
        client = JenkinsClient(server_url, username, api_token)
    except ValueError:
        return {}, {}

    # pylint: disable-next=protected-access
    session = client._http  # documented probe seam, see client.py
    base_url = client.base_url

    server_result = _build_server_result(session, base_url, username)
    if not server_result["overall_ok"]:
        # Every job row would just repeat the same upstream cause.
        return server_result, {}

    try:
        coordinator: Any = load_config().get("coordinator", {})
    except ValueError:
        return server_result, {}
    repos = coordinator.get("repos", {}) if isinstance(coordinator, dict) else {}
    if not isinstance(repos, dict) or not repos:
        return server_result, {}

    return server_result, _build_jobs_result(session, base_url, repos)


__all__ = ["verify_jenkins"]
