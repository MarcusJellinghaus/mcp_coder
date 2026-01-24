# Implementation Decisions

This document records the decisions made during plan review discussion.

## Decision 1: Rebase Conflict Prediction
**Question**: How should we handle rebase conflict prediction accuracy issues with `git merge-tree`?
**Decision**: Skip conflict prediction entirely, just detect if rebase is needed (Option C)
**Rationale**: `git merge-tree` has 10-20% false positive rate and 5-10% false negative rate. Keeping it simple removes unreliable prediction component.

## Decision 2: Integration Testing Scope
**Question**: Should we add integration tests for `collect_branch_status()` workflow?
**Decision**: Keep it simple with unit tests and mocked dependencies only (Option A)
**Rationale**: Maintains fast test execution and reliable CI without additional complexity.

## Decision 3: Performance Caching Strategy
**Question**: Should we add caching for repeated branch status checks?
**Decision**: No additional caching, rely on existing utility caching (Option A)
**Rationale**: CIResultsManager already provides caching. Keep implementation simple and focused.

## Decision 4: Auto-Fix Scope
**Question**: How comprehensive should auto-fix capabilities be?
**Decision**: Only fix CI failures, keep it minimal and safe (Option A)
**Rationale**: Reduces complexity and risk by limiting auto-fixes to CI failures using existing `check_and_fix_ci()` logic.

## Decision 5: Error Handling Strategy
**Question**: How should we handle partial failures during status collection?
**Decision**: Always attempt full collection with clear "unavailable" indicators (Option C)
**Rationale**: Provides maximum information to users while clearly indicating what data is missing.

## Decision 6: LLM Output Truncation
**Question**: Should we apply truncation to all output components or just CI logs?
**Decision**: Only truncate CI logs, keep other status info complete (Option A)
**Rationale**: CI logs are the longest content. Other status information is important and relatively short.

## Impact Summary
These decisions simplify the implementation while maintaining all core functionality:
- Lower risk through simplified rebase detection
- Faster implementation with focused testing approach
- Easier maintenance with minimal caching and auto-fix scope
- Better user experience with comprehensive error handling