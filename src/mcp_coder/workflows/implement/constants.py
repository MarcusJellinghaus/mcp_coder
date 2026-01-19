"""Constants for the implement workflow.

This module consolidates all constants used across the implement workflow modules
(core.py, task_processing.py, prerequisites.py) to ensure consistency and
single source of truth.
"""

# Directory paths
PR_INFO_DIR = "pr_info"
CONVERSATIONS_DIR = f"{PR_INFO_DIR}/.conversations"
COMMIT_MESSAGE_FILE = f"{PR_INFO_DIR}/.commit_message.txt"

# LLM timeout settings (in seconds)
LLM_IMPLEMENTATION_TIMEOUT_SECONDS = 3600  # 60 minutes
LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS = 600  # 10 minutes
LLM_FINALISATION_TIMEOUT_SECONDS = 600  # 10 minutes

# Mypy checking behavior
RUN_MYPY_AFTER_EACH_TASK = False  # If False, mypy runs once after all tasks complete
