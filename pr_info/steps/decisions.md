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

---

## Decision 7: Code Review Follow-up Decisions
**Date**: 2025-10-29  
**Context**: Post-implementation code review identified areas for clarification and improvement

### Decision 7.1: Hardcoded `/workspace/repo` Path Strategy
**Decision**: Keep `/workspace/repo` hardcoded in command templates (KISS approach)  
**Rationale**:
- Simple operational requirement: Jenkins workspace structure must be consistent
- Matches existing `DEFAULT_TEST_COMMAND` pattern in codebase
- Can be made configurable in future if multiple workspace paths needed
- KISS principle - avoid premature flexibility

**Impact**:
- Add documentation comment explaining Jenkins workspace requirement
- No configuration parameter needed initially

### Decision 7.2: PYTHONPATH Configuration for Cross-Platform Support
**Decision**: Use forward slashes and single path in `.mcp.json`: `"${MCP_CODER_PROJECT_DIR}/src"`  
**Rationale**:
- Must support both Windows and Linux
- Python accepts forward slashes on all platforms
- After refactoring `build_label_lookups()` to `src/mcp_coder/...`, only `src/` in PYTHONPATH is needed
- Simpler than maintaining platform-specific configurations

**Impact**:
- Change `.mcp.json` PYTHONPATH from `"${MCP_CODER_PROJECT_DIR}\\src;${MCP_CODER_PROJECT_DIR}"` to `"${MCP_CODER_PROJECT_DIR}/src"`
- Works cross-platform without conditional logic

### Decision 7.3: Package Data Verification
**Decision**: Trust setuptools package data mechanism, no additional test needed  
**Rationale**:
- Package data is standard setuptools feature with well-tested behavior
- If package builds successfully, `config/*.json` will be included
- Can be verified in manual installation testing
- KISS principle - avoid test for framework behavior

**Impact**:
- No additional test file needed
- Manual verification during release testing sufficient

### Decision 7.4: Error Message Verbosity
**Decision**: Keep current simpler error messages  
**Rationale**:
- Current messages are clear enough for users familiar with config structure
- Avoid over-verbose output
- Users can refer to documentation for configuration examples
- KISS principle

**Impact**:
- No changes to error message formatting

### Decision 7.5: Label Configuration Loading Pattern
**Decision**: Keep current two-call pattern, add module docstring documentation  
**Rationale**:
- Two-line pattern (`get_labels_config_path()` + `load_labels_config()`) is explicit and clear
- No hidden behavior or magic
- Adding helper function creates one more API to maintain
- Documentation makes pattern clear for future developers
- KISS principle

**Impact**:
- Add comprehensive module docstring to `label_config.py` with usage examples
- No new helper functions

### Decision 7.6: Edge Case Test Coverage
**Decision**: Skip additional edge case tests for now  
**Rationale**:
- Current test coverage is comprehensive (>85%)
- Edge cases identified are unlikely scenarios
- Can be added if issues arise in production
- KISS principle - test what matters most

**Impact**:
- No additional test cases for:
  - Invalid JSON in bundled labels.json (framework validation)
  - Concurrent coordinator runs (documented as out-of-scope)
  - Network failures (already covered by error handling decorator)

### Decision 7.7: Label Names vs Internal IDs in Code
**Decision**: Use GitHub API label names directly in Python code (not internal_ids)  
**Rationale**:
- GitHub API works with label names (visible label text)
- Issue queries return names, add/remove operations use names
- Using names avoids constant translation internal_id ↔ name
- Simpler code with less indirection
- Label names rarely change in practice
- KISS principle

**Impact**:
- `WORKFLOW_MAPPING` uses label names like `"status-02:awaiting-planning"`
- Add comment explaining design decision and relationship to config
- Internal IDs remain useful for human-readable references in documentation

### Decision 7.8: Documentation for Hard-Coded Values
**Decision**: Add simple comment explaining label name dependency  
**Rationale**:
- Makes implicit dependency explicit
- Helps future maintainers understand relationship to config
- Simple one-line comment sufficient
- KISS principle

**Impact**:
- Add comment to `WORKFLOW_MAPPING`: "Label names must match those defined in config/labels.json"
