"""Implementation-lane safety gates for the shared review engine.

These gates are pure logic that returns ``(reason, details)`` tuples: the round
loop in :mod:`core` calls each at a single thin call site and turns a blocking
result into a ``_fail``. Message-building (open-task listing / capping, the
malformed-tracker cause) lives here, not in ``core.py``, so the core loop stays
under its line budget.

Gate 1 (:func:`check_open_tasks_gate`) is the pre-flight open-tasks check: it
refuses to start ``review-implementation`` when ``pr_info/TASK_TRACKER.md`` has
unchecked ``## Tasks`` items and points the human at ``/implementation_finalise``.
Both gates are gated on ``config.enforce_implementation_gates`` and are a no-op
for the plan lane.
"""

from pathlib import Path

from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    get_incomplete_tasks,
)

from .config import ReviewConfig

# Cap the open-task listing in the failure comment so a large tracker does not
# produce an unreadable wall of text; the total count is still reported.
MAX_LISTED_TASKS = 10


def check_open_tasks_gate(
    config: ReviewConfig, project_dir: Path
) -> tuple[str | None, str | None]:
    """Entry gate: block the run when ``## Tasks`` has unchecked items.

    Args:
        config: The review workflow config; the gate is skipped entirely unless
            ``config.enforce_implementation_gates`` is set (plan lane → no-op).
        project_dir: Repository root; the tracker is read from
            ``project_dir / "pr_info"``.

    Returns:
        ``(None, None)`` to proceed, or ``("tasks", <details>)`` to block the
        run — where ``<details>`` is a human-readable cause line for the failure
        comment (open-task listing, or the malformed-tracker cause).
    """
    if not config.enforce_implementation_gates:
        return None, None
    try:
        tasks = get_incomplete_tasks(str(project_dir / "pr_info"))
    except TaskTrackerFileNotFoundError:
        # No tracker → nothing to enforce; mirrors create_pr's skip behaviour.
        return None, None
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # No ``## Tasks`` section (TaskTrackerSectionNotFoundError) or any other
        # read failure: block, naming the cause. `/implementation_finalise`
        # operates on a well-formed tracker and will not repair the structure.
        return "tasks", (
            f"`pr_info/TASK_TRACKER.md` could not be read as a task list "
            f"({exc}) — fix the tracker structure; "
            f"`/implementation_finalise` will not repair this."
        )
    if not tasks:
        return None, None
    shown = tasks[:MAX_LISTED_TASKS]
    more = len(tasks) - len(shown)
    listing = ", ".join(shown) + (f" … and {more} more" if more else "")
    return "tasks", (
        f"{len(tasks)} open task(s) in `pr_info/TASK_TRACKER.md`: "
        f"{listing} — run `/implementation_finalise`."
    )
