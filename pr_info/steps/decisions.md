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

## Decision 11: Jenkins Version Compatibility

**Topic:** Should we document which Jenkins version was tested?

**Decision:** Document tested Jenkins version in module docstring

**Rationale:**
- Provides clear compatibility information for users
- Helps with troubleshooting version-specific issues

**Impact:**
- Step 2: Add "Tested with Jenkins X.Y.Z" note to module docstring
- Step 5: Verify version note is present
