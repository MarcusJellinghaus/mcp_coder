# Implementation Decisions

This document tracks decisions made during the plan review discussion.

## 1. Event Fetching Error Handling
**Decision:** Treat event fetching failures as errors and stop processing.
**Rationale:** Ensures we don't miss API problems and maintains data integrity.
**Implementation:** Remove `@_handle_github_errors` decorator from `get_issue_events()` to let exceptions propagate naturally.

## 2. Debug Parameters
**Decision:** No `--issue` parameter for validating specific issues.
**Rationale:** KISS principle - keep the tool simple, use `--dry-run` for testing instead.

## 3. Ignore Labels Filtering Strategy
**Decision:** Skip issues that have ANY ignore label present.
**Rationale:** Conservative approach - if an issue is marked to ignore, skip it completely.
**Example:** Issue with both "Overview" and "status-01:created" will be skipped.

## 4. Label Lookups Data Structure
**Decision:** Use TypedDict for label lookups instead of plain tuple or dataclass.
**Rationale:** Consistent with existing codebase patterns using TypedDict, self-documenting field names.

## 5. Display Format
**Decision:** Use plain text format (no emojis or colored output).
**Rationale:** Simple, works everywhere (CI/CD, different terminals, log files).

## 6. Exit Code Priority
**Decision:** When both errors AND warnings exist, exit with code 1 (errors take precedence).
**Rationale:** More critical issues should determine the exit code.

## 7. EventData Type Structure
**Decision:** Keep single EventData TypedDict with `label: Optional[str]`.
**Rationale:** KISS - simpler to have one type for all events rather than multiple specialized types.

## 8. Time Calculation Helper Function
**Decision:** Extract time calculation into `calculate_elapsed_minutes()` helper function.
**Rationale:** More testable and reusable, centralizes datetime logic.

## 9. Progress Logging
**Decision:** No separate progress logging needed.
**Rationale:** Per-issue status logs already provide progress information.

## 10. API Call Count Logging
**Decision:** Log API call counts at DEBUG level only.
**Rationale:** Useful for debugging rate limit issues without cluttering INFO output.

## 11. Summary Statistics
**Decision:** No additional summary statistics logging beyond what `display_summary()` shows.
**Rationale:** Avoid redundancy - display_summary already shows all needed information.

## 12. Summary Display Format
**Decision:** Keep current format with totals first, then details (no overview section at top).
**Rationale:** Simpler, less redundant.

## 13. Step Organization
**Decision:** Keep current structure with code and related unit tests in the same step.
**Rationale:** Each step is self-contained with implementation and validation together.

## 14. Quick Reference Section in Summary
**Decision:** Do not add a "Quick Reference" section to summary.md.
**Rationale:** Current summary structure is sufficient for the plan's needs.

## 15. Event Type Filtering in get_issue_events()
**Decision:** Return ALL event types from GitHub API, but add optional `filter_by_type` parameter.
**Rationale:** Provides flexibility for future use while documenting that currently only label events are used.
**Implementation:** Add `filter_by_type: Optional[IssueEventType] = None` parameter with exact match filtering.

## 16. IssueEventType Enum Definition
**Decision:** Use Python Enum (str, Enum) for event types, include all ~22 GitHub event types (issue + PR events).
**Rationale:** Provides IDE autocomplete, type safety, and complete API coverage. Pythonic and maintainable.
**Implementation:** Define in `issue_manager.py` near top with TypedDicts, include PR-specific events for completeness.

## 17. Timestamp Handling Simplicity
**Decision:** Keep simple 'Z' suffix replacement only in `calculate_elapsed_minutes()`.
**Rationale:** GitHub API provides reliable, consistent timestamp format. No need for complex parsing.

