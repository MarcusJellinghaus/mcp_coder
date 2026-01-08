# Decisions Log: Issue #254

Decisions made during plan review discussion.

---

## Decision 1: Path Matching Behavior

**Question:** How should `ignore_files` match filenames from git status?

**Options:**
- A: Exact path match (simpler, sufficient for `uv.lock` at root)
- B: Basename match (more robust, matches `uv.lock` in any directory)

**Decision:** A - Exact path match

**Rationale:** Simpler implementation, sufficient for the current use case where `uv.lock` is created at the repo root by `uv sync`.

---

## Decision 2: Step Structure

**Question:** Keep two separate steps (strict TDD) or combine into one?

**Options:**
- A: Keep two steps (strict TDD, separate commits)
- B: Combine into one step (simpler, single commit)

**Decision:** B - Combine into one step

**Rationale:** The change is small enough that a single step is sufficient.

---

## Decision 3: Additional Test Case

**Question:** Add a 5th test for `ignore_files=[]` (empty list)?

**Options:**
- A: Yes, add the test (5 tests total)
- B: No, 4 tests is sufficient

**Decision:** A - Yes, add the test

**Rationale:** Ensures backward compatibility when empty list is passed.

---

## Decision 4: Constant for "uv.lock"

**Question:** Create a constant for `"uv.lock"` used in 4 call sites?

**Options:**
- A: Yes, add constant (DRY, single source of truth)
- B: No, inline `["uv.lock"]` is fine

**Decision:** A - Yes, add constant

**Rationale:** DRY principle, single source of truth for build artifacts to ignore.

---

## Decision 5: Line Numbers in Plan

**Question:** Keep or remove approximate line numbers from the plan?

**Options:**
- A: Keep them (helpful hints, even if approximate)
- B: Remove them (function names are specific enough)

**Decision:** A - Keep them

**Rationale:** Helpful hints for locating code, even if they drift slightly.
