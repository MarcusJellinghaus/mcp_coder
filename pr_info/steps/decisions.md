# Implementation Decisions

This document records the decisions made during the project plan review discussion.

---

## Decision 1: Configuration Helper Simplification

**Topic:** Should `_get_jenkins_config()` return all 4 values including `test_job`, or only the 3 required values?

**Decision:** Return only 3 required values (server_url, username, api_token)

**Rationale:**
- Cleaner separation between client config and test-only config
- Simpler function with focused purpose
- Test fixture can handle test_job separately (just 2-3 lines)

**Impact:**
- Step 2: Update `_get_jenkins_config()` to return dict with 3 keys only
- Step 3: Integration test fixture reads test_job separately

---

## Decision 2: Integration Test Skip Messages

**Topic:** Should skip messages be detailed (~40 lines) or simplified?

**Decision:** Use shorter, simpler skip messages

**Rationale:**
- Keeps fixture code concise (~10-15 lines instead of ~40)
- Still provides necessary information
- Easier to maintain

**Impact:**
- Step 3: Simplify skip messages in `jenkins_test_setup` fixture

---

## Decision 3: Error Handling Strategy

**Topic:** How should we distinguish between different Jenkins error types?

**Decision:** Keep it simple - wrap all JenkinsException as JenkinsError

**Rationale:**
- Follows KISS principle
- Simplest possible implementation
- Avoids fragile error message parsing or status code inspection
- Forward-compatible with library changes

**Impact:**
- Step 2: Simplify error handling in client.py

---

## Decision 4: Exception Types

**Topic:** Should we keep specific exception types or use only one?

**Decision:** Use only one exception class `JenkinsError`

