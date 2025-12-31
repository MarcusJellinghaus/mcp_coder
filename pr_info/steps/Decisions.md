# Decisions Log

Decisions made during plan review discussion.

## Structure Decisions

1. **Keep 5-step structure** (now 6 with Step 0): Do not merge Step 1 and Step 2. Keep them separate as originally planned.

2. **Add Step 0**: Refactor branch validation into a reusable function in `branches.py` before proceeding with CI implementation steps.

## Data Structure Decisions

3. **Remove CIFailureData TypedDict**: Not needed - each method has its own clear return type. The combined type was never used as a return value.

4. **Include workflow info in CIStatusData**: Add `workflow_name`, `event`, and `workflow_path` fields to the run data returned by `get_latest_ci_status`.

## Method Behavior Decisions

5. **get_latest_ci_status workflow filtering**: Return latest run across ALL workflows (no filtering). Workflow info is included in response so consumer can identify which workflow.

6. **get_failed_job_logs - ZIP handling**: GitHub API returns logs as a ZIP file. Update implementation to:
   - Add `requests` to `pyproject.toml` dependencies
   - Use `Bearer` token format for authentication
   - Extract ZIP content using `zipfile` module

7. **get_artifacts instead of get_junit_failures**: Rename and simplify - no XML parsing. Just download artifacts and return raw content. Let consumer handle parsing.

8. **get_artifacts return type**: Return `Dict[str, str]` - extract ZIP and return file contents as strings.

9. **get_artifacts filtering**: Add optional `name_filter` parameter. Default returns all artifacts, consumer can filter if desired.

## Error Handling Decisions

10. **Rate limiting**: Handle same as other errors - log and return empty/default. Consistent with existing managers.

11. **Large log size**: No limit - return full logs, let consumer handle size.

## Validation Decisions

12. **Branch validation strictness**: Use basic git rules - no spaces, no special characters like `~`, `^`, `:`, `?`, `*`, `[`. Refactor existing inline validation from `create_branch()` into reusable function.

## Documentation Decisions

13. **Algorithm detail level**: Keep detailed structure in step files but add note that field names are illustrative and should be verified against actual PyGithub objects.

14. **Test fixtures**: Use `@pytest.fixture` pattern - standard pytest approach.

## Plan Review Decisions (Round 2)

15. **Log retrieval approach**: Return all logs from the run as `Dict[str, str]`. Job status info is NOT included (consumer already has it from `get_latest_ci_status()`). Consumer can filter logs by job name using the job info they already have.

16. **Shared ZIP download helper**: Create `_download_and_extract_zip(url: str)` helper in Step 3, reuse in Step 4.

17. **Distinguishing empty responses**: Return empty only for "no runs found". Let exceptions propagate for API errors or invalid branch (handled by `@_handle_github_errors` decorator).

18. **Large artifact handling**: No limit on artifact size. Document memory implications. Consumer's responsibility to use `name_filter` wisely.

19. **Binary file handling in artifacts**: Return `Dict[str, str]` only. Skip binary files with a log warning. Add binary support in a future iteration if needed.

20. **Step 0 simplification**: Keep Step 0 but simplify test cases - just cover valid/invalid basics, fewer edge cases.

21. **Smoke test default branch**: Use `get_default_branch_name()` from `git_operations.branches` to detect the correct branch dynamically.

22. **Fixture location**: Shared fixtures (like `mock_repo`, `ci_manager`) should go in `tests/utils/github_operations/conftest.py`.
