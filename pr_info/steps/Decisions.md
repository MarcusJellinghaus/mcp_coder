# Decisions for CI Pipeline Check and Auto-Fix (#217)

This document records decisions made during plan review discussions.

## Decision 1: SHA Tracking After Fix Commits

**Question:** How to track commit SHA after pushing fixes (new commit has different SHA)?

**Decision:** Remove SHA validation entirely - just poll for any completed CI run on the branch.

**Rationale:** Simplifies the implementation significantly. No need to track or compare SHAs.

---

## Decision 2: Prompt Placeholder Substitution

**Question:** How to substitute placeholders like `[job_name]` in prompts?

**Decision:** Use prompts.md with `.replace()` or `.format()` for variable substitution at runtime.

**Rationale:** Keeps prompts in the standard location, consistent with other prompts in the project.

---

## Decision 3: Job-to-Log Matching (Step-Level Data)

**Question:** How to identify which log file contains the actual failure (e.g., `test/4_Run tests.txt`)?

**Decision:** Enhance `CIResultsManager.get_latest_ci_status()` to include step-level data for each job. This requires a new Step 0 in the implementation plan.

**Data structure addition:**
```python
jobs: [{
    id, name, status, conclusion, started_at, completed_at,
    steps: [{number, name, conclusion}]  # NEW
}]
```

**Rationale:** GitHub API provides step-level info. This allows precise identification of the failed step and construction of the correct log filename: `{job_name}/{step_number}_{step_name}.txt`

---

## Decision 4: Quality Checks in Fix Loop

**Question:** How to run pylint/pytest/mypy after LLM makes a fix?

**Decision:** Include quality check instructions in the CI Fix prompt - LLM runs checks itself.

**Rationale:** Consistent with existing pattern in `task_processing.py` where the LLM runs quality checks via MCP tools.

---

## Decision 5: Analysis and Fix as Separate LLM Calls

**Question:** Should analysis and fix be combined into one LLM call or kept separate?

**Decision:** Keep two separate calls with the following flow:
1. Analysis LLM → writes problem description to temp file
2. Python code: read temp file, delete file, log content to console, construct fix prompt with content inline
3. Fix LLM → receives analysis content directly in prompt

**Rationale:** Structured separation allows logging for debugging while cleaning up temp file immediately.

---

## Decision 6: Integration Test Complexity

**Question:** Integration tests in Step 4 mock 10 functions - too complex?

**Decision:** Simplify tests to only verify that `check_and_fix_ci()` is called with correct parameters. Trust the function's own unit tests for behavior.

**Rationale:** Reduces test fragility and maintenance burden.

---

## Decision 7: Temp File in .gitignore

**Question:** Should `pr_info/.ci_problem_description.md` be added to .gitignore?

**Decision:** Yes, add to .gitignore as a safety net.

**Rationale:** Protects against crashes or interrupts that might leave the temp file on disk.

---

## Decision 8: Debug SHA Logging

**Question:** Should we log CI run SHA and latest commit SHA for debugging?

**Decision:** Yes, add both SHAs to logging for debugging purposes.

**Implementation:**
- Log latest local commit SHA at INFO level when starting CI check
- Log CI run commit SHA at INFO level when CI status is retrieved
- Helps troubleshoot when CI runs don't match expected commits

---

## Decision 9: CI Fix Timeout

**Question:** Should we add a new `LLM_CI_FIX_TIMEOUT_SECONDS` constant or reuse existing?

**Decision:** Reuse existing `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` (3600s) for CI fixes.

**Rationale:** Consistent with original issue specification. Avoids redundant constants.

---

## Decision 10: Log Filename Matching Strategy

**Question:** How should we match step info to GitHub log filenames?

**Decision:** Use a helper function (`_get_failed_jobs_summary`) that constructs expected filename and does exact match only.

**Rationale:** Simpler implementation. If mismatches occur in practice, we can enhance with fuzzy matching later.

---

## Decision 11: Incomplete Test Stub

