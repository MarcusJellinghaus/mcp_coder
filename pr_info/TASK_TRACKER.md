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

### Step 1: Add Git Branch Diff Function with Tests
- [ ] Write tests in tests/utils/test_git_workflows.py
- [ ] Add get_branch_diff() function to src/mcp_coder/utils/git_operations.py
- [ ] Run pylint check for Step 1 implementation
- [ ] Run pytest check for Step 1 implementation  
- [ ] Run mypy check for Step 1 implementation
- [ ] Prepare git commit message for Step 1

### Step 2: Add Repository Cleanup Functions with Tests
- [ ] Create tests/test_create_pr.py with tests for cleanup functions
- [ ] Add utility functions to workflows/create_PR.py
- [ ] Run pylint check for Step 2 implementation
- [ ] Run pytest check for Step 2 implementation
- [ ] Run mypy check for Step 2 implementation
- [ ] Prepare git commit message for Step 2

### Step 3: Add PR Summary Prompt Template
- [ ] Add PR Summary Generation prompt to src/mcp_coder/prompts/prompts.md
- [ ] Run pylint check for Step 3 implementation
- [ ] Run pytest check for Step 3 implementation
- [ ] Run mypy check for Step 3 implementation
- [ ] Prepare git commit message for Step 3

### Step 4: Implement Main Workflow Script with Tests
- [ ] Extend tests/test_create_pr.py with main workflow tests
- [ ] Complete workflows/create_PR.py main function and helpers
- [ ] Run pylint check for Step 4 implementation
- [ ] Run pytest check for Step 4 implementation
- [ ] Run mypy check for Step 4 implementation
- [ ] Prepare git commit message for Step 4

### Step 5: Create Windows Batch Wrapper and Integration Tests
- [ ] Create workflows/create_PR.bat wrapper
- [ ] Create tests/test_create_pr_integration.py
- [ ] Run pylint check for Step 5 implementation
- [ ] Run pytest check for Step 5 implementation
- [ ] Run mypy check for Step 5 implementation
- [ ] Prepare git commit message for Step 5

### Final Validation
- [ ] Final integration test of complete workflow
- [ ] All tasks completed

### Pull Request
- [ ] Prepare PR review documentation
- [ ] Generate PR summary and description
