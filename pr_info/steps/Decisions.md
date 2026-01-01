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

---

## Decision 9: Input Validation for `_split_repo_identifier()`
**Topic:** How to handle edge cases like multiple slashes or no slash in input  
**Decision:** Raise an exception for invalid input (no slash or multiple slashes)  
**Rationale:** In practice, `repo_full_name` always comes from `execute_coordinator_run()` in "owner/repo" format — invalid input indicates a bug

---

## Decision 10: Return Type of `_split_repo_identifier()`
**Topic:** Should owner be allowed to be None in the return type  
**Decision:** Return `tuple[str, str]` — both owner and repo always present  
**Rationale:** With validation raising exceptions for invalid input, owner is never None

---

## Decision 11: Mock Object Handling Test
**Topic:** Whether to add a test for Mock object handling of `repo_url`  
**Decision:** Not needed  
**Rationale:** We use `repo_full_name` directly now (always a string parameter), so Mock handling is irrelevant

---

## Decision 12: Documentation Placement
**Topic:** Where to place the terminology table  
**Decision:** Both module docstring AND comment near `_split_repo_identifier()`  
**Rationale:** Module docstring for overall context, function comment for discoverability

---

## Decision 13: Simplify `_get_cache_file_path()` Signature
**Topic:** Whether to remove the `owner` parameter from `_get_cache_file_path()`  
**Decision:** Yes — remove the `owner` parameter and fallback branches  
**Rationale:** Since `repo_full_name` always contains a slash now, the parameter and fallback logic are redundant

---

## Decision 14: Introduce `RepoIdentifier` Class
**Topic:** Whether to introduce a class instead of loose variables for repository identifiers  
**Decision:** Yes — create a `RepoIdentifier` dataclass with clear properties and factory methods  
**Rationale:** Prevents confusion between `repo_full_name`, `repo_name`, `owner`, `repo_url` by having a single source of truth

---

## Decision 15: Include `from_repo_url` Method
**Topic:** Whether `RepoIdentifier` should have a `from_repo_url` factory method  
**Decision:** Yes — include both `from_full_name` and `from_repo_url` methods  
**Rationale:** Single source of truth for all repository identifier parsing

---

## Decision 16: Location of `RepoIdentifier` Class
**Topic:** Where to place the `RepoIdentifier` class  
**Decision:** Add to `src/mcp_coder/utils/github_operations/github_utils.py`  
**Rationale:** Fits with GitHub-related utilities and can be reused across modules

---

## Decision 17: Adoption Scope for `RepoIdentifier`
**Topic:** How extensively to adopt the new class in this PR  
**Decision:** Full adoption — update all callers in `coordinator.py` to use `RepoIdentifier`  
**Rationale:** Consistent design throughout the module

---

## Decision 18: Error Handling for Invalid Input
**Topic:** Should `from_repo_url` raise an exception or return `None` on invalid URLs  
**Decision:** Raise `ValueError` (consistent with `from_full_name`, fail fast)  
**Rationale:** Consistent behavior across both factory methods

---

## Decision 19: Empty String Validation
**Topic:** Should we validate that both `owner` and `repo_name` are non-empty  
**Decision:** Yes — raise `ValueError` if either part is empty  
**Rationale:** Prevents invalid identifiers like `/repo` or `owner/`

---

## Decision 20: Step 1 Test Count Clarification
**Topic:** How to describe the number of tests in Step 1  
**Decision:** Change to "3 unit tests + 1 integration test"  
**Rationale:** Accurate count of the 4 test functions

---

## Decision 21: Minimal Documentation
**Topic:** How much documentation to add and where  
**Decision:** Minimal — only document `RepoIdentifier` class itself (class docstring + method docstrings), skip module docstring updates in `coordinator.py`  
**Rationale:** Reduces maintenance burden; the class is self-documenting

---

## Decision 22: Test Count Accuracy
**Topic:** Mismatch between summary.md ("3 unit tests") and step_1.md (5 test methods)  
**Decision:** Update summary.md to say "5 unit tests" for `TestRepoIdentifierFromFullName`  
**Rationale:** Accurate documentation

---

## Decision 23: Export RepoIdentifier from `__init__.py`
**Topic:** Whether to export `RepoIdentifier` from the package `__init__.py`  
**Decision:** Yes — export from `src/mcp_coder/utils/github_operations/__init__.py`  
**Rationale:** Cleaner imports, signals it's a public API

---

## Decision 24: Trailing Slash Test Coverage
**Topic:** Whether to add explicit test cases for URLs with trailing slashes  
**Decision:** Skip — current tests are sufficient  
**Rationale:** The regex is simple enough; trailing slash handling doesn't need explicit tests

---

## Decision 25: Dataclass Frozen Parameter
**Topic:** Whether to add `frozen=True` to the `RepoIdentifier` dataclass  
**Decision:** No — keep as regular dataclass  
**Rationale:** Simpler, more flexible

---

## Decision 26: Add `__str__` Method
**Topic:** Whether to add a `__str__` method to `RepoIdentifier`  
**Decision:** Yes — add `__str__` returning `self.full_name`  
**Rationale:** Cleaner logging syntax


## Decision 27: NameError Fix Strategy
**Topic:** How to fix potential NameError in exception handler when `repo_identifier` is not defined  
**Decision:** Initialize `repo_identifier` to `None` before the try block, then check for `None` in the exception handler  
**Rationale:** Clean approach that doesn't require nested try blocks or `dir()` checks

---

## Decision 28: Exception Handling Scope
**Topic:** Whether to keep narrowed exception types or revert to broad exception handling  
**Decision:** Revert to `except Exception` in all four locations  
**Rationale:** Safety - library exceptions from `requests`, `PyGithub`, and Jenkins client may not be caught otherwise, causing unhandled crashes

---

## Decision 29: Keep Default `__repr__`
**Topic:** Whether to add custom `__repr__` method to `RepoIdentifier`  
**Decision:** Keep the default dataclass `__repr__`  
**Rationale:** The default `RepoIdentifier(owner='...', repo_name='...')` format is already good for debugging

---

## Decision 30: Error Message Consistency
**Topic:** How to make error messages in `from_full_name()` consistent  
**Decision:** Include the invalid input in all error messages  
**Rationale:** Consistent format helps debugging; shows what was passed vs what was expected

---

## Decision 31: Remove Accidental Keyword-Only Marker
**Topic:** Whether to keep the `*,` added to `dispatch_workflow` signature  
**Decision:** Remove - it was an accidental/incidental change unrelated to this PR  
**Rationale:** Out of scope; no clear reason for the change