**Question:** What to do with the `test_analysis_writes_to_temp_file_then_deleted` stub?

**Decision:** Remove it from the plan. The behavior is implicitly tested by other tests.

---

## Decision 12: Integration Test Complexity

**Question:** How to handle the 9-mock integration test in Step 4?

**Decision:** Remove integration tests entirely. Trust unit tests for `check_and_fix_ci()` and manual verification of wiring.

**Rationale:** Reduces test fragility and maintenance burden.

---

## Decision 13: Commit Message Handling in CI Fix

**Question:** Should CI fix commits use the same fallback logic as finalisation?

**Decision:** Yes, use the same 3-level fallback: file → LLM generation → default message.

**Rationale:** Consistent behavior across the codebase.

---

## Decision 14: Distinguishing Exit 0 Scenarios in Logging

**Question:** How to distinguish different exit 0 scenarios (CI passed, API error, no CI, timeout)?

**Decision:** Use INFO level with distinct, searchable message prefixes:
- `CI_PASSED: Pipeline succeeded`
- `CI_NOT_CONFIGURED: No workflow runs found - skipping CI check`
- `CI_TIMEOUT: No completed run after polling - skipping CI check`
- `CI_API_ERROR: Could not retrieve CI status - skipping CI check`

**Rationale:** Makes it easier to grep logs for specific outcomes.

---

## Decision 15: Explicit TypedDicts for Step and Job Data

**Question:** Should step-level data use `Dict[str, Any]` with comments or explicit TypedDicts?

**Decision:** Add explicit `StepData` and `JobData` TypedDicts in `ci_results_manager.py` for full type safety.

**Rationale:** Provides mypy full type checking on step fields. Keeps all CI-related types together.

---

## Decision 16: Log Filename Format Debugging

**Question:** How to handle potential mismatches in GitHub log filename format?

**Decision:** 
1. Add a code comment documenting the assumed format: `{job_name}/{step_number}_{step_name}.txt`
2. When no matching log file is found, log a WARNING with both the expected filename AND the available filenames

**Rationale:** Allows debugging format mismatches without adding complexity. Can improve matching later if needed.

---

## Decision 17: Detect New CI Run After Push Using Run ID

**Question:** How to detect if a new CI run was triggered after pushing a fix?

**Decision:** 
1. Store the failed run's ID before pushing the fix
2. After push, poll for new run: 6 attempts at 5-second intervals (30 seconds total)
3. If new run ID found → proceed to poll for completion
4. If no new run after 30 seconds → log warning, exit gracefully (exit 0)

**Rationale:** Run IDs are monotonically increasing and simpler to compare than timestamps. The 30-second window gives GitHub time to trigger the new run without waiting too long.

---

## Decision 18: LLM Error Handling

**Question:** How should LLM errors (timeout, connection failure) during analysis or fix be handled?

**Decision:** Retry the LLM call once, then graceful exit 0 if still failing.

**Rationale:** Keeps the workflow from being blocked by transient LLM issues while giving it one more chance.

---

## Decision 19: Create get_latest_commit_sha Helper

**Question:** The plan references `get_latest_commit_sha` for debug logging, but it doesn't exist in the codebase.

**Decision:** Create `get_latest_commit_sha()` helper function in `commits.py` as part of Step 0.

**Rationale:** Reusable helper function. Runs `git rev-parse HEAD` to get current commit SHA.

---

## Decision 20: Branch Detection After Finalisation

**Question:** Should Step 4 check if `get_current_branch_name()` returns None after finalisation?

**Decision:** Remove the check. Trust that branch is always available after successful finalisation.

**Rationale:** Simplifies the code. After successful finalisation (which includes push), the branch will always be available.

---

## Decision 21: TypedDict Compatibility for JobData

**Question:** The current `CIStatusData.jobs` is `List[Dict[str, Any]]`. Adding `JobData` TypedDict with steps - is this a breaking change?

**Decision:** Update existing TypedDict to use `List[JobData]` for better type safety. This is a breaking change but acceptable since:
- The module is internal
- Better type safety outweighs compatibility concerns
- Mypy will catch any issues in dependent code

