# Implementation Summary: CI Pipeline Check and Auto-Fix (#217)

## Overview

Add CI pipeline checking and automatic fix functionality to the `implement` command. After finalisation completes and code is pushed, the workflow will poll for CI completion, analyze any failures, and attempt automated fixes (max 3 attempts).

## Architectural Changes

### New Components

1. **CI Check Integration** (`src/mcp_coder/workflows/implement/core.py`)
   - `check_and_fix_ci()` - Main orchestration function for CI checking and fixing
   - `_extract_log_excerpt()` - Helper to truncate long logs (first 30 + last 170 lines)
   - `_get_failed_jobs_summary()` - Helper to extract failed job info from CI status

2. **New Constants** (`src/mcp_coder/workflows/implement/constants.py`)
   - `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300`
   - `CI_POLL_INTERVAL_SECONDS = 15`
   - `CI_MAX_POLL_ATTEMPTS = 50`
   - `CI_MAX_FIX_ATTEMPTS = 3`

3. **New Prompts** (`src/mcp_coder/prompts/prompts.md`)
   - "CI Failure Analysis Prompt" - Analyzes CI failure with log excerpts
   - "CI Fix Prompt" - Implements fixes based on problem description

### Integration Point

The CI check is called **once after finalisation** in `run_implement_workflow()`, between Step 5.5 (finalisation) and Step 6 (progress summary).

### Data Flow

```
Finalisation complete
        ↓
Poll for CI completion (15s interval, max 50 attempts)
        ↓
CI passed? → Done (exit 0)
        ↓ (failed)
For up to 3 attempts:
    ├── Get failed job logs
    ├── Extract log excerpt (≤200 lines)
    ├── LLM Analysis → problem description file + console log
    ├── LLM Fix → code changes
    ├── Run local checks (pylint, pytest, mypy)
    ├── Format, commit, push
    ├── Delete temp file
    └── Poll for new CI run
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

- `pr_info/.ci_problem_description.md` - Deleted before analysis, deleted after fix
- Added to `.gitignore` as safety net

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/workflows/implement/constants.py` | Modify | Add 4 CI-related constants |
| `src/mcp_coder/prompts/prompts.md` | Modify | Add 2 CI prompts |
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
3. **Log truncation**: First 30 + last 170 lines for logs > 200 lines (preserves setup errors and recent output)
4. **Multiple failures**: Detail first failed job only, mention others by name (keeps prompts focused)
5. **INFO logging**: All CI results logged at INFO level with `# TODO: change to DEBUG level` comments
