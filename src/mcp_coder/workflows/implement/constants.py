"""Constants for the implement workflow.

This module consolidates all constants used across the implement workflow modules
(core.py, task_processing.py, prerequisites.py) to ensure consistency and
single source of truth.
"""

# Directory paths
PR_INFO_DIR = "pr_info"
COMMIT_MESSAGE_FILE = f"{PR_INFO_DIR}/.commit_message.txt"

# LLM timeout settings (in seconds)
LLM_IMPLEMENTATION_TIMEOUT_SECONDS = 3600  # 60 minutes
LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS = 600  # 10 minutes
LLM_FINALISATION_TIMEOUT_SECONDS = 600  # 10 minutes

# Mypy checking behavior
RUN_MYPY_AFTER_EACH_TASK = False  # If False, mypy runs once after all tasks complete

# CI check constants
LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300  # 5 minutes for CI failure analysis
CI_POLL_INTERVAL_SECONDS = 15  # Poll CI status every 15 seconds
CI_MAX_POLL_ATTEMPTS = 50  # Max 50 attempts = 12.5 minutes max wait
CI_MAX_FIX_ATTEMPTS = 3  # Max 3 fix attempts before giving up
CI_NEW_RUN_POLL_INTERVAL_SECONDS = 5  # Poll for new CI run every 5 seconds
CI_NEW_RUN_MAX_POLL_ATTEMPTS = 6  # Max 6 attempts = 30 seconds to detect new run
# Note: CI fix uses existing LLM_IMPLEMENTATION_TIMEOUT_SECONDS (3600s) - see Decision 9
