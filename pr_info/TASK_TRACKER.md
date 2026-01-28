# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** for Issue #75: File size checker CLI command.

---

## Tasks

### Step 1: Dependencies and Filesystem Wrapper
**File:** [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Update pyproject.toml - move mcp-server-filesystem to main dependencies
- [x] Create src/mcp_coder/mcp_server_filesystem.py wrapper
- [x] Create tests/checks/__init__.py package
- [x] Verify dependency installation works
- [x] Prepare git commit message for step 1
- [x] All Step 1 tasks completed

### Step 2: Core File Size Checking Logic (TDD)
**File:** [pr_info/steps/step_2.md](steps/step_2.md)

- [x] Create src/mcp_coder/checks/__init__.py with exports
- [x] Write tests for count_lines() function
- [x] Implement count_lines() function
- [x] Write tests for load_allowlist() function
- [x] Implement load_allowlist() function
- [x] Write tests for get_file_metrics() function
- [x] Implement get_file_metrics() function
- [x] Write tests for check_file_sizes() function
- [x] Implement check_file_sizes() function
- [x] Write tests for render_output() function
- [x] Implement render_output() function
- [x] Write tests for render_allowlist() function
- [x] Implement render_allowlist() function
- [x] Run pylint, mypy on checks package
- [x] Prepare git commit message for step 2
- [x] All Step 2 tasks completed

### Step 3: CLI Integration
**File:** [pr_info/steps/step_3.md](steps/step_3.md)

- [ ] Write CLI command handler tests
- [ ] Create src/mcp_coder/cli/commands/check_file_sizes.py
- [ ] Update src/mcp_coder/cli/main.py with check command group
- [ ] Write CLI integration tests
- [ ] Manual test: mcp-coder check file-size --help
- [ ] Manual test: mcp-coder check file-size on project
- [ ] Run full test suite
- [ ] Run pylint, mypy on all changes
- [ ] Prepare git commit message for step 3
- [ ] All Step 3 tasks completed

---

## Pull Request

- [ ] Review all changes and ensure consistency
- [ ] Update docs/cli-reference.md with new command
- [ ] Submit pull request for review
