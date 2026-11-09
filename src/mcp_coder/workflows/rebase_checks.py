"""Deterministic check layer for the ``mcp-coder rebase`` workflow.

Runs the requests bound to the ``rebase`` / ``rebase_automated`` toolkit entry
and reduces their findings to line-insensitive failure keys so the
orchestrator in ``rebase.py`` can compare a pre-rebase baseline against a
post-rebase verification run as a pure set difference.
"""

import logging
from pathlib import Path

from mcp_coder.utils.toolkit_runner import load_toolkit, run_binding

logger = logging.getLogger(__name__)


class CheckRunError(Exception):
    """A check failed to RUN (infrastructure), as opposed to reporting failures."""


FailureKey = str
"""``"<action>: <Finding.key>"``, e.g. ``"test: tests/test_a.py::test_x"``.

Finding keys are line-insensitive; the action prefix avoids collisions.
"""

FixTexts = dict[str, str]
"""Action -> the ``fix_text`` (or ``summary``) of its ``findings`` results.

Texts of several requests for the same action are joined by a blank line.
"""


def _run_all_checks(
    project_dir: Path, automated: bool = False
) -> tuple[set[FailureKey], FixTexts]:
    """Run the rebase binding and union its findings into failure keys.

    Findings (failed tests, lint messages, type errors) become keys; a request
    whose result is ``error``, or a toolkit that fails to load, raises
    ``CheckRunError``. A ``skipped`` request adds no keys.

    Args:
        project_dir: Path to the project directory.
        automated: Run the ``rebase_automated`` binding instead of ``rebase``.

    Returns:
        ``(keys, fix_texts)``: the union of failure keys across all bound
        requests, and per action with findings the joined ``fix_text``
        (falling back to ``summary``).

    Raises:
        CheckRunError: If the toolkit fails to load or a request fails to run.
    """
    entry = "rebase_automated" if automated else "rebase"
    try:
        results = run_binding(load_toolkit(project_dir), project_dir, entry)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise CheckRunError(f"toolkit: {exc}") from exc
    keys: set[FailureKey] = set()
    texts: dict[str, list[str]] = {}
    for request, result in results:
        if result.status == "error":
            raise CheckRunError(f"{request}: {result.summary}")
        if result.status == "skipped":
            logger.info("%s skipped: %s", request, result.summary)
        action = request.split("@")[0]
        keys |= {f"{action}: {finding.key}" for finding in result.findings}
        if result.status == "findings":
            texts.setdefault(action, []).append(result.fix_text or result.summary)
    return keys, {action: "\n\n".join(parts) for action, parts in texts.items()}
