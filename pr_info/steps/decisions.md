# Implementation Decisions

This document logs all decisions made during the planning phase discussions.

## Decision 1: Label Configuration Strategy
**Date**: 2025-10-28  
**Context**: How to load and filter label configuration for coordinator run  
**Decision**: Reuse existing functionality by moving `build_label_lookups()` from `validate_labels.py` to `label_config.py`  
**Rationale**: 
- Minimal refactoring required
- `validate_labels.py` already has the exact filtering logic needed
- Most similar to current codebase patterns
- Simple to implement - just move one function to shared module

**Impact**:
- `workflows/label_config.py`: Add `build_label_lookups()` function
- `workflows/validate_labels.py`: Update import to use shared function
- `coordinator.py`: Call `build_label_lookups()` to get label categories

---

## Decision 2: BaseGitHubManager Refactoring for Remote Operations
**Date**: 2025-10-28  
**Context**: Coordinator needs to work with GitHub API without local repository clones  
**Decision**: Refactor `BaseGitHubManager.__init__()` to accept either `project_dir` OR `repo_url`  
**Rationale**:
- Coordinator has repo URLs from config, not local clones
- All GitHub operations are remote API calls
- `project_dir` is only used to extract repo URL from git remote
- Existing code using `project_dir` remains unchanged

**Impact**:
- `src/mcp_coder/utils/github_operations/base_manager.py`: Support both `project_dir` and `repo_url` parameters
- Backward compatible - existing usage continues to work
- Coordinator can instantiate managers with: `IssueManager(repo_url="https://github.com/user/repo.git")`

---

## Decision 3: Label Update Error Handling (KISS)
**Date**: 2025-10-28  
**Context**: What happens if label removal succeeds but label addition fails?  
**Decision**: Use fail-fast approach - let errors propagate, accept potential partial state  
**Rationale**:
- KISS principle - keep implementation simple
- Partial state (missing label) is unlikely and acceptable
- No complex rollback logic needed
- Aligns with overall fail-fast strategy in the feature

**Impact**:
- Simple error handling in `dispatch_workflow()`
- If label operations fail, coordinator stops processing

---

## Decision 4: Jenkins Job Verification Strategy
**Date**: 2025-10-28  
**Context**: Should coordinator wait for Jenkins jobs to complete?  
**Decision**: Only verify job successfully queued, don't wait for execution or completion  
**Rationale**:
- KISS principle - fast execution
- Coordinator can process multiple issues quickly
- Failed jobs detected by other means (Jenkins notifications, manual monitoring)
- Waiting for completion could timeout or block for extended periods

**Impact**:
- `dispatch_workflow()` calls `client.get_job_status()` once to verify queued
- Returns immediately after label update
- Future enhancement: separate monitoring process for failed jobs (out of scope)

---

## Decision 5: Duplicate Processing Prevention
**Date**: 2025-10-28  
**Context**: Race condition if multiple coordinator instances run simultaneously  
**Decision**: Accept the race condition - require manual coordination (don't run multiple instances simultaneously)  
**Rationale**:
- KISS principle - avoid complex locking mechanisms
- Simple operational requirement vs. infrastructure overhead
- Can be added as future enhancement if needed

**Impact**:
- Document operational requirement: only run one `coordinator run` at a time
- No locking mechanism in initial implementation
- Future enhancement: file-based or database locking (out of scope)

---

## Decision 6: Workflow Command Templates
**Date**: 2025-10-28  
**Context**: Jenkins commands need different templates per workflow type  
**Decision**: Create three separate command templates with:
- Hard-coded `/workspace/repo` as project_dir
- Add `git pull` to ensure latest code
- Remove `claude mcp list` command
- Include appropriate git checkout per workflow

**Rationale**:
- Three workflows have different requirements:
  - `create-plan`: runs on main branch
  - `implement`: runs on feature branch
  - `create-pr`: runs on feature branch
- Hard-coding `/workspace/repo` matches existing `DEFAULT_TEST_COMMAND` pattern
- `git pull` ensures latest code before execution
- `claude mcp list` removed for simplicity

**Templates**:
```bash
# Template 1: create-plan
git checkout main
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo

# Template 2: implement
git checkout {branch_name}
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo

# Template 3: create-pr
git checkout {branch_name}
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo
```

**Impact**:
- Add three template constants to `coordinator.py`
- `dispatch_workflow()` selects appropriate template based on workflow type
