# Implementation Decisions Log

## Overview
This document logs architectural and implementation decisions made during plan review discussion.

**Date:** 2026-02-12  
**Issue:** #219 - No linked branch found for issues with draft PRs  
**Context:** Plan review and refinement discussion

---

## Decisions Made

### Decision 1: GraphQL Query Pagination Limit
**Question:** How to handle the 100-item limit in timeline query?  
**Options Considered:**
- A) Keep 100 limit, no pagination
- B) Add pagination handling
- C) Add warning if limit hit

**Decision:** **Option A** - Keep 100 limit, no pagination  
**Rationale:** 
- Simplest approach
- Very unlikely to hit in practice (most issues have <10 cross-references)
- Document limitation in docstring
- Adds no complexity

---

### Decision 2: PR State Filtering Logic
**Question:** Should we include closed draft PRs in branch resolution?  
**Options Considered:**
- A) Include closed drafts (`state == "OPEN" or is_draft`)
- B) Only OPEN PRs (`state == "OPEN"`)
- C) Keep current logic with documentation

**Decision:** **Option B** - Only include OPEN PRs (draft or not)  
**Rationale:**
- Cleaner, simpler logic
- Closed PRs (draft or not) represent abandoned work
- If a draft PR is closed, the branch shouldn't be used for workflows
- More intuitive behavior

**Implementation Impact:**
- Change filtering from `if state == "OPEN" or is_draft` 
- To: `if state == "OPEN"`
- Update tests to match this logic

---

### Decision 3: Test File Structure
**Question:** How to structure the 8 test scenarios to minimize duplication?  
**Options Considered:**
- A) Keep 8 separate test functions (~350 lines)
- B) Heavy parametrization (~200-250 lines)
- C) Hybrid approach (~280 lines)

**Decision:** **Option C** - Hybrid approach  
**Rationale:**
- Parametrize very similar tests (e.g., single draft PR vs single open PR)
- Keep complex scenarios separate (primary path, multiple PRs, errors)
- Balance between DRY principle and test clarity
- Reduces duplication without sacrificing readability

**Implementation Impact:**
- Estimated test file size: ~280 lines (down from ~350)
- Use `@pytest.mark.parametrize` for similar scenarios
- Keep distinct test functions for complex cases

---

### Decision 4: Multiple PRs Warning Message Detail
**Question:** Should warning log include branch names or just PR numbers?  
**Options Considered:**
- A) PR numbers only
- B) PR numbers + branch names
- C) PR numbers + branch names + states

**Decision:** **Option A** - PR numbers only  
**Rationale:**
- Simpler implementation
- Sufficient for debugging (users can click PR links)
- Keeps log output concise
- No additional code complexity

**Implementation:**
```python
logger.warning(
    f"Issue #{issue_number}: multiple draft/open PRs found: "
    f"{pr_numbers}. Cannot determine branch unambiguously."
)
```

---

### Decision 5: Performance Monitoring
**Question:** Should we add performance timing logs?  
**Options Considered:**
- A) No performance monitoring
- B) Temporary timing during development
- C) Permanent debug-level timing logs

**Decision:** **Option A** - No performance monitoring  
**Rationale:**
- Keep implementation focused
- Existing decorators provide sufficient logging
- Performance isn't critical (async workflow dispatch)
- Trust the estimates (primary <100ms, fallback ~500ms)

---

### Decision 6: Error Logging Level
**Question:** Should "no branch found" be ERROR, WARNING, or INFO?  
**Options Considered:**
- A) ERROR level (current)
- B) WARNING level
- C) INFO level

**Decision:** **Option A** - Keep ERROR level  
**Rationale:**
- Issue cannot proceed with workflow - requires attention
- Makes it visible in monitoring/alerts
- Indicates action needed (add branch or create PR)
- Appropriate for workflow-blocking situations

---

### Decision 7: Error Message Wording
**Question:** Keep or change "Requirement: Issue must have..." line?  
**Options Considered:**
- A) Remove the line entirely
- B) Change to factual context
- C) Keep current wording

**Decision:** **Option C** - Keep current wording  
**Rationale:**
- Clear and helpful for operators
- Directly states what's needed
- Good for users unfamiliar with the system
- No change needed

---

### Decision 8: Architecture Decision Record (ADR)
**Question:** Create separate ADR document?  
**Options Considered:**
- A) No ADR - self-documenting code
- B) Create formal ADR in docs/architecture/adr/
- C) Use plan files as ADR

**Decision:** **Option A** - No separate ADR  
**Rationale:**
- Plan files and code comments provide sufficient context
- Small feature doesn't warrant formal ADR
- No extra documentation overhead
- Implementation is self-documenting

---

### Decision 9: Pre-Implementation Step 0
**Question:** Add formal preparation step before Step 1?  
**Options Considered:**
- A) No Step 0 - start with Step 1
- B) Add Step 0 as formal step
- C) Add checklist to Step 1

**Decision:** **Option A** - No Step 0  
**Rationale:**
- LLM prompts already reference necessary context
- Detailed step files guide implementation
- No need for formal preparation step
- Keep 4 steps as planned

---

### Decision 10: Integration Test with Real GitHub API
**Question:** Add integration test calling real GitHub API?  
**Options Considered:**
- A) No integration test - mocks sufficient
- B) Add to test_branch_resolution.py
- C) Add to existing integration test file

**Decision:** **Option A** - No integration test  
**Rationale:**
- Unit tests with mocks cover all logic
- Integration tests are slow and require tokens
- Existing codebase integration tests catch API changes
- GraphQL query syntax is straightforward

---

### Decision 11: Explicit Rollback Testing
**Question:** Add formal rollback verification to Step 4?  
**Options Considered:**
- A) No rollback testing - trust analysis
- B) Add rollback verification steps
- C) Document procedure only

**Decision:** **Option A** - No rollback testing  
**Rationale:**
- Changes are additive and low-risk
- Existing tests verify no breaking changes
- Not necessary for this small change
- Would add ~10 minutes without significant value

---

## Summary of Implementation Impacts

### Code Changes
1. **PR filtering logic**: Use `state == "OPEN"` only (simpler)
2. **Test structure**: Hybrid with parametrization (~280 lines vs ~350)

### No Changes Required
- GraphQL pagination: Keep 100 limit
- Warning messages: PR numbers only
- Performance monitoring: None added
- Logging levels: Keep as planned
- Error messages: Keep current wording
- Documentation: No ADR needed
- Test scope: Unit tests only, no integration tests
- Process: Keep 4 steps, no Step 0, no rollback testing

### Plan File Updates Needed
1. **step_2.md**: Update PR filtering logic documentation
2. **step_1.md**: Note hybrid test structure with parametrization
3. **summary.md**: Update test file size estimate (280 lines)

---

**Plan Status:** Reviewed and refined ✅  
**Ready for Implementation:** Yes ✅