**Rationale:**
- Maximum simplicity
- Follows YAGNI principle (don't define unused types)
- Can add specific exceptions later if truly needed

**Impact:**
- Step 1: Remove specific exception types from models
- Step 2: Define only `JenkinsError` in client.py
- Step 4: Export only `JenkinsError`
- All steps: Update test expectations

---

## Decision 5: Job Status Edge Cases

**Topic:** How should we handle edge cases like expired/cancelled queue items?

**Decision:** Pass through status strings as-is from Jenkins

**Rationale:**
- Simple implementation
- Forward-compatible with new Jenkins statuses
- No validation needed
- Users get exactly what Jenkins provides

**Impact:**
- Step 2: No status validation in `get_job_status()`

---

## Decision 6: Timeout Configuration

**Topic:** Should timeout be configurable or fixed?

**Decision:** Fixed at 30 seconds

**Rationale:**
- Simplest approach - no configuration needed
- 30 seconds is reasonable for most Jenkins operations
- Reduces configuration complexity

**Impact:**
- Step 2: Hard-code timeout=30 in Jenkins() client initialization
- No config file or environment variable for timeout

---

## Decision 7: Integration Test Reliability

**Topic:** Should integration tests retry on transient failures?

**Decision:** No retry logic - let tests fail if Jenkins has issues

**Rationale:**
- Simplest implementation
- Failures clearly indicate real problems
- No hidden flakiness

**Impact:**
- Step 3: No retry logic in integration tests

---

## Decision 8: Known Limitations Documentation

**Topic:** Where should we document known limitations?

**Decision:** Document limitations in code docstrings only

**Rationale:**
- Keeps Step 5 focused on validation
- Limitations are close to the code they describe
- Simpler step structure

**Impact:**
- Step 2: Add limitations to class/function docstrings
- Step 5: No separate "Known Limitations" section

---

## Decision 9: Thread Safety Documentation

**Topic:** Should we document thread safety for JenkinsClient?

**Decision:** Don't document thread safety

**Rationale:**
- Keeps documentation simpler
- Not a critical concern for typical usage

**Impact:**
- Step 2: No thread safety notes in docstrings

---

## Decision 10: Architecture Decision Record

**Topic:** Should we create a separate ADR document?

**Decision:** Keep decisions in summary.md (no separate ADR file)

**Rationale:**
- Avoids duplication
- Decisions already well-documented in summary.md
- Simpler structure

**Impact:**
- No new ADR file created
- summary.md remains the source of truth for decisions

---

## Decision 11: Jenkins Version Compatibility (SUPERSEDED)

**Topic:** Should we document which Jenkins version was tested?

**Decision:** SUPERSEDED by Decision 14 - Do not document Jenkins version

**Rationale:**
- Original decision replaced during review discussion
- See Decision 14 for current approach

**Impact:**
- This decision is no longer active


---

## Decision 12: Exception Types Consistency (Review Discussion)

**Topic:** Resolve inconsistency between Decision 4 (single exception) and Steps 2/5 (multiple exceptions)

**Decision:** Stick with single `JenkinsError` exception only

**Rationale:**
- Maintains consistency with Decision 4
- Follows KISS principle
- Simpler implementation and testing
- Error messages provide sufficient context

**Impact:**
- Step 2: Remove references to JenkinsConnectionError, JenkinsAuthError, JenkinsJobNotFoundError
- Step 4: Export only `JenkinsError`
- Step 5: Update requirements checklist to reflect single exception

---

## Decision 13: Test Specification Detail Level (Review Discussion)

**Topic:** Should test specifications be simplified to high-level coverage only?

**Decision:** Keep current detailed test specifications

**Rationale:**
- Provides comprehensive implementation guidance
- Reduces ambiguity during implementation
- Ensures thorough test coverage

**Impact:**
- No changes to Steps 1-3 test specifications

---

## Decision 14: Jenkins Version Documentation (Review Discussion)

**Topic:** Should we document which Jenkins version was tested?

**Decision:** Do not document Jenkins version at all

**Rationale:**
- Keeps documentation simpler
- Avoids maintenance burden of version updates
- Works with modern Jenkins versions generically

**Impact:**
- Step 2: Remove "Tested with Jenkins X.Y.Z" note from module docstring
- Remove Decision 11 (superseded by this decision)

---

## Decision 15: Queue Item Expiration Handling (Review Discussion)

**Topic:** How should we handle expired/purged queue items?

**Decision:** Let it fail naturally - Jenkins API will error, wrap as JenkinsError

**Rationale:**
- Simplest approach (KISS principle)
- No special handling needed
- Jenkins error message provides context
- Forward-compatible

**Impact:**
- Step 2: No special handling for expired queue items in `get_job_status()`

---

## Decision 16: Build Number Availability (Review Discussion)

**Topic:** What if a queued job fails before getting a build number?

**Decision:** Pass through whatever Jenkins provides - build_number stays None if unavailable

**Rationale:**
- Aligns with Decision 5 (pass through as-is)
- Simple implementation
- No validation needed
- Handles edge cases gracefully

**Impact:**
- Step 2: No special error handling for missing build numbers

---

## Decision 17: Exception Chaining (Review Discussion)

**Topic:** Should JenkinsError preserve the original exception?

**Decision:** Yes - use `raise JenkinsError("message") from original_exception`

**Rationale:**
- Python best practice
- Preserves full stack trace for debugging
- Helpful for troubleshooting
- No additional complexity

**Impact:**
- Step 2: Use exception chaining with `from` syntax in all error handling

---

## Decision 18: Rate Limiting (Review Discussion)

**Topic:** Should we document or handle Jenkins API rate limiting?

**Decision:** No rate limiting handling or documentation

**Rationale:**
- Let Jenkins API errors surface naturally (KISS principle)
- Simplest implementation
- Users can handle rate limiting at their level if needed

**Impact:**
- No rate limiting documentation or handling anywhere

---

## Decision 19: Timeout Documentation Location (Review Discussion)

**Topic:** Where should the 30-second timeout be documented?

**Decision:** Document in JenkinsClient class docstring (not module docstring)

**Rationale:**
- More visible to users instantiating the class
- Keeps limitation close to where it matters

**Impact:**
- Step 2: Move timeout limitation from module docstring to class docstring

---

## Decision 20: Job Parameters Validation (Review Discussion)

**Topic:** Should we validate that params is a dict?

**Decision:** Yes - add explicit type validation

**Rationale:**
- Provides clear error message early
- Better user experience than cryptic Jenkins API error
- Simple validation (2 lines of code)

**Impact:**
- Step 2: Add type check in `start_job()`: raise ValueError if params is not None and not a dict

---

## Decision 21: Build Duration Availability (Review Discussion)

**Topic:** When is duration_ms available and what should be documented?

**Decision:** duration_ms is None until job completes - document in JobStatus docstring

**Rationale:**
- Clear behavior specification
- Helps users understand when to expect values
- Simple to implement and understand

**Impact:**
- Step 1: Add documentation in JobStatus docstring about duration_ms availability
- Step 2: Ensure duration_ms is None for running/queued jobs

---

## Decision 22: Job URL Source (Review Discussion)

**Topic:** Should job URL be constructed or obtained from Jenkins API?

**Decision:** Get URL from Jenkins API response only - don't construct it

**Rationale:**
- Single source of truth (Jenkins)
- Avoids URL construction errors
- Forward-compatible with Jenkins URL structure changes
- Simple implementation

**Impact:**
- Step 2: Extract URL from Jenkins API response (build_info) in `get_job_status()`

---

## Decision 23: Troubleshooting Documentation (Review Discussion)

**Topic:** Should we add a troubleshooting section?

**Decision:** No troubleshooting section - rely on clear error messages

**Rationale:**
- Keeps documentation minimal (KISS principle)
- Good error messages should be self-explanatory
- Reduces maintenance burden

**Impact:**
- No troubleshooting section added anywhere

---

## Decision 24: Quick Start Example (Review Discussion)

**Topic:** Should we add a Quick Start example to summary.md?

**Decision:** No separate Quick Start - examples in docstrings are sufficient

**Rationale:**
- Docstrings already contain usage examples
- Avoids duplication
- Simpler documentation structure

**Impact:**
- No Quick Start section added to summary.md

---

## Decision 25: Performance Considerations (Review Discussion)

**Topic:** Should we document performance considerations about polling?

**Decision:** No performance documentation about polling

**Rationale:**
- Trust users to handle polling appropriately (KISS principle)
- Avoids prescriptive guidance
- Users know their use cases best

**Impact:**
- No polling guidance in documentation

---

## Decision 26: File Size Estimates (Review Discussion)

**Topic:** Should we add KB size estimates in addition to line counts?

**Decision:** Line counts are sufficient - no KB size estimates needed

**Rationale:**
- Line counts adequate for planning
- File sizes vary with comments/whitespace
- Simpler documentation

**Impact:**
- No changes to existing line count estimates

---

## Decision 27: Rollback Plan (Review Discussion)

**Topic:** Should we document what to do if quality checks fail?

**Decision:** No rollback plan needed

**Rationale:**
- Fix-and-rerun process is self-evident
- Obvious procedure doesn't need documentation
- Keeps plan simpler

**Impact:**
- No rollback section added to Step 5

---

## Decision 28: Complexity Estimate Format (Review Discussion)

**Topic:** Should we update the specific line count estimates (450-550 vs 710-810)?

**Decision:** Remove specific line counts - just note "moderate complexity"

**Rationale:**
- Avoids over-precision in estimates
- More flexible
- Focuses on complexity level rather than exact numbers

**Impact:**
- Summary.md: Update "Estimated Complexity" section to remove specific line counts

---

## Decision 29: Scope Simplification (Review Discussion)

**Topic:** Should we simplify the implementation scope to reduce complexity?

**Decision:** Keep current scope as-is - no simplifications

**Rationale:**
- Current scope is appropriate for requirements
- Features are all valuable
- Already applied KISS principle in design decisions

**Impact:**
- No scope changes to any step
