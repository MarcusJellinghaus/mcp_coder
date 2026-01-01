# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**

1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**

- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Write Tests for `RepoIdentifier` Class
- [x] Create tests in tests/utils/github_operations/test_repo_identifier.py
- [x] Implement TestRepoIdentifierFromFullName class (5 unit tests)
- [x] Implement TestRepoIdentifierFromRepoUrl class (6 unit tests)
- [x] Implement TestRepoIdentifierProperties class (3 unit tests)
- [x] Run pylint on test file and fix all issues
- [x] Run pytest on test file and fix all issues
- [x] Run mypy on test file and fix all issues
- [x] Prepare git commit message for Step 1

### Step 2: Implement `RepoIdentifier` Class
- [ ] Add RepoIdentifier dataclass to src/mcp_coder/utils/github_operations/github_utils.py
- [ ] Implement from_full_name() factory method with validation
- [ ] Implement from_repo_url() factory method for HTTPS and SSH GitHub URLs
- [ ] Implement full_name and cache_safe_name properties
- [ ] Implement __str__ method
- [ ] Add RepoIdentifier to src/mcp_coder/utils/github_operations/__init__.py exports
- [ ] Run tests from Step 1 to verify behavior
- [ ] Run pylint on implementation and fix all issues
- [ ] Run pytest on all tests and fix all issues
- [ ] Run mypy on implementation and fix all issues
- [ ] Prepare git commit message for Step 2

### Step 3: Update `coordinator.py` to Use `RepoIdentifier`
- [ ] Add import for RepoIdentifier from github_utils
- [ ] Delete the entire _parse_repo_identifier() function
- [ ] Simplify _get_cache_file_path() to accept RepoIdentifier and remove owner parameter
- [ ] Update get_cached_eligible_issues() to use RepoIdentifier
- [ ] Update execute_coordinator_run() to create RepoIdentifier from repo_url
- [ ] Simplify exception handler to use RepoIdentifier directly
- [ ] Run pylint on coordinator.py and fix all issues
- [ ] Run pytest on all coordinator tests and fix all issues
- [ ] Run mypy on coordinator.py and fix all issues
- [ ] Prepare git commit message for Step 3

### Step 4: Update Tests and Documentation
- [ ] Delete TestParseRepoIdentifier class from tests/utils/test_coordinator_cache.py
- [ ] Delete test_get_cached_eligible_issues_url_parsing_fallback test
- [ ] Update TestCacheFilePath to use RepoIdentifier
- [ ] Add test_no_spurious_warnings_with_repo_identifier integration test
- [ ] Update imports in test file to use RepoIdentifier
- [ ] Run pylint on test file and fix all issues
- [ ] Run pytest on all tests and fix all issues
- [ ] Run mypy on test file and fix all issues
- [ ] Prepare git commit message for Step 4

### Pull Request
- [ ] Review all code changes for consistency and quality
- [ ] Run full test suite to ensure no regressions
- [ ] Prepare comprehensive PR description summarizing all changes
- [ ] Create pull request with proper title and description