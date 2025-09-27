# Implementation Decisions

## Decisions Made During Plan Review

### 1. Step 1 Scope Reduction
**Decision:** Modify Step 1 to focus only on adding the `github_integration` test marker
**Rationale:** PyGithub dependency was already installed outside the implementation plan
**Choice:** Option B - Keep Step 1 but only for the test marker addition

### 2. Configuration Key Naming
**Decision:** Use `github.test_repo_url` instead of `github.repo_url_integration_tests`
**Rationale:** Shorter and cleaner while still being clear
**Choice:** Option B - Change to `github.test_repo_url`

### 3. Error Handling Strategy
**Decision:** Keep empty dict `{}` return on all errors
**Rationale:** Simple, consistent, safe approach that follows KISS principle
**Choice:** Option A - Keep `{}` return on all errors

### 4. Test Repository Setup Guidance
**Decision:** Enhance configuration example with comment showing expected repo URL format
**Rationale:** Provides guidance without adding complexity
**Choice:** Option D - Add comment in configuration example

### 5. Test Branch Cleanup
**Decision:** Add cleanup logic to delete test branch after closing PR
**Rationale:** Prevents test branch accumulation in repository
**Choice:** Option A - Add cleanup logic to the test itself

### 6. File Structure Change
**Decision:** Use package structure `src/mcp_coder/utils/github_operations/` with `__init__.py` and `gh_pull_requests.py`
**Rationale:** Sets up for future GitHub operations expansion while maintaining organization
**Choice:** Option B - Package with `__init__.py` that exports functions + `gh_pull_requests.py` implementation

### 7. Test Marker Documentation
**Decision:** Update existing marker documentation pattern to include github_integration
**Rationale:** Follows established documentation patterns in pyproject.toml
**Choice:** Option B - Update existing marker documentation pattern

### 8. Additional Function - list_pull_requests()
**Decision:** Add `list_pull_requests(state="open")` function returning list of PR summary dicts
**Rationale:** Provides useful listing functionality while keeping simple API consistent
**Choice:** Option A - Simple list function with state filter

### 9. Repository Parameter Design
**Decision:** Add explicit `repo_url` parameter to all four functions for production use
**Rationale:** Tests use configured test repo, production functions need repo as parameter for flexibility
**Choice:** Option A - Add `repo_url` parameter to all four functions (create, get, list, close)


### 10. API Design Change: PullRequestManager Class
**Decision:** Replace functional API with object-oriented PullRequestManager class approach
**Rationale:** User suggested PullRequestManager class similar to `Github(token).get_repo(repo_name)` pattern would simplify and enhance the API
**Benefits Discussed:** Reduced repetition (no repo_url in every call), better resource management (single GitHub client), cleaner API, enhanced state management
**Choice:** Implement PullRequestManager class as primary API, remove old functional API
**User Quote:** "Okay, don't worry about the old API any more. Can you review the project plan and update it?"
