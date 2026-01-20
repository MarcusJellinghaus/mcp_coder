# Implementation Summary: CI Pipeline Check and Auto-Fix (#217)

## Overview

Add CI pipeline checking and automatic fix functionality to the `implement` command. After finalisation completes and code is pushed, the workflow will poll for CI completion, analyze any failures, and attempt automated fixes (max 3 attempts).

## Key Decisions

See `Decisions.md` for full details on architectural decisions made during plan review.

## Architectural Changes

### New Components

1. **CIResultsManager Enhancement** (`src/mcp_coder/utils/github_operations/ci_results_manager.py`)
   - Add step-level data to job info: `steps: [{number, name, conclusion}]`
   - Enables precise identification of failed step and correct log file

2. **CI Check Integration** (`src/mcp_coder/workflows/implement/core.py`)
   - `check_and_fix_ci()` - Main orchestration function for CI checking and fixing
   - `_extract_log_excerpt()` - Helper to truncate long logs (first 30 + last 170 lines)
   - `_get_failed_jobs_summary()` - Helper to extract failed job info from CI status

3. **New Constants** (`src/mcp_coder/workflows/implement/constants.py`)
   - `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300`
   - `LLM_CI_FIX_TIMEOUT_SECONDS = 600`
   - `CI_POLL_INTERVAL_SECONDS = 15`
   - `CI_MAX_POLL_ATTEMPTS = 50`
   - `CI_MAX_FIX_ATTEMPTS = 3`

4. **New Prompts** (`src/mcp_coder/prompts/prompts.md`)
   - "CI Failure Analysis Prompt" - Analyzes CI failure with log excerpts
   - "CI Fix Prompt" - Implements fixes based on problem description

### Integration Point

The CI check is called **once after finalisation** in `run_implement_workflow()`, between Step 5.5 (finalisation) and Step 6 (progress summary).

### Data Flow

```
Finalisation complete
        ↓
Log local commit SHA (debug)
        ↓
Poll for CI completion (15s interval, max 50 attempts)
        ↓
Log CI run commit SHA (debug)
        ↓
CI passed? → Done (exit 0)
        ↓ (failed)
For up to 3 attempts:
    ├── Get failed job info (including step-level data)
    ├── Identify failed step → construct log filename
    ├── Get logs, extract excerpt (≤200 lines)
    ├── LLM Analysis → writes to temp file
    ├── Read temp file, delete it, log content to console
    ├── LLM Fix (with analysis content in prompt) → code changes + quality checks
    ├── Format, commit, push
    └── Poll for new CI run (any completed run on branch)
        ↓
Max attempts exhausted → exit 1
```

### Exit Codes

| Scenario | Exit Code |
|----------|-----------|
| CI passes (first check or after fix) | 0 |
| API errors / no CI configured | 0 (with warning) |
| CI timeout (no run found) | 0 (with warning) |
| Max fix attempts exhausted | 1 |

### Temporary Files

- `pr_info/.ci_problem_description.md` - Written by analysis, read and deleted before fix
- Added to `.gitignore` as safety net against crashes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/utils/github_operations/ci_results_manager.py` | Modify | Add step-level data to jobs |
| `tests/utils/github_operations/test_ci_results_manager_*.py` | Modify | Add tests for step data |
| `src/mcp_coder/workflows/implement/constants.py` | Modify | Add 5 CI-related constants |
| `src/mcp_coder/prompts/prompts.md` | Modify | Add 2 CI prompts with placeholders |
| `.gitignore` | Modify | Add temp file exclusion |
| `src/mcp_coder/workflows/implement/core.py` | Modify | Add CI check function + workflow integration |
| `tests/workflows/implement/test_ci_check.py` | Create | Unit tests for CI check functions |

## Dependencies

- `CIResultsManager` from `src/mcp_coder/utils/github_operations/ci_results_manager.py` (prerequisite #213)
- Existing `ask_llm()` interface for LLM calls
- Existing quality check functions (`run_formatters`, `commit_changes`, `push_changes`)

## Design Decisions

1. **Single function approach**: One main `check_and_fix_ci()` function handles all orchestration
2. **Inline polling**: Simple loop, no separate polling abstraction needed
3. **No SHA validation**: Poll for any completed CI run on branch (simplifies implementation)
4. **Step-level data**: CIResultsManager provides step info to identify exact failure location
5. **Log truncation**: First 30 + last 170 lines for logs > 200 lines (preserves setup errors and recent output)
6. **Two-phase LLM**: Separate analysis and fix calls, with temp file read/deleted between them
7. **Quality checks in prompt**: LLM runs pylint/pytest/mypy as part of fix prompt (consistent with existing pattern)
8. **Multiple failures**: Detail first failed job only, mention others by name (keeps prompts focused)
9. **SHA debug logging**: Log local commit SHA and CI run SHA at INFO level for debugging
