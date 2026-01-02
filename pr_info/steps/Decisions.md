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
