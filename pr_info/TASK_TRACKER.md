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
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

### Step 1: Label Configuration JSON ([details](steps/step_1.md))
- [x] Create workflows/config/labels.json with 10 workflow status labels
- [x] Create workflows/label_config.py with load_labels_config() function
- [x] Create tests/workflows/config/test_labels.json test fixture
- [x] Create tests/workflows/test_label_config.py with validation tests
- [x] Create tests/workflows/test_issue_stats.py skeleton
- [ ] Run pylint check and fix all issues found
- [ ] Run pytest check (fast unit tests) and fix all issues found
- [ ] Run mypy check and fix all issues found
- [x] Prepare git commit message for label configuration setup

### Step 2: IssueManager.list_issues() Method ([details](steps/step_2.md))
- [ ] Add list_issues() method to src/mcp_coder/utils/github_operations/issue_manager.py
- [ ] Implement GitHub API pagination support
- [ ] Add unit tests to tests/utils/github_operations/test_issue_manager.py
- [ ] Test pagination handling with mocked data
- [ ] Test pull request filtering
- [ ] Run pylint check and fix all issues found
- [ ] Run pytest check (fast unit tests) and fix all issues found
- [ ] Run mypy check and fix all issues found
- [ ] Prepare git commit message for IssueManager.list_issues() method

### Step 3: Core Statistics Script ([details](steps/step_3.md))
- [ ] Create workflows/issue_stats.py main script
- [ ] Implement load_labels_config() integration
- [ ] Implement validate_issue_labels() function
- [ ] Implement filter_ignored_issues() function
- [ ] Implement group_issues_by_category() function
- [ ] Implement display_statistics() with summary and details modes
- [ ] Implement format_issue_line() for compact display
- [ ] Implement truncate_title() for long titles
- [ ] Implement parse_arguments() with --filter, --details, --ignore-labels flags
- [ ] Implement main() orchestrator function
- [ ] Add comprehensive tests to tests/workflows/test_issue_stats.py (12+ test functions)
- [ ] Test ignore labels feature (JSON config + CLI)
- [ ] Test validation error display in details mode
- [ ] Run pylint check and fix all issues found
- [ ] Run pytest check (fast unit tests) and fix all issues found
- [ ] Run mypy check and fix all issues found
- [ ] Prepare git commit message for issue statistics workflow

### Step 4: CLI Integration & Batch Launcher ([details](steps/step_4.md))
- [ ] Create workflows/issue_stats.bat batch launcher
- [ ] Configure UTF-8 encoding setup in batch script
- [ ] Configure PYTHONPATH setup in batch script
- [ ] Test batch launcher without arguments
- [ ] Test batch launcher with --filter flag
- [ ] Test batch launcher with --details flag
- [ ] Test batch launcher with --ignore-labels flag
- [ ] Test batch launcher with invalid arguments
- [ ] Test batch launcher from different directory
- [ ] Run pylint check on entire implementation and fix all issues found
- [ ] Run pytest check (fast unit tests) on entire implementation and fix all issues found
- [ ] Run mypy check on entire implementation and fix all issues found
- [ ] Prepare git commit message for CLI integration

### Step 5: Refactor define_labels.py ([details](steps/step_5.md))
- [ ] Add import for load_labels_config from workflows.label_config
- [ ] Remove WORKFLOW_LABELS constant from define_labels.py
- [ ] Update main() to load from JSON config
- [ ] Add error handling for missing/invalid JSON
- [ ] Extract only needed fields (name, color, description) from JSON
- [ ] Update tests in tests/workflows/test_define_labels.py
- [ ] Add test for missing config file error
- [ ] Add test for invalid JSON error
- [ ] Verify backward compatibility (same labels created)
- [ ] Manual test: workflows\define_labels.bat --dry-run
- [ ] Run pylint check and fix all issues found
- [ ] Run pytest check (fast unit tests) and fix all issues found
- [ ] Run mypy check and fix all issues found
- [ ] Prepare git commit message for define_labels refactoring

### Pull Request
- [ ] Review all changes across all steps
- [ ] Ensure all code quality checks pass (pylint, pytest, mypy)
- [ ] Verify all tests pass with fast unit test exclusions
- [ ] Create comprehensive PR summary for issue #109
- [ ] Include before/after examples in PR description
- [ ] Document new workflow usage in PR description
