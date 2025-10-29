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

### Step 0: Refactor Shared Components
**Details:** [step_0.md](steps/step_0.md)

- [x] Move `build_label_lookups()` from `workflows/validate_labels.py` to `workflows/label_config.py`
- [x] Move `LabelLookups` TypedDict to `workflows/label_config.py`
- [x] Update import in `workflows/validate_labels.py`
- [x] Add `repo_url` parameter support to `BaseGitHubManager.__init__()`
- [x] Implement `_init_with_project_dir()` helper method
- [x] Implement `_init_with_repo_url()` helper method
- [x] Update `_get_repository()` to work with both modes
- [x] Add validation for exactly one of (project_dir, repo_url)
- [x] Write tests for `BaseGitHubManager` with `project_dir` (existing behavior)
- [x] Write tests for `BaseGitHubManager` with `repo_url` (new behavior)
- [x] Write tests for error cases (neither, both parameters)
- [x] Run pylint check and fix all issues
- [x] Run pytest check (fast unit tests) and fix all issues
- [x] Run mypy check and fix all issues
- [ ] Prepare git commit message for Step 0

### Step 1: Label Configuration Integration
**Details:** [step_1.md](steps/step_1.md)

- [x] Add import statement in `src/mcp_coder/cli/commands/coordinator.py`
- [x] Import `load_labels_config` from `workflows.label_config`
- [x] Import `build_label_lookups` from `workflows.label_config`
- [x] Run pylint check and fix all issues
- [x] Run mypy check and fix all issues
- [x] Prepare git commit message for Step 1

### Step 2: Issue Filtering Logic
**Details:** [step_2.md](steps/step_2.md)

- [x] Add `PRIORITY_ORDER` constant to `coordinator.py`
- [x] Write test: `test_get_eligible_issues_filters_by_bot_pickup_labels()`
- [x] Write test: `test_get_eligible_issues_excludes_ignore_labels()`
- [x] Write test: `test_get_eligible_issues_priority_order()`
- [x] Write test: `test_get_eligible_issues_empty_result()`
- [x] Implement `get_eligible_issues()` function signature
- [x] Implement label configuration loading
- [x] Implement issue querying via `IssueManager`
- [x] Implement filtering by bot_pickup labels (exactly one required)
- [x] Implement exclusion by ignore_labels
- [x] Implement priority sorting (status-08 → 05 → 02)
- [x] Implement logging for filtering results
- [x] Run pylint check and fix all issues
- [x] Run pytest check (fast unit tests) and fix all issues
- [x] Run mypy check and fix all issues
- [x] Prepare git commit message for Step 2

### Step 3: Workflow Dispatcher
**Details:** [step_3.md](steps/step_3.md)

- [x] Add `WORKFLOW_MAPPING` constant to `coordinator.py`
- [x] Add `CREATE_PLAN_COMMAND_TEMPLATE` constant
- [x] Add `IMPLEMENT_COMMAND_TEMPLATE` constant
- [x] Add `CREATE_PR_COMMAND_TEMPLATE` constant
- [x] Write test: `test_dispatch_workflow_create_plan()`
- [x] Write test: `test_dispatch_workflow_implement()`
- [x] Write test: `test_dispatch_workflow_create_pr()`
- [x] Write test: `test_dispatch_workflow_missing_branch()`
- [x] Write test: `test_dispatch_workflow_jenkins_failure()`
- [x] Write test: `test_dispatch_workflow_label_update()`
- [x] Implement `dispatch_workflow()` function signature
- [x] Implement branch name resolution logic
- [x] Implement command template selection
- [x] Implement Jenkins job parameter building
- [x] Implement Jenkins job triggering via `JenkinsClient.start_job()`
- [x] Implement job status verification via `JenkinsClient.get_job_status()`
- [x] Implement label update (remove old, add new)
- [x] Implement error handling for missing branch
- [x] Run pylint check and fix all issues
- [x] Run pytest check (fast unit tests) and fix all issues
- [x] Run mypy check and fix all issues
- [ ] Prepare git commit message for Step 3

### Step 4: Main Coordinator Runner
**Details:** [step_4.md](steps/step_4.md)

