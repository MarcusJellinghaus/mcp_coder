# Implementation Decisions

This document records key architectural and design decisions made during plan review discussions.

---

## Decision 1: Module Refactoring - Create Shared `llm_response_utils.py`

**Context:** The `strip_claude_footers()` function is used by both commit operations and PR creation workflows.

**Decision:** Move `strip_claude_footers()` to a new shared module `src/mcp_coder/workflow_utils/llm_response_utils.py`.

**Rationale:**
- Test structure should mirror source code structure
- Function is now shared between two modules (commits and PRs)
- Better separation of concerns
- Avoids cross-module imports from commit_operations to PR creation

**Impact:**
- **Create:** `src/mcp_coder/workflow_utils/llm_response_utils.py`
- **Create:** `tests/workflow_utils/test_llm_response_utils.py`
- **Move:** `strip_claude_footers()` function from `commit_operations.py` to new module
- **Move:** All `TestStripClaudeFooters` tests to new test file
- **Update imports in:**
  - `src/mcp_coder/workflow_utils/commit_operations.py`
  - `src/mcp_coder/workflows/create_pr/core.py`

**Date:** 2026-02-13

---

## Decision 2: PR Body Test Location

**Context:** Step 2 adds 5 new tests for PR body integration. Original plan placed them in `test_commit_operations.py`.

**Decision:** Add PR body integration tests to `tests/workflows/create_pr/test_parsing.py` instead.

**Rationale:**
- Test structure should mirror source code structure
- `parse_pr_summary()` is in `src/mcp_coder/workflows/create_pr/core.py`
- Tests for `parse_pr_summary()` already exist in `test_parsing.py`
- Better separation between workflow_utils tests and workflow tests

**Impact:**
- Step 2 tests go to `tests/workflows/create_pr/test_parsing.py`
- Tests will verify full `parse_pr_summary()` integration, not just `strip_claude_footers()` in isolation

**Date:** 2026-02-13

---

## Decision 3: Use Parameterized Tests

**Context:** Original plan proposed 13 individual test methods (8 in Step 1 + 5 in Step 2).

**Decision:** Use `@pytest.mark.parametrize` to reduce test count to ~8 tests total.

**Rationale:**
- Reduces code duplication
- Standard pytest best practice
- Easier to maintain and extend with new test cases
- Clearer test intent (groups related variations)

**Examples:**
- Combine case-insensitive variations into one parameterized test
- Combine model name variations (Opus, Sonnet) into one parameterized test
- Combine real-world pattern tests into one parameterized test

**Date:** 2026-02-13

---

## Decision 4: Pytest Execution with Integration Test Exclusions

**Context:** CLAUDE.md recommends excluding slow integration tests for regular development.

**Decision:** Step 3's full test suite run should use integration test exclusions.

**Command:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"]
)
```

**Rationale:**
- Faster feedback during development
- Follows CLAUDE.md requirements
- Integration tests require external resources (git repos, network, API tokens)
- Unit tests provide sufficient coverage for this feature

**Date:** 2026-02-13

---

## Decision 5: Regex Pattern Breadth

**Context:** Co-Authored-By regex pattern uses `.*` which is very permissive.

**Decision:** Keep the broad pattern `r'^Co-Authored-By:\s*Claude.*<noreply@anthropic\.com>$'`.

**Rationale:**
- Simple and future-proof for new model names
- Edge cases (weird content between "Claude" and email) are unlikely in footer context
- Pattern already specific enough (must start with Co-Authored-By and end with anthropic email)
- If issues arise, can tighten later

**Date:** 2026-02-13

---

## Decision 6: Add Docstring Update to Acceptance Criteria

**Context:** Enhanced `strip_claude_footers()` supports new features (case-insensitive, model variations, PR usage).

**Decision:** Add "Update docstring to reflect case-insensitive matching, model variations, and PR body usage" to Step 1 acceptance criteria.

**Rationale:**
- Docstring must match implementation
- Makes expectations explicit for implementer
- Ensures documentation stays current

**Date:** 2026-02-13

---

## Decision 7: Skip Separate decisions.txt File

**Context:** Should key decisions be documented in a separate file?

**Decision:** No separate decisions.txt file initially - summary.md is sufficient. (Note: This Decisions.md was created later based on discussion outcomes.)

**Rationale:**
- summary.md already documents the approach clearly
- Avoids duplication
- Can add decision documentation later if needed

**Date:** 2026-02-13
