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


