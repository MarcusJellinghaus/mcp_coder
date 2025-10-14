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
