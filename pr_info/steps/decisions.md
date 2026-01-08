# Decisions for Issue #259

Decisions made during plan review discussion.

## Decision 1: Test Style

**Question**: Should tests use mocks (consistent with existing) or real filesystem?

**Decision**: Use **mocks** - consistent with existing tests in `test_repository.py`.

## Decision 2: Existing Test Gap

**Question**: Existing tests don't mock `clean_profiler_output()`. Should we mock all helpers or leave some unmocked?

**Decision**: **Mock all helpers** - creates clean, consistent unit tests. Add `@patch` decorators for all four cleanup functions.

## Decision 3: Extract Helper Function

**Question**: Should we extract a reusable `delete_pr_info_subdirectory()` helper?

**Decision**: **No** - keep inline. KISS and YAGNI apply; only 2 use cases don't justify abstraction.

## Decision 4: Simplify Step 2 Pseudocode

**Question**: Should detailed pseudocode be replaced with "follow existing pattern" reference?

**Decision**: **No** - keep detailed pseudocode. Explicit guidance is better for LLM implementation.

## Decision 5: Acceptance Criteria Checkboxes

**Question**: Should acceptance criteria be marked `[x]` or `[ ]`?

**Decision**: **Unchecked `[ ]`** - work hasn't been done yet, checkboxes should reflect actual state.

## Decision 6: Remove DATA Section from Step 1

**Question**: Step 1 has a "DATA: Test Structure" section describing filesystem structure, but Decision #1 says to use mocks. Should we keep or remove it?

**Decision**: **Remove** - not needed for mock-based tests, and conflicts with the mock decision.

## Decision 7: Scope of Existing Test Updates

**Question**: Step 1 includes a note to update existing tests to mock `clean_profiler_output`. Should this be removed as out of scope for Issue #259?

**Decision**: **Keep** - include the test improvements in this PR.

## Decision 8: Number of Test Cases

**Question**: Should we have two test cases (happy path + no-op path) or simplify to one?

**Decision**: **One test case** - with mocks, we're testing that `cleanup_repository()` calls the deletion logic. The "exists vs doesn't exist" distinction isn't meaningful with mocks.

## Decision 9: Test Function Naming

**Question**: Should the test be named `test_cleanup_repository_deletes_conversations_directory` or something more accurate for mock-based testing?

**Decision**: **Rename** to `test_cleanup_repository_includes_conversations_cleanup` - more accurate for what the mock-based test verifies.

## Decision 10: Error Handling Pseudocode

**Question**: Should the error handling pseudocode in Step 2 be verified against `clean_profiler_output()` pattern?

**Decision**: **Keep as-is** - trust the implementer to follow existing patterns in the codebase.
