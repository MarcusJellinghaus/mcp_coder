# Implementation Decisions

This document logs decisions made during project plan review and discussion.

---

## Decision 1: Import Strategy (Question 1)

**Decision:** Allow both direct imports and public API imports, always using absolute paths starting with `mcp_coder`

**Context:** When asked about import style guidelines in Step 2

**Options Discussed:**
- A/C - Allow both styles with absolute paths (CHOSEN)
- B - Enforce one consistent style
- D - No guidelines

**Rationale:** 
- Prefer absolute paths over relative imports for clarity
- Both `from mcp_coder.llm.types import X` and `from mcp_coder.llm import X` are acceptable
- Avoid relative imports like `from .types import X`

**Impact:** Will be documented in summary.md as a guideline

---

## Decision 2: Backward Compatibility (Question 2)

**Decision:** No backward compatibility needed - safe to delete old import paths immediately

**Context:** When asked about external users importing from old paths

**Options Discussed:**
- A - No external users, safe to delete (CHOSEN)
- B - Add deprecation warnings
- C - Be cautious, add shims

**Rationale:** This is an internal project with no external users

**Impact:** No need for deprecation shims or migration period

---

## Decision 3: Test Data Organization (Question 3)

**Decision:** Create `conftest.py` only if shared fixtures are actually needed during implementation

**Context:** When asked about organizing test fixtures and test data

**Options Discussed:**
- A - Create conftest.py for shared fixtures, keep data inline (CHOSEN)
- B - Create both conftest.py and test_data/ folder
- C - Keep everything inline
- D - Don't specify now

**Additional Context:** Keep it simple - only add structure when necessary during Steps 8-10

**Impact:** Will add note to Steps 8-10 about creating conftest.py only if needed

---

## Decision 4: Performance Checks (Question 4)

**Decision:** Remove performance checks from the plan - can be added later if needed

**Context:** When asked about adding performance regression checks to Step 11

**Options Discussed:**
- A - Add pytest --durations check
- B - Keep informal, remove from plan (CHOSEN)
- C - Add comprehensive checks

**Rationale:** Performance checks can be added later if they become necessary

**Impact:** No performance-related verification in Step 11

---

## Decision 5: Documentation Updates (Question 5)

**Decision:** Only ARCHITECTURE.md and README.md need updating (already covered in plan)

**Context:** When asked about other documentation that might need updates

**Options Discussed:**
- A - Yes, API docs need updating
- B - Only ARCHITECTURE.md and README.md (CHOSEN)
- C - Add checklist to review

**Rationale:** Project doesn't have additional API documentation

**Impact:** No changes needed - already in plan

---

## Decision 6: Smoke Test Script (Question 6)

**Decision:** Don't add smoke test script - existing pytest suite is sufficient

**Context:** When asked about adding a manual smoke test script to Step 11

**Options Discussed:**
- A - Add smoke test script
- B - Pytest suite is sufficient (CHOSEN)
- C - Maybe later

**Rationale:** Comprehensive pytest suite already provides adequate verification

**Impact:** No smoke test script will be added

---

## Decision 7: Pre-flight Checklist (Question 7)

**Decision:** Assume pre-flight preparation is already done - don't add Step 0

**Context:** When asked about adding a pre-flight checklist before Step 1

**Options Discussed:**
- A - Add Step 0 with checklist
- B - Assume already done (CHOSEN)
- C - Add to summary.md

**Rationale:** Standard preparation (clean state, branch creation, etc.) is assumed

**Impact:** No Step 0 will be added

---

## Decision 8: Progress Tracking (Question 8)

**Decision:** Use existing TASK_TRACKER.md for progress tracking

**Context:** When asked about creating a separate progress.md file

**Options Discussed:**
- A - Create progress.md
- B - Use existing TASK_TRACKER.md (CHOSEN)
- C - No tracking needed

**Rationale:** TASK_TRACKER.md already serves this purpose

**Impact:** No additional progress tracking file needed

---

## Decision 9: Test Reorganization Steps (Question 9)

**Decision:** Keep Steps 8-10 separate (don't consolidate)

**Context:** When asked if test reorganization steps could be combined

**Options Discussed:**
- A - Keep separate: Step 8, 9, 10 (CHOSEN)
- B - Combine into 2 steps
- C - Combine into 1 step

**Rationale:** Safer and more granular approach for test reorganization

**Impact:** No changes to Steps 8-10 structure

---

## Decision 10: Business Logic Extraction Steps (Question 10)

**Decision:** Keep Steps 4-6 separate (don't consolidate)

**Context:** When asked if business logic extraction steps could be combined

**Options Discussed:**
- A - Keep separate: Step 4, 5, 6 (CHOSEN)
- B - Combine into 1 step
- C - Combine into 2 steps

**Rationale:** Safer and easier to debug with separate steps

**Impact:** No changes to Steps 4-6 structure

---

## Decision 11: Code Block Language Specifications (Question 11)

**Decision:** Keep code blocks as-is - no need to standardize language specifications

**Context:** When asked about specifying languages in code blocks (```python vs ```)

**Options Discussed:**
- A - Update all code blocks
- B - Fine as-is (CHOSEN)
- C - Fix only if issues arise

**Rationale:** Not worth the effort, current state is acceptable

**Impact:** No changes to code block formatting

---

## Decision 12: File Path Separators (Question 12)

**Decision:** Keep mix of forward slashes and backslashes - doesn't matter

**Context:** When asked about standardizing path separators in documentation

**Options Discussed:**
- A - Use forward slashes everywhere
- B - Use backslashes everywhere
- C - Keep the mix (CHOSEN)

**Rationale:** Path separator style doesn't affect functionality

**Impact:** No changes to path formatting

---

## Summary of Changes to Plan

Based on these decisions, only 2 updates needed:

1. **summary.md** - Add import guideline section
2. **Steps 8-10** - Add note about conftest.py only if needed

All other aspects of the plan remain unchanged.
