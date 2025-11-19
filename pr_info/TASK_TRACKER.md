# Task Tracker: Add --execution-dir Flag Implementation

## Implementation Steps

### Step 1: Add Path Resolution Utility ✅
**Status:** Complete  
**File:** `pr_info/steps/step_1.md`  
**Summary:** Create utility function to resolve and validate execution directory paths

**Key Deliverables:**
- [x] `src/mcp_coder/cli/utils.py` - Add `resolve_execution_dir()` function
- [x] `tests/cli/test_utils.py` - Add `TestResolveExecutionDir` test class
- [x] 6 test cases covering all edge cases
- [x] Function handles None, absolute, relative paths correctly

**Complexity:** Low  
**Estimated Lines:** ~75 total (15 implementation + 60 tests)

**Commit Message:**
```
feat(cli): Add resolve_execution_dir utility function

Implement path resolution utility for execution directory handling with
validation and CWD resolution. Includes comprehensive test coverage for
absolute paths, relative paths, and error cases.
```

---

### Step 2: Update CLI Argument Parsing ✅
**Status:** Complete  
**File:** `pr_info/steps/step_2.md`  
**Summary:** Add --execution-dir argument to all commands that invoke Claude

**Key Deliverables:**
- [x] `src/mcp_coder/cli/main.py` - Add `--execution-dir` to 5 command parsers
- [x] `tests/cli/test_main.py` - Add `TestExecutionDirArgument` test class
- [x] 8 test cases verifying argument parsing
- [x] Help text shows flag for all affected commands

**Commands Updated:**
- prompt
- commit auto
- implement
- create-plan
- create-pr

**Complexity:** Low  
**Estimated Lines:** ~120 total (20 implementation + 100 tests)

**Commit Message:**
```
feat(cli): Add --execution-dir argument to CLI commands

Add --execution-dir flag to all commands that invoke Claude (prompt,
commit auto, implement, create-plan, create-pr) to control Claude's
working directory. Includes comprehensive test coverage with 8 test cases
verifying argument parsing across all affected commands.
```

---

### Step 5: Update LLM Interface Layer ✅
**Status:** Complete  
**File:** `pr_info/steps/step_5.md`  
**Summary:** Add execution_dir parameter to ask_llm() and prompt_llm() functions

**Key Deliverables:**
- [x] `src/mcp_coder/llm/interface.py` - Add execution_dir parameter
- [x] Update `ask_llm()` function signature
- [x] Update `prompt_llm()` function signature
- [x] `tests/llm/test_interface.py` - Add execution_dir tests
- [x] Pass execution_dir as cwd to providers

**Key Concept:** Separate `project_dir` (env vars) from `execution_dir` (subprocess cwd)

**Complexity:** Low  
**Estimated Lines:** ~90 total (10 implementation + 80 tests)

**Note:** Step 5 moved before steps 3-4 per Decision #2 - workflows and interface must be updated before command handlers can use them.

**Commit Message:**
```
feat(llm): Add execution_dir parameter to LLM interface

Add execution_dir parameter to ask_llm() and prompt_llm() to separate
execution context from project directory. Parameter is passed as cwd to
Claude providers, enabling proper workspace support. Includes comprehensive
test coverage with 43 tests verifying parameter handling across CLI and API
methods.

Key changes:
- ask_llm(): Add execution_dir parameter, pass as cwd to provider
- prompt_llm(): Add execution_dir parameter for both CLI and API methods
- Update docstrings to clarify project_dir vs execution_dir semantics
- All 43 tests pass, type checking and linting clean
```

---

### Step 6: Update Claude Provider Documentation ✅
**Status:** Complete  
**File:** `pr_info/steps/step_6.md`  
**Summary:** Update docstrings to clarify cwd parameter usage in Claude providers

**Key Deliverables:**
- [x] `src/mcp_coder/llm/providers/claude/claude_code_cli.py` - Update docstring
- [x] `src/mcp_coder/llm/providers/claude/claude_code_api.py` - Update docstring
- [x] `src/mcp_coder/llm/providers/claude/claude_code_interface.py` - Update docstring
- [x] Clarify cwd vs project_dir distinction
- [x] Add inline comments where helpful

