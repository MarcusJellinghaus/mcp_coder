"""Constants for the implement workflow.

This module consolidates all constants used across the implement workflow modules
(core.py, task_processing.py, prerequisites.py) to ensure consistency and
single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Directory paths + shared tuning constants (relocated to workflow_steps;
# re-exported here so existing `from .constants import …` call sites across
# implement keep working). Redundant aliases mark these as explicit re-exports
# for mypy.
from mcp_coder.workflow_steps.constants import (
    COMMIT_MESSAGE_FILE as COMMIT_MESSAGE_FILE,
)
from mcp_coder.workflow_steps.constants import (
    LLM_INACTIVITY_TIMEOUT_SECONDS as LLM_INACTIVITY_TIMEOUT_SECONDS,
)
from mcp_coder.workflow_steps.constants import PR_INFO_DIR as PR_INFO_DIR

# LLM timeout settings (in seconds)
#
# Every value below is an *inactivity/silence* budget (max seconds with no stdout
# line from `claude`), NOT a wall-clock cap. Since the blocking entrypoint now drains
# the streaming core (stream_subprocess with an inactivity watchdog), each caller's
# `timeout` bounds silence, not total runtime. All are kept below the external CI
# step/build cap so mcp-coder kills a hung call before the external watchdog SIGKILLs it.

# Inactivity budget (was wall-clock), kept below the CI step cap.
LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS = 600  # 10 minutes of silence
# Inactivity budget (was wall-clock), kept below the CI step cap.
LLM_FINALISATION_TIMEOUT_SECONDS = 600  # 10 minutes of silence

# Mypy checking behavior
RUN_MYPY_AFTER_EACH_TASK = False  # If False, mypy runs once after all tasks complete

# Used by the `implement` workflow's task-processing retry loop
# (process_task_with_retry in task_processing.py) to bound retries
# when an LLM call produces zero file changes for a task.
MAX_NO_CHANGE_RETRIES = 3  # Max LLM calls per task when zero changes detected


class FailureCategory(Enum):
    """Maps 1:1 to failure label IDs in labels.json."""

    GENERAL = "implementing_failed"
    CI_FIX_EXHAUSTED = "ci_fix_needed"
    LLM_TIMEOUT = "llm_timeout"
    MCP_UNAVAILABLE = "mcp_unavailable"
    TASK_TRACKER_PREP_FAILED = "task_tracker_prep_failed"
    NO_CHANGES_AFTER_RETRIES = "no_changes_after_retries"


@dataclass(frozen=True)
class WorkflowFailure:
    """Structured failure info for the implement workflow."""

    category: FailureCategory
    stage: str
    message: str
    tasks_completed: int = 0
    tasks_total: int = 0
    build_url: str | None = None
    elapsed_time: float | None = None
