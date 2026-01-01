# Decisions Log

Decisions made during plan review discussion.

---

## Decision 1: Merge Steps 2 and 3
**Topic:** Step structure for implementation  
**Decision:** Merge Step 2 (replace parsing call) and Step 3 (delete function) into a single implementation step  
**Rationale:** These are tightly coupled — keeping them separate creates an unnecessary intermediate state

---

## Decision 2: Test Scope for Step 1
**Topic:** How many tests to add in Step 1  
**Decision:** Moderate scope — add 1-2 focused tests (bug fix verification + one edge case)  
**Rationale:** Existing test file already has comprehensive coverage; only need focused tests for the actual change

---

## Decision 3: Keep Step 4 Documentation Updates
**Topic:** Whether to keep, reduce, or remove documentation updates  
**Decision:** Keep as-is with full terminology table and docstring updates  

---

## Decision 4: Exception Handler Simplification
**Topic:** How to handle `_parse_repo_identifier()` call in exception handler  
**Decision:** Simplify to use `repo_full_name` directly for logging  
**Rationale:** More informative in logs, removes 6 lines of nested try/except, simpler code

---

## Decision 5: Line Number References
**Topic:** How to reference code locations in step files  
**Decision:** Reference by function/block name instead of line numbers  
**Rationale:** More maintainable as line numbers shift with code changes

---

## Decision 6: Extract String Split to Function
**Topic:** Whether to inline the string split logic or extract to a function  
**Decision:** Extract to a small `_split_repo_identifier()` function  
**Rationale:** Allows focused unit testing of the logic

---

## Decision 7: Test Organization
**Topic:** How to organize replacement tests  
**Decision:** Create new `TestSplitRepoIdentifier` class with 2-3 simple test methods  

---

## Decision 8: Old Test Cleanup
**Topic:** What to do with tests for removed functionality  
**Decision:** Delete `TestParseRepoIdentifier` class and `test_get_cached_eligible_issues_url_parsing_fallback`  
**Rationale:** These test functionality that no longer exists
