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
