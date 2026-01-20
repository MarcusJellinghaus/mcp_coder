# Implementation Summary: CI Pipeline Check and Auto-Fix (#217)

## Overview

Add CI pipeline checking and automatic fix functionality to the `implement` command. After finalisation completes and code is pushed, the workflow will poll for CI completion, analyze any failures, and attempt automated fixes (max 3 attempts).

## Key Decisions

See `Decisions.md` for full details on architectural decisions made during plan review.

## Architectural Changes

### New Components

1. **CIResultsManager Enhancement** (`src/mcp_coder/utils/github_operations/ci_results_manager.py`)
   - Add explicit `StepData` and `JobData` TypedDicts for full type safety (Decision 15, 21)
   - Update `CIStatusData.jobs` from `List[Dict[str, Any]]` to `List[JobData]`
   - Add step-level data to job info: `steps: [{number, name, conclusion}]`
   - Enables precise identification of failed step and correct log file

2. **Git Helper Function** (`src/mcp_coder/utils/git_operations/commits.py`)
   - Add `get_latest_commit_sha()` for debug logging (Decision 19)

3. **CI Check Integration** (`src/mcp_coder/workflows/implement/core.py`)
   - `check_and_fix_ci()` - Main orchestration function for CI checking and fixing
   - `_extract_log_excerpt()` - Helper to truncate long logs (first 30 + last 170 lines)
   - `_get_failed_jobs_summary()` - Helper to extract failed job info from CI status

4. **New Constants** (`src/mcp_coder/workflows/implement/constants.py`)
   - `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300`
   - `CI_POLL_INTERVAL_SECONDS = 15`
   - `CI_MAX_POLL_ATTEMPTS = 50`
   - `CI_MAX_FIX_ATTEMPTS = 3`
   - `CI_NEW_RUN_POLL_INTERVAL_SECONDS = 5`
   - `CI_NEW_RUN_MAX_POLL_ATTEMPTS = 6`
   - Note: CI fix reuses `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` (Decision 9) - so 6 new constants total

5. **Prompt Substitution Helper** (`src/mcp_coder/prompt_manager.py`)
   - Add `get_prompt_with_substitutions()` helper function (Decision 22)
   - Standardizes `[placeholder]` substitution pattern for CI prompts

6. **New Prompts** (`src/mcp_coder/prompts/prompts.md`)
   - "CI Failure Analysis Prompt" - Analyzes CI failure with log excerpts
   - "CI Fix Prompt" - Implements fixes based on problem description

### Integration Point

The CI check is called **once after finalisation** in `run_implement_workflow()` as Step 5.6, between Step 5.5 (finalisation) and Step 6 (progress summary).

### Data Flow

```
Finalisation complete
        ↓
Log local commit SHA (debug)
        ↓
Poll for CI completion:
  - Get latest CI run on branch
  - If not completed → wait 15s, retry (max 50 attempts)
  - If completed → check conclusion
        ↓
Log CI run commit SHA (debug)
        ↓
CI passed? → log CI_PASSED, Done (exit 0)
        ↓ (failed)
For up to 3 attempts:
    ├── Get failed job info (including step-level data)
    ├── Get logs, extract excerpt (≤200 lines)
    ├── LLM Analysis → writes to temp file
    ├── Read temp file, delete it, log content to console
    ├── LLM Fix (with analysis content in prompt) → code changes + quality checks
    ├── Format, commit, push (fail fast on git errors)
    └── Poll for new CI run:
      - 6 attempts at 5s intervals (30s max) to detect new run ID
      - If no new run → log warning, exit gracefully (exit 0)
      - If new run found → wait for completion
        ↓
Max attempts exhausted → exit 1
```

### Exit Codes and Logging (Decision 14)

| Scenario | Exit Code | Log Message |
|----------|-----------|-------------|
| CI passes (first check or after fix) | 0 | `CI_PASSED: Pipeline succeeded` |
| API errors (graceful) | 0 | `CI_API_ERROR: Could not retrieve CI status - skipping` |
| No CI configured | 0 | `CI_NOT_CONFIGURED: No workflow runs found - skipping` |
| CI timeout (no run found) | 0 | `CI_TIMEOUT: No completed run after polling - skipping` |
| Git errors during fix (fail fast) | 1 | Error message |
| Max fix attempts exhausted | 1 | Error message |

### Temporary Files

- `pr_info/.ci_problem_description.md` - Written by analysis, read and deleted before fix
- Added to `.gitignore` as safety net against crashes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/utils/github_operations/ci_results_manager.py` | Modify | Add step-level data to jobs |
| `tests/utils/github_operations/test_ci_results_manager_*.py` | Modify | Add tests for step data |
| `src/mcp_coder/utils/git_operations/commits.py` | Modify | Add `get_latest_commit_sha()` helper |
| `tests/utils/git_operations/test_commits.py` | Modify | Add tests for new helper |
| `src/mcp_coder/workflows/implement/constants.py` | Modify | Add 6 CI-related constants |
| `src/mcp_coder/prompts/prompts.md` | Modify | Add 2 CI prompts with placeholders |
| `.gitignore` | Modify | Add temp file exclusion |
| `src/mcp_coder/workflows/implement/core.py` | Modify | Add CI check function + workflow integration |
| `tests/workflows/implement/test_ci_check.py` | Create | Unit tests for CI check functions (no integration tests per Decision 12) |

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
10. **Exact filename matching**: Log filename format is `{job_name}/{step_number}_{step_name}.txt` (verified against existing tests). Lookup uses exact match only, warns with expected/found filenames on mismatch (Decision 10, 16)
11. **3-level commit fallback**: CI fix commits use file → LLM → default fallback (Decision 13)
12. **Distinct log prefixes**: Exit 0 scenarios have searchable prefixes (Decision 14)
13. **Run ID comparison**: After push, compare run IDs to detect if new CI run triggered (Decision 17)
