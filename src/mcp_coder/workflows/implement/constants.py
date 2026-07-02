"""Constants for the implement workflow.

This module consolidates all constants used across the implement workflow modules
(core.py, task_processing.py, prerequisites.py) to ensure consistency and
single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Directory paths
PR_INFO_DIR = "pr_info"
COMMIT_MESSAGE_FILE = f"{PR_INFO_DIR}/.commit_message.txt"

# LLM timeout settings (in seconds)
#
# Every value below is an *inactivity/silence* budget (max seconds with no stdout
# line from `claude`), NOT a wall-clock cap. Since the blocking entrypoint now drains
# the streaming core (stream_subprocess with an inactivity watchdog), each caller's
# `timeout` bounds silence, not total runtime. All are kept below the external CI
# step/build cap so mcp-coder kills a hung call before the external watchdog SIGKILLs it.

# Inactivity/silence budget (max seconds with no stdout line from `claude`), NOT wall-clock.
# 600s gives headroom for a long *silent* MCP tool call (e.g. a multi-minute run_pytest) at the
# tool-using autonomous sites (implement, mypy-fix, CI-fix). Kept below the external CI step/build
# cap so mcp-coder kills a hung call before the external watchdog SIGKILLs it.
LLM_INACTIVITY_TIMEOUT_SECONDS = 600
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

# CI check constants
# Inactivity budget (was wall-clock), kept below the CI step cap. CI-analysis is a
# pure-LLM call (no MCP tools), so 300s is safe: an LLM emits a token quickly.
LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300  # 5 minutes of silence for CI failure analysis
CI_POLL_INTERVAL_SECONDS = 15  # Poll CI status every 15 seconds
CI_MAX_POLL_ATTEMPTS = 50  # Max 50 attempts = 12.5 minutes max wait
CI_MAX_FIX_ATTEMPTS = 4  # Max 4 fix attempts before giving up
CI_NEW_RUN_POLL_INTERVAL_SECONDS = 5  # Poll for new CI run every 5 seconds
CI_NEW_RUN_MAX_POLL_ATTEMPTS = 6  # Max 6 attempts = 30 seconds to detect new run
# Note: CI fix is a tool-using site and uses LLM_INACTIVITY_TIMEOUT_SECONDS (600s).


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
