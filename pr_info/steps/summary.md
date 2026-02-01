# Stream Logging Enhancement - Implementation Summary

## Overview

This PR enhances the Claude CLI integration with stream-json output logging for better debugging and monitoring capabilities.

## Completed Work (Step 0)

- Switched Claude CLI from `--output-format json` to `--output-format stream-json`
- Added NDJSON stream logging to `logs/claude-sessions/` directory
- Implemented stream parsing functions (`parse_stream_json_line/file/string`)
- Added `branch_name` parameter to CLI functions for log file context
- Added cost/usage tracking from stream result messages
- Created integration tests for stream functionality

## Remaining Steps

### Step 1: Refactor Test File (Required for CI)

Split `tests/llm/providers/claude/test_claude_code_cli.py` (826 lines) into multiple files to comply with the 750-line limit.

### Step 2: Add Branch Name to All LLM Call Sites

Update all 13 LLM call sites across 6 files to pass `branch_name` parameter for better log file correlation.

## Files Modified (Step 0)

- `src/mcp_coder/llm/interface.py`
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- `src/mcp_coder/llm/providers/claude/claude_code_interface.py`
- `tests/llm/providers/claude/test_claude_cli_stream_integration.py` (new)
- `tests/llm/providers/claude/test_claude_code_cli.py`
- `tests/llm/providers/claude/test_claude_code_interface.py`
- `tests/llm/providers/claude/test_llm_sessions.py`
- `tests/llm/test_interface.py`
- `tests/unit/llm/providers/claude/test_claude_mcp_config.py`

## Files to Modify (Steps 1-2)

### Step 1
- `tests/llm/providers/claude/test_claude_code_cli.py` (split)
- `tests/llm/providers/claude/test_claude_cli_stream_parsing.py` (new)
- `tests/llm/providers/claude/test_claude_cli_wrappers.py` (new)

### Step 2
- `src/mcp_coder/utils/git_utils.py` (new utility function)
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/create_plan.py`
- `src/mcp_coder/workflows/create_pr/core.py`
- `src/mcp_coder/workflow_utils/commit_operations.py`
- `src/mcp_coder/cli/commands/prompt.py`