**Rationale:** Full type safety with explicit `JobData` and `StepData` TypedDicts is worth the minor breaking change.

---

## Decision 22: Prompt Substitution Helper Function

**Question:** How to substitute `[placeholder]` values in prompts loaded from prompts.md?

**Decision:** Create a new helper function `get_prompt_with_substitutions(source, header, substitutions: dict)` in `prompt_manager.py`.

**Implementation:**
```python
def get_prompt_with_substitutions(
    source: str, 
    header: str, 
    substitutions: Dict[str, str]
) -> str:
    """Get prompt and substitute [placeholder] values.
    
    Args:
        source: File path or string content
        header: Header name to search for
        substitutions: Dict mapping placeholder names to values
            e.g., {"job_name": "test", "step_name": "Run tests"}
    
    Returns:
        Prompt with all [placeholder] values replaced
    """
    prompt = get_prompt(source, header)
    for key, value in substitutions.items():
        prompt = prompt.replace(f"[{key}]", value)
    return prompt
```

**Rationale:** Standardizes placeholder substitution pattern. Keeps prompts in prompts.md consistent with other prompts.

---

## Decision 23: Branch Check with Defensive Error Logging

**Question:** Should Step 4 check if `get_current_branch_name()` returns None after finalisation?

**Decision:** Keep the branch check as a defensive measure, but log at ERROR level instead of WARNING.

**Update to Decision 20:** Decision 20 originally said to remove the check. After code review, we decided to keep it for defensive programming.

**Implementation:**
```python
if current_branch:
    ci_success = check_and_fix_ci(...)
else:
    logger.error("Could not determine current branch - skipping CI check")
```

**Rationale:** Defensive programming - while the branch should always be available after finalisation, logging at ERROR level ensures visibility if something unexpected occurs.

---

## Decision 24: Fix commit_sha Field Lookup

**Question:** The code uses `run_info.get("head_sha")` but the field is named `commit_sha` in CIResultsManager.

**Decision:** Fix the lookup to use `"commit_sha"` to match the actual field name in `CIStatusData`.

**Rationale:** Simple bug fix. The field name `commit_sha` is more descriptive than `head_sha`.

---

## Decision 25: Refactor _run_ci_analysis_and_fix into Smaller Functions

**Question:** The `_run_ci_analysis_and_fix` function has too many arguments and branches (requires pylint disables).

**Decision:** 
1. Extract into separate helpers: `_run_ci_analysis()` and `_run_ci_fix()`
2. Use a config dataclass to reduce argument count
3. Remove pylint disables after refactoring

**Rationale:** Improves readability, testability, and maintainability.

---

## Decision 26: Use List[JobData] Type Annotation

**Question:** `_get_failed_jobs_summary` uses `list[dict[str, Any]] | list[Any]` - should it use the TypedDict?

**Decision:** Update type annotation to use `List[JobData]` for better type safety.

**Rationale:** Leverages the existing TypedDict for full type checking.

---

## Decision 27: Add Short SHA to CI Log Messages

**Question:** Should CI status log messages include the commit SHA for debugging?

**Decision:** Add short SHA (7 characters) to all CI status log messages.

**Implementation:**
```python
logger.info(f"CI_PASSED: Pipeline succeeded (sha: {run_sha[:7]})")
```

**Rationale:** Improves debuggability while keeping messages concise.

---

## Decision 28: Handle Empty Temp File with Fallback

**Question:** What should happen if the temp problem description file exists but is empty?

**Decision:** 
1. Update `_read_problem_description` to use fallback when file content is empty
2. Add a test for this edge case

**Implementation:**
```python
if temp_file.exists():
    content = temp_file.read_text(encoding="utf-8").strip()
    temp_file.unlink()
    if content:  # Only use file content if not empty
        return content
    logger.debug("Temp file was empty, using fallback")
return fallback_response
```

**Rationale:** Ensures robust handling of edge cases.

---