**Complexity:** Very Low (documentation only)  
**Estimated Lines:** ~30 total (docstring updates)

**Commit Message:**
```
docs(llm): Clarify cwd parameter in Claude provider docstrings

Update documentation in Claude provider files to clarify that the `cwd`
parameter controls subprocess execution directory, not project location.

Changes:
- claude_code_cli.py: Simplified cwd docstring and inline comments
- claude_code_api.py: Clarified cwd purpose across all async/sync functions
- claude_code_interface.py: Updated cwd documentation for consistency

This is a documentation-only change with no behavior modifications.
All unit tests pass (66 tests).
```

---

### Step 7: Update Workflow Layers ⏳
**Status:** Not Started  
**File:** `pr_info/steps/step_7.md`  
**Summary:** Update workflow functions to accept and pass execution_dir to LLM calls

**Key Deliverables:**
- [ ] `src/mcp_coder/workflows/implement/core.py` - Add execution_dir parameter
- [ ] `src/mcp_coder/workflows/create_plan.py` - Add execution_dir parameter
- [ ] `src/mcp_coder/workflows/create_pr/core.py` - Add execution_dir parameter
- [ ] Update all LLM calls in workflows
- [ ] Update workflow tests
- [ ] Propagate parameter through sub-functions

**Functions Updated:**
- `prepare_task_tracker()`
- `run_implement_workflow()`
- `create_plan()`
- `create_pr_workflow()`

**Complexity:** Medium  
**Estimated Lines:** ~190 total (40 implementation + 150 tests)

---

### Step 3: Update Command Handlers (Prompt, Commit) ⏳
**Status:** Not Started  
**File:** `pr_info/steps/step_3.md`  
**Summary:** Update prompt and commit command handlers to extract and validate execution_dir

**Key Deliverables:**
- [ ] `src/mcp_coder/cli/commands/prompt.py` - Extract and validate execution_dir
- [ ] `src/mcp_coder/cli/commands/commit.py` - Extract and validate execution_dir
- [ ] `tests/cli/commands/test_prompt.py` - Add execution_dir tests
- [ ] `tests/cli/commands/test_commit.py` - Add execution_dir tests
- [ ] Error handling for invalid paths

**Complexity:** Low  
**Estimated Lines:** ~150 total (30 implementation + 120 tests)

**Note:** Step 3 moved after steps 5-7 per Decision #2 - command handlers depend on LLM interface and workflows having execution_dir support.

---

### Step 4: Update Command Handlers (Implement, Create-Plan, Create-PR) ⏳
**Status:** Not Started  
**File:** `pr_info/steps/step_4.md`  
**Summary:** Update remaining command handlers to extract and pass execution_dir to workflows

**Key Deliverables:**
- [ ] `src/mcp_coder/cli/commands/implement.py` - Extract and pass execution_dir
- [ ] `src/mcp_coder/cli/commands/create_plan.py` - Extract and pass execution_dir
- [ ] `src/mcp_coder/cli/commands/create_pr.py` - Extract and pass execution_dir
- [ ] Tests for all three commands
- [ ] Consistent error handling pattern

**Complexity:** Low  
**Estimated Lines:** ~225 total (45 implementation + 180 tests)

**Note:** Step 4 moved after steps 5-7 per Decision #2 - command handlers depend on workflows having execution_dir support.

---

### Step 8: Integration Testing and Documentation ⏳
**Status:** Not Started  
**File:** `pr_info/steps/step_8.md`  
**Summary:** Create integration tests and update all documentation

**Key Deliverables:**
- [ ] `tests/integration/test_execution_dir_integration.py` - New integration tests
- [ ] `docs/architecture/ARCHITECTURE.md` - Document architectural changes
- [ ] `.claude/CLAUDE.md` - Add usage guidelines
- [ ] End-to-end testing of all scenarios
- [ ] Verify separation of concerns works correctly

**Test Scenarios:**
- Workspace with multiple projects
- CI/CD environments
- Config discovery in execution_dir
- Git operations in project_dir
- Relative path resolution