- [x] Write test: `test_execute_coordinator_run_creates_config_if_missing()`
- [x] Write test: `test_execute_coordinator_run_single_repo_success()`
- [x] Write test: `test_execute_coordinator_run_no_eligible_issues()`
- [x] Write test: `test_execute_coordinator_run_missing_repo_config()`
- [x] Write test: `test_execute_coordinator_run_dispatch_failure_fail_fast()`
- [x] Write test: `test_execute_coordinator_run_requires_all_or_repo()`
- [x] Implement `execute_coordinator_run()` function signature
- [x] Implement config existence check and auto-creation
- [x] Implement repository list extraction (--all or --repo)
- [x] Implement Jenkins credentials retrieval
- [x] Implement per-repository processing loop
- [x] Implement repository config loading and validation
- [x] Implement manager initialization (Jenkins, Issue, Branch)
- [x] Implement eligible issues retrieval
- [x] Implement workflow dispatch loop with fail-fast
- [x] Implement logging for processing progress
- [x] Implement error handling and exit codes
- [x] Run pylint check and fix all issues
- [x] Run pytest check (fast unit tests) and fix all issues
- [x] Run mypy check and fix all issues
- [x] Prepare git commit message for Step 4

### Step 5: CLI Integration
**Details:** [step_5.md](steps/step_5.md)

- [x] Add import for `execute_coordinator_run` in `src/mcp_coder/cli/main.py`
- [x] Add coordinator run subparser in `create_parser()`
- [x] Add mutually exclusive group (--all | --repo, required=True)
- [x] Add routing logic in `main()` function
- [x] Write test: `test_coordinator_run_with_repo_argument()`
- [x] Write test: `test_coordinator_run_with_all_argument()`
- [x] Write test: `test_coordinator_run_with_log_level()`
- [x] Write test: `test_coordinator_run_requires_all_or_repo()`
- [x] Write test: `test_coordinator_run_all_and_repo_mutually_exclusive()`
- [x] Manual verification: `mcp-coder coordinator run --help`
- [x] Run pylint check and fix all issues
- [x] Run pytest check (fast unit tests) and fix all issues
- [x] Run mypy check and fix all issues
- [x] Prepare git commit message for Step 5

### Step 6: Integration Testing & Validation
**Details:** [step_6.md](steps/step_6.md)

- [x] Write test: `test_end_to_end_single_repo_multiple_issues()`
- [x] Write test: `test_end_to_end_all_repos_mode()`
- [x] Write test: `test_end_to_end_priority_ordering()`
- [x] Write test: `test_end_to_end_ignore_labels_filtering()`
- [x] Write test: `test_end_to_end_fail_fast_on_jenkins_error()`
- [x] Write test: `test_end_to_end_fail_fast_on_missing_branch()`
- [x] Write test: `test_end_to_end_log_level_pass_through()`
- [x] Write test: `test_no_open_issues()`
- [x] Write test: `test_all_issues_have_bot_busy_labels()`
- [x] Write test: `test_issue_with_multiple_bot_pickup_labels()`
- [x] Set up comprehensive mocks for all dependencies
- [x] Verify complete workflow (jobs triggered, labels updated)
- [x] Verify priority ordering in integration tests
- [x] Verify filtering logic in integration tests
- [x] Verify fail-fast behavior in integration tests
- [x] Run pylint check and fix all issues
- [x] Run pytest check (fast unit tests) and fix all issues
- [x] Run mypy check and fix all issues
- [x] Run all coordinator tests: `pytest tests/cli/commands/test_coordinator.py -v`
- [x] Run all CLI tests: `pytest tests/cli/test_main.py -v`
- [x] Prepare git commit message for Step 6

### Step 7: Code Review Follow-up
**Details:** [step_7.md](steps/step_7.md)

- [x] Update `.mcp.json` PYTHONPATH to `"${MCP_CODER_PROJECT_DIR}/src"`
- [x] Add documentation comment before `CREATE_PLAN_COMMAND_TEMPLATE`
- [x] Add documentation comment before `WORKFLOW_MAPPING`
- [ ] Add module docstring to `src/mcp_coder/utils/github_operations/label_config.py`
- [ ] Verify no code logic changes (documentation only)
- [ ] Verify existing tests still pass
- [ ] Prepare git commit message for Step 7

---

## Pull Request

- [ ] Review all changes across modified files
- [ ] Verify all unit tests pass
- [ ] Verify all integration tests pass
- [ ] Verify pylint, pytest, and mypy checks all pass
- [ ] Generate PR summary from commit messages and implementation
- [ ] Review PR description for completeness
- [ ] Check that all success criteria from summary.md are met
- [ ] Verify backward compatibility (existing coordinator test still works)
- [ ] Final validation: feature ready for PR submission