## 18. API Error Documentation
**Decision:** Add explicit "Raises: GithubException" section to `check_stale_bot_process()` docstring with explanatory note.
**Rationale:** Makes it crystal clear this function intentionally propagates exceptions (per Decision #1), unlike other methods.

## 19. Timezone Format Testing
**Decision:** Do not add specific test for GitHub timestamp format verification.
**Rationale:** Trust GitHub API consistency - unnecessary test overhead.

## 20. Rate Limit Logging Threshold
**Decision:** Do not add INFO-level warning for high API call counts.
**Rationale:** DEBUG level logging of API call count is sufficient for monitoring.

## 21. Dry-Run Behavior Documentation
**Decision:** Do not add separate documentation section for dry-run behavior.
**Rationale:** Behavior is self-explanatory from code and argument help text.

## 22. Exception Handling in main()
**Decision:** Wrap `process_issues()` in try/except to catch GithubException, log error with traceback, and exit cleanly.
**Rationale:** Provides clear error message when API fails mid-processing, indicating validation was incomplete.

## 23. TypedDict for LabelLookups
**Decision:** Keep TypedDict for LabelLookups structure (confirmed).
**Rationale:** More maintainable and self-documenting than tuples or other alternatives.

## 24. Steps 2 and 3 Separation
**Decision:** Keep Steps 2 and 3 separate as originally planned.
**Rationale:** Better for incremental testing and implementation. Each step remains focused and manageable.

---

## Code Review Follow-up Decisions

### 25. Hardcoded Label Name Fallback
**Decision:** Remove fallback value in `process_issues()`, use direct dictionary access `id_to_name["created"]`.
**Rationale:** Fail fast with clear KeyError if "created" label is missing from config. No silent fallbacks that could hide configuration errors.
**Implementation:** Change `id_to_name.get("created", "status-01:created")` to `id_to_name["created"]`.

### 26. Temporary Test File Cleanup
**Decision:** Delete `test_multiple_labels_manual.py` from project root.
**Rationale:** Temporary manual testing file no longer needed - comprehensive automated tests exist in proper location.
**Action:** Remove file immediately.

### 27. Duplicate resolve_project_dir() Function
**Decision:** Remove duplicate implementation from `workflows/validate_labels.py`, import from `mcp_coder.workflows.utils`.
**Rationale:** Avoid code duplication - utility function already exists and is identical.
**Implementation:** 
- Remove lines ~430-480 from `workflows/validate_labels.py`
- Add import: `from mcp_coder.workflows.utils import resolve_project_dir`

### 28. Rate Limiting Feedback Visibility
**Decision:** Keep API call count logging at DEBUG level only.
**Rationale:** Users who need visibility can use `--log-level DEBUG`. Script doesn't make excessive calls in typical use.
**Action:** No change needed - current implementation is correct.

### 29. Test Results Documentation
**Decision:** Delete `pr_info/test_results_multiple_labels.md` immediately.
**Rationale:** File served its purpose for PR verification documentation but is no longer needed.
**Action:** Remove file now.

### 30. Type Hints in Test Functions
**Decision:** Fix all `tmp_path: Any` type hints to `tmp_path: Path` in test file.
**Rationale:** Improve type safety and enable better mypy checking. Simple find-replace operation.
**Implementation:** Update all test function signatures in `tests/workflows/test_validate_labels.py`.

### 31. Time Tolerance Magic Numbers
**Decision:** Keep inline time tolerance assertions as-is with comments.
**Rationale:** Inline assertions with comments are clear and readable. Extracting to constant wouldn't add value.
**Action:** No change needed - current implementation is optimal.

### 32. Batch File UTF-8 Comments
**Decision:** Add specific comment about Unicode label name support.
**Rationale:** Make it clear why UTF-8 setup is needed (for label names with emoji/special characters).
**Implementation:** Update comment in `workflows/validate_labels.bat` near UTF-8 setup section.

### 33. Version Flag for Script
**Decision:** Do not add `--version` flag to script.
**Rationale:** Internal workflow script tracked by git history. Version flag adds maintenance overhead without sufficient benefit.
**Action:** No change needed.
