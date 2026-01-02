# Decisions Log for Issue #156: Multi-Phase Task Tracker Support

This document records decisions made during the plan review discussion.

---

## Decision 1: Algorithm Style

**Context:** The code change to handle phase headers could be written as a simple one-liner or as an explicit if/else with pass.

**Decision:** Keep explicit `if/else` with `pass` for clarity rather than `if "phase" not in header_text: break`.

**Reasoning:** Makes the intent more obvious to readers.

---

## Decision 2: Test Count

**Context:** Some tests in the plan had overlapping coverage (tests #1 and #4).

**Decision:** Keep all 5 tests for thoroughness.

**Reasoning:** Better to have comprehensive coverage.

---

## Decision 3: Architecture Simplification

**Context:** The original plan used keyword detection ("phase") to identify continuation headers. This raised questions about other patterns like "Sprint 2", "Part B", etc.

**Decision:** Use boundary-based extraction instead of keyword/header-level logic.

**New approach:**
1. Find "## Tasks" header → mark start
2. Find "## Pull Request" header → mark end (optional)
3. Return everything between them
4. If no "## Pull Request", return everything after "## Tasks"

**Reasoning:** 
- Much simpler to understand and maintain
- Robust to any structure within the Tasks section
- Handles missing Pull Request section gracefully
- Hierarchy parsing is handled separately by `_parse_task_lines()`, not affected by this change

---

## Decision 4: Debug Logging

**Context:** Suggested adding debug logging to help troubleshoot parsing issues.

**Decision:** Add informative debug logging when finding the section.

**Format:**
```
DEBUG - Found Tasks section between '## Tasks' and '## Pull Request', lines 15 to 42 (27 lines)
```

---

## Decision 5: LLM Prompt Clarification

**Context:** Step 1 states tests should "FAIL initially" (TDD), but `test_backward_compatibility_single_phase` will pass immediately.

**Decision:** Clarify that only the new multi-phase tests will fail initially; the backward compatibility test will pass.

---

## Decision 6: Step 2 Edit Approach

**Context:** Should Step 2 show the complete new function or just a diff?

**Decision:** Show the complete new function with short reasoning explaining the simplified approach.

---

## Decision 7: Case Sensitivity

**Context:** The code uses `.lower()` for header matching.

**Decision:** Keep case-insensitive matching for end markers.

---

## Decision 8: Alternative End Markers

**Context:** Should we also stop at "PR Tasks", "Merge Request", etc.?

**Decision:** Only "pull request" is used in this project; keep it simple with just this one end marker.

---

## Decision 9: Test Cleanup Strategy

**Context:** Some tests may have overlapping coverage (e.g., test 4 duplicates test 1's purpose, test 5 may be covered by existing tests).

**Decision:** Keep all 5 tests initially, then add a Step 4 to evaluate and remove redundant tests after all tests pass successfully.

**Reasoning:** Start with full coverage, then clean up once everything works.

---

## Decision 10: Test Data Structures

**Context:** Should we use one test data file or multiple structures?

**Decision:** Keep both test data structures — the complex `multi_phase_tracker.md` file AND the simple inline test in test 4.

**Reasoning:** Ensures coverage of both realistic multi-phase trackers and minimal edge cases.

---

## Decision 11: Edge Case for Missing Phase 1

**Context:** Should we add a test for when `## Tasks` is immediately followed by `## Phase 2:` with no Phase 1?

**Decision:** No additional test needed — the existing tests cover this implicitly since the boundary-based extraction doesn't care about phase numbering.

---

## Decision 12: Remove Step 4 (Test Cleanup)

**Context:** Step 4 was dedicated to evaluating and removing redundant tests after implementation. The 5 tests each serve different purposes.

**Decision:** Remove Step 4 entirely — keep all 5 tests.

**Reasoning:** The time spent deciding what to remove exceeds the value of removing anything. Tests 1-3 are core functionality, Test 4 is a focused edge case, Test 5 documents backward compatibility.

---

## Decision 13: Add Test for Empty Tasks Section

**Context:** Edge case where Tasks section is immediately followed by Pull Request with no content between them.

**Decision:** Add a test for empty Tasks section to the existing `TestFindImplementationSection` class.

**Reasoning:** Ensures edge case is covered; belongs in `TestFindImplementationSection` since it tests that specific function, not multi-phase behavior.

---

## Decision 14: Convert Test Data File to Inline

**Context:** The plan created a separate file `tests/workflow_utils/test_data/multi_phase_tracker.md`. This could be inline instead.

**Decision:** Convert to inline — remove the file, use a string constant in tests. Keep both inline structures (realistic + minimal).

**Reasoning:** Test data co-located with test logic is easier to understand and maintain.

---

## Decision 15: Add Missing Import to Step 1

**Context:** Step 1's test code uses `TemporaryDirectory` but doesn't show the import.

**Decision:** Add the missing `from tempfile import TemporaryDirectory` import to Step 1 for complete, copy-paste-ready code.
