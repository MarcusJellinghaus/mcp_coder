"""Shared constants for workflow_steps.

Generic commit/CI tuning constants live here (the workflow-agnostic middle
tier), so steps can import them downward without reaching up into a specific
workflow package. `implement/constants.py` re-exports the ones its own
staying-in-`implement` code still uses.
"""

from __future__ import annotations

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
