# Implementation Decisions

## Decisions Made During Plan Review

### 1. Architecture: Full Separation of Concerns (Pure Functions)
**Decision:** Apply separation of concerns with pure functions + I/O wrappers across all affected steps (Steps 2, 3, 4)

**Rationale:** Better testability, faster tests (no I/O), clearer code structure

**Discussed:** User requested "separation of concerns / pure function testing"

**Option chosen:** Full separation (Option A) for all steps

---

### 2. Function Naming: No Underscore Prefix
**Decision:** Pure functions will NOT use underscore prefix (e.g., `parse_cli_json_string` not `_parse_cli_json_string`)

**Rationale:** These functions will have unit tests, making them part of the tested API surface

**Discussed:** User confirmed "B if we write unit tests etc"

**Option chosen:** Option B (no underscore)

---

### 3. Session ID Handling: Optional Type
**Decision:** Make `session_id` field `str | None` in TypedDict, allow None values

**Rationale:** Most accurate representation - clearly indicates when session is unavailable, type-safe

**Discussed:** User selected Option C for Topic 2

**Implementation:**
- TypedDict: `session_id: str | None`
- Parsing returns None if not found (no "unknown" placeholder)
- Users must check for None before using

---

### 4. CLI JSON Format: Use Real Verified Structure
**Decision:** Use actual CLI output structure verified by testing

**Rationale:** User tested `claude --output-format json "test"` and provided real output

**Key findings:**
- Text field: `"result"` (not "text" or "content")
- Session ID field: `"session_id"` exists and is populated
- Cost tracking: `"total_cost_usd"` available
- Complete structure preserved in `raw_response`

**KISS principle applied:** No invented fallback fields, extract only `"result"` field as verified

---

### 5. CLI Parsing: Simple Field Extraction
**Decision:** Extract only verified fields, no invented fallbacks

**Rationale:** User feedback "Do not invent future problems, KISS !!!!"

**Implementation:**
```python
text = raw_response.get("result", "")
session_id = raw_response.get("session_id")
```

No fallback attempts for alternative field names.

---

### 6. API Implementation: Leverage Existing Code
**Decision:** Use existing `ask_claude_code_api_detailed_sync()` function instead of building from scratch

**Rationale:** Function already extracts session_id from SystemMessage, returns structured data

**Discussed:** User chose Option B (check existing code) for Topic 4

**Key findings:**
- Session ID available in `SystemMessage.session_id`
- Existing function returns: text, session_info, result_info, raw_messages
- Can simplify Step 4 implementation significantly

---

### 7. Delivery Approach: Single PR with All 9 Steps
**Decision:** Implement all 9 steps in one PR, commit after each step

**Rationale:** Complete feature delivery, easier to review as a cohesive unit

**Discussed:** User selected Option A for Topic 5

**Implementation flow:**
- Sequential implementation: Step 1 → Step 2 → ... → Step 9
- Commit after each step passes tests
- Final PR contains complete feature

---

### 8. Test Reduction: Focus on Essential Coverage
**Decision:** Reduce test verbosity by ~40% through pure function testing

**Impact:**
- Step 2: 16 tests → ~8 tests
- Step 3: 10+ tests → ~7 tests
- Overall: Faster implementation, same coverage

**Rationale:** Pure functions are easier to test, I/O wrappers need minimal tests

---

## Non-Decisions (Explicitly Not Made)

### Future Response Format Changes
**Not decided:** How to handle future CLI/API response structure changes

**Approach:** Store complete `raw_response`, allowing future parsing enhancements without breaking changes

**Rationale:** User emphasized "Keep the program flexible and extendible in the future"

### Cross-Method Session Compatibility
**Not decided:** Whether CLI and API sessions are interchangeable

**Approach:** Store `method` field, handle sessions independently per method

### Tool/MCP Call Handling
**Not decided:** How to handle additional fields from tool calls, MCP interactions

**Approach:** Raw storage captures everything automatically for future use

**User note:** "I think it will not be very comprehensive, since we might have tools and mcp tool calls, etc. But it is a first example"