**Complexity:** Medium  
**Estimated Lines:** ~450 total (300 tests + 150 docs)

---

## PR Creation Tasks

### Task 1: Create Pull Request Summary ⏳
**Status:** Not Started  
**Description:** Use Claude to generate comprehensive PR summary

**Requirements:**
- [ ] Reference all 8 implementation steps
- [ ] Summarize architectural changes
- [ ] List all modified files
- [ ] Include testing strategy
- [ ] Show example usage
- [ ] Note breaking changes (if any)

---

### Task 2: Final Quality Checks ⏳
**Status:** Not Started  
**Description:** Run all quality checks before PR submission

**Checklist:**
- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] All integration tests pass: `pytest tests/integration/ -v`
- [ ] Type checking passes: `mypy src/mcp_coder/`
- [ ] Linting passes: `pylint src/mcp_coder/`
- [ ] Code formatting: `black src/mcp_coder/`
- [ ] Import sorting: `isort src/mcp_coder/`
- [ ] Documentation builds without errors

---

### Task 3: Update CHANGELOG ⏳
**Status:** Not Started  
**Description:** Document changes in CHANGELOG.md (if exists)

**Entry:**
```markdown
## [Unreleased]

### Added
- `--execution-dir` flag to control Claude's working directory
- Separation of execution context from project directory
- Support for workspace-based MCP configurations

### Changed
- Default execution behavior now uses shell's CWD (breaking change)
- Claude subprocess execution location is now explicit

### Documentation
- Updated ARCHITECTURE.md with execution context design
- Added usage examples for --execution-dir flag
```

---

## Implementation Metrics

**Total Estimated Lines:**
- Implementation: ~180 lines
- Tests: ~800 lines  
- Documentation: ~180 lines
- **Total: ~1,160 lines**

**Complexity Distribution:**
- Very Low: 1 step (Step 6 - documentation only)
- Low: 5 steps (Steps 1-5)
- Medium: 2 steps (Steps 7-8)

**Test Coverage Target:** >90% for new code

---

## Dependencies Between Steps - ACTUAL IMPLEMENTATION ORDER

```
Step 1 (Path Resolution) ✅ COMPLETE
  ↓
Step 2 (CLI Parsing) ✅ COMPLETE
  ↓
Step 5 (LLM Interface) ← Add execution_dir to ask_llm/prompt_llm
  ↓
Step 6 (Provider Documentation) ← Document cwd vs project_dir
  ↓
Step 7 (Workflows) ← Update workflows to use execution_dir
  ↓
Step 3 (Prompt/Commit Handlers) ← Extract execution_dir and pass to LLM/workflows
  ↓
Step 4 (Other Handlers) ← Extract execution_dir and pass to workflows
  ↓
Step 8 (Integration + Docs) ← End-to-end testing
```

**Sequential Implementation Required:** Yes  
**Rationale for Reordering:** Per Decision #2, the infrastructure (LLM interface and workflows) must support execution_dir before command handlers can use it. This prevents breaking changes and ensures clean integration.

---

## Success Criteria

**Feature is complete when:**
- ✅ All 8 implementation steps are completed
- ✅ All tests pass (unit + integration)
- ✅ All quality checks pass (mypy, pylint)
- ✅ Documentation is updated and accurate
- ✅ Manual testing validates real-world scenarios
- ✅ No regression in existing functionality
- ✅ PR is reviewed and approved

**User Experience:**
- Users can explicitly control Claude's execution directory
- Separation of concerns is clear and intuitive
- Default behavior (CWD) works as expected
- Error messages are helpful
- Help text is clear

---

## Notes

**Design Philosophy:** KISS (Keep It Simple, Stupid)
- Minimal code changes
- Clear parameter naming
- Consistent patterns across layers
- Comprehensive but focused testing

**Breaking Changes:**
- Default behavior changes from `project_dir` to shell's CWD
- Acceptable for v0.1.x
- Users can explicitly set `--execution-dir` for old behavior

**Future Enhancements:**
- Could add environment variable: `MCP_CODER_EXECUTION_DIR`
- Could add config file option for default execution_dir
- Not included in this implementation (KISS)
