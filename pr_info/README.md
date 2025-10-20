# Jenkins Job Automation - Implementation Plan

## Quick Navigation

This directory contains the complete implementation plan for issue #136: Jenkins Job Automation Support.

---

## 📋 Implementation Documents

### **Summary**
- **[summary.md](steps/summary.md)** - Complete overview with architecture, design decisions, and file list

### **Implementation Steps (TDD)**

1. **[step_1.md](steps/step_1.md)** - Models and Model Tests
   - Create `JobStatus` and `QueueSummary` dataclasses
   - Write comprehensive unit tests
   - **Files:** `models.py`, `test_models.py`
   - **Est. Time:** 30-45 minutes

2. **[step_2.md](steps/step_2.md)** - Jenkins Client and Unit Tests
   - Create `JenkinsClient` class with API methods
   - Implement configuration helper
   - Define custom exceptions
   - Write unit tests with mocked python-jenkins
   - **Files:** `client.py`, `test_client.py`
   - **Est. Time:** 60-90 minutes

3. **[step_3.md](steps/step_3.md)** - Integration Tests
   - Create integration tests with real Jenkins server
   - Add `jenkins_integration` pytest marker
   - Implement graceful skipping when not configured
   - **Files:** `test_integration.py`, `pyproject.toml`
   - **Est. Time:** 30-45 minutes

4. **[step_4.md](steps/step_4.md)** - Module Exports and Public API
   - Create package `__init__.py` with exports
   - Update utils `__init__.py`
   - Verify imports work
   - **Files:** `jenkins_operations/__init__.py`, `utils/__init__.py`
   - **Est. Time:** 15-20 minutes

5. **[step_5.md](steps/step_5.md)** - Quality Checks and Validation
   - Run pylint, pytest, mypy (all must pass)
   - Fix any issues found
   - Verify all requirements met
   - **Est. Time:** 30-45 minutes

---

## 🎯 Key Design Principles

### **KISS Principle Applied:**
- ✅ 3 source files instead of 5 (merged config, exceptions into client.py)
- ✅ Lazy validation (no connection test on init)
- ✅ Let python-jenkins handle job path validation
- ✅ Consolidated test files

### **Test-Driven Development:**
- Write tests FIRST
- Implement to pass tests
- Run quality checks after each step

### **Mandatory MCP Tool Usage:**
- `mcp__filesystem__save_file` - Create new files
- `mcp__filesystem__edit_file` - Modify existing files
- `mcp__code-checker__run_pylint_check` - Linting
- `mcp__code-checker__run_pytest_check` - Testing
- `mcp__code-checker__run_mypy_check` - Type checking

---

## 📁 Files to Create

### **Source Files (3 new):**
1. `src/mcp_coder/utils/jenkins_operations/__init__.py`
2. `src/mcp_coder/utils/jenkins_operations/models.py`
3. `src/mcp_coder/utils/jenkins_operations/client.py`

### **Test Files (4 new):**
4. `tests/utils/jenkins_operations/__init__.py`
5. `tests/utils/jenkins_operations/test_models.py`
6. `tests/utils/jenkins_operations/test_client.py`
7. `tests/utils/jenkins_operations/test_integration.py`

### **Files to Modify (2 existing):**
8. `pyproject.toml` - Add `jenkins_integration` marker
9. `src/mcp_coder/utils/__init__.py` - Add jenkins_operations exports

**Total:** 7 new files, 2 modified files

---

## ✅ Success Criteria

### **Functionality:**
- ✅ Start Jenkins jobs and get queue ID
- ✅ Check job status with detailed information
- ✅ Get queue summary (running/queued counts)
- ✅ Configuration from `~/.mcp_coder/config.toml`
- ✅ Environment variable overrides

### **Code Quality:**
- ✅ Pylint: 10.00/10 (no errors)
- ✅ Pytest: All tests pass (~30 unit tests)
- ✅ Mypy: No type errors
- ✅ Type hints throughout
- ✅ Comprehensive docstrings

### **Testing:**
- ✅ Unit tests with mocked python-jenkins
- ✅ Integration tests with `@pytest.mark.jenkins_integration`
- ✅ Tests skip gracefully when not configured

### **Architecture:**
- ✅ Follows existing patterns (git_operations, github_operations)
- ✅ Proper error handling with custom exceptions
- ✅ Structured logging with `structlog`
- ✅ Clean public API

---

## 🚀 Getting Started

### **For Implementation:**

1. Read `steps/summary.md` for complete overview
2. Start with `steps/step_1.md` (models + tests)
3. Follow each step in order
4. Run quality checks after each step
5. Fix any issues before moving to next step

### **For Code Review:**

1. Read `steps/summary.md` for architecture decisions
2. Review implementation against step requirements
3. Verify all quality checks pass
4. Check that requirements from issue #136 are met

---

## 📖 Reference Information

### **Issue:**
- **Number:** #136
- **Title:** Add Jenkins Job Automation Support
- **Branch:** `136-jenkins-jobs-triggering---from-python`

### **Related Documentation:**
- `docs/architecture/ARCHITECTURE.md` - Project architecture
- `.claude/CLAUDE.md` - Project coding guidelines
- `pyproject.toml` - Project configuration

### **Similar Patterns:**
- `src/mcp_coder/utils/git_operations/` - Modular utility package
- `src/mcp_coder/utils/github_operations/` - API client pattern
- `tests/utils/github_operations/test_github_integration_smoke.py` - Integration test pattern

---

## 💡 Tips for LLMs

### **When Implementing:**
1. Always read the step file first
2. Use the provided LLM prompt at the top of each step
3. Follow TDD: tests first, then implementation
4. Use MCP tools exclusively (no Bash for code operations)
5. Run quality checks after each step

### **When Stuck:**
1. Review `steps/summary.md` for context
2. Check similar patterns in existing code
3. Read error messages carefully
4. Use `mcp__filesystem__read_file` to inspect existing code

### **Quality Check Commands:**
```python
# Pylint
mcp__code-checker__run_pylint_check(
    target_directories=["src/mcp_coder/utils/jenkins_operations"]
)

# Pytest (unit tests only)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-v", "tests/utils/jenkins_operations/"]
)

# Mypy
mcp__code-checker__run_mypy_check(
    target_directories=["src/mcp_coder/utils/jenkins_operations"]
)
```

---

## 📊 Estimated Effort

- **Total Implementation Time:** 2.5-4 hours
- **Code Volume:** ~500-600 lines
- **Test Coverage:** ~30 unit tests + 2 integration tests
- **Complexity:** Low-Medium (following existing patterns)

---

## ✨ All CLAUDE.md requirements followed

This implementation plan strictly adheres to all requirements from `.claude/CLAUDE.md`:
- ✅ Uses MCP tools exclusively
- ✅ All code quality checks mandatory
- ✅ Test-driven development approach
- ✅ Follows existing project patterns
- ✅ KISS principle applied throughout
