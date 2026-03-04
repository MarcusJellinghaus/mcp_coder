# Implementation Decisions

This document records architectural and implementation decisions made during plan review.

## Decision 1: Pattern Matching Edge Case Handling

**Date:** 2026-03-04  
**Context:** What should happen if multiple log files match the pattern `*_{job_name}.txt`?

**Decision:** Take first match + log warning if multiple matches found (Option A + C)

**Rationale:**
- Simplest approach assumes GitHub provides one file per job (most common case)
- Warning provides visibility for debugging if multiple matches occur
- No over-engineering for edge case that may not happen in practice

**Implementation:**
- Take first match and break loop
- Before breaking, check if additional matches exist
- Log warning with list of all matching files if multiple found

---

## Decision 2: Add Test for Fallback Scenario

**Date:** 2026-03-04  
**Context:** Should we test that the old format fallback still works?

**Decision:** Yes - add test for old format fallback (Option A)

**Rationale:**
- Ensures backward compatibility is actually working
- Validates fallback logic isn't broken by pattern matching changes
- Low cost, high confidence in robustness

**Implementation:**
- Add new test: `test_build_ci_error_details_fallback_to_old_format()`
- Mock logs using old format: `{job_name}/{step_number}_{step_name}.txt`
- Verify logs still display correctly
- Add to Step 3 (test additions phase)

---

## Decision 3: Line Budget Handling for URLs

**Date:** 2026-03-04  
**Context:** Should we adjust line budget calculation for URL overhead (2-4 lines)?

**Decision:** No - trust existing truncation logic (Option B)

**Rationale:**
- URLs are only 2-4 lines, minimal overhead
- Existing truncation logic is robust and handles dynamic content
- Avoiding premature optimization
- Keep implementation simple

**Implementation:**
- No changes to line budget calculation
- Add URLs directly to output_lines
- Track lines_used as normal

---

## Decision 4: Update Logging Warning Message

**Date:** 2026-03-04  
**Context:** Should we update the warning in `get_failed_jobs_summary()` that references old filename format?

**Decision:** Yes - update warning to reflect pattern matching (Option A)

**Rationale:**
- Current warning shows misleading "Expected" filename in old format
- Updated warning aids debugging by showing actual pattern tried
- Improves troubleshooting experience

**Implementation:**
- Update warning at line ~305-310 in `get_failed_jobs_summary()`
- Change from: `"Expected: '{log_filename}'"`
- To: `"Tried pattern: '*_{job_name}.txt'"`
- Add to Step 4 (pattern matching implementation)

---

## Decision 5: Step Granularity

**Date:** 2026-03-04  
**Context:** Should Steps 5 and 6 be combined (both add URLs)?

**Decision:** Keep separate steps (Option A)

**Rationale:**
- Current granularity provides clarity
- Easier to verify each feature independently
- Step 5 focuses on happy path (URLs with logs)
- Step 6 focuses on error path (URLs without logs)
- Separate tests for each scenario

**Implementation:**
- No changes to step structure
- Maintain Step 5 and Step 6 as separate steps

---

## Decision 6: Architectural Decisions Documentation

**Date:** 2026-03-04  
**Context:** Are there pre-existing architectural decisions to review?

**Decision:** No separate decisions file exists yet

**Rationale:**
- This is the first decisions.md file for this feature
- All context is in summary.md and step files
- This document captures new decisions from plan review

**Implementation:**
- Create this decisions.md file
- Reference from summary.md if needed
