# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: A complete user-facing capability
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Implement Rebase Detection Utility
[x] **Step 1.1**: Write tests for `needs_rebase()` function in `tests/utils/git_operations/test_branches.py`
[x] **Step 1.2**: Implement `needs_rebase()` function in `src/mcp_coder/utils/git_operations/branches.py`
[x] **Step 1.3**: Run quality checks: pylint, pytest, mypy - fix all issues
[x] **Step 1.4**: Prepare git commit message for rebase detection utility

### Step 2: Create Branch Status Data Structures
[x] **Step 2.1**: Write tests for `BranchStatusReport` dataclass in `tests/utils/test_branch_status.py`
[x] **Step 2.2**: Implement `BranchStatusReport` and helpers in `src/mcp_coder/utils/branch_status.py`
[x] **Step 2.3**: Run quality checks: pylint, pytest, mypy - fix all issues
[x] **Step 2.4**: Prepare git commit message for branch status data structures

### Step 3: Implement Branch Status Collection Logic
[x] **Step 3.1**: Write tests for `collect_branch_status()` function in `tests/utils/test_branch_status.py`
[x] **Step 3.2**: Implement `collect_branch_status()` and helpers in `src/mcp_coder/utils/branch_status.py`
[x] **Step 3.3**: Run quality checks: pylint, pytest, mypy - fix all issues
[x] **Step 3.4**: Prepare git commit message for branch status collection logic

### Step 4: Implement CLI Command
[x] **Step 4.1**: Write tests for CLI command in `tests/cli/commands/test_check_branch_status.py`
[x] **Step 4.2**: Implement CLI command in `src/mcp_coder/cli/commands/check_branch_status.py`
[x] **Step 4.3**: Run quality checks: pylint, pytest, mypy - fix all issues
[x] **Step 4.4**: Prepare git commit message for CLI command implementation

### Step 5: Add CLI Parser Integration
[x] **Step 5.1**: Write tests for CLI parser integration in `tests/cli/test_main.py`
[x] **Step 5.2**: Modify `src/mcp_coder/cli/main.py` to add command parser and routing
[x] **Step 5.3**: Run quality checks: pylint, pytest, mypy - fix all issues
[x] **Step 5.4**: Prepare git commit message for CLI parser integration

### Step 6: Create Slash Command Wrapper
[x] **Step 6.1**: Create `.claude/commands/check_branch_status.md` slash command wrapper
[x] **Step 6.2**: Test slash command functionality manually
[x] **Step 6.3**: Run quality checks: pylint, pytest, mypy - fix all issues
[x] **Step 6.4**: Prepare git commit message for slash command wrapper

## Pull Request
[x] **PR.1**: Review all implementation steps are complete
[x] **PR.2**: Run final quality checks across entire codebase
[x] **PR.3**: Prepare comprehensive PR description summarizing the branch status check feature