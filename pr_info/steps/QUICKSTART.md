# Quick Start: Implementing GitHub Labels Manager

## 📋 Overview
Simple 4-step TDD implementation to add labels management to existing GitHub operations.

## 🎯 Implementation Order

### Step 1: Unit Tests (Red Phase)
**File**: `pr_info/steps/step_1.md`
- Add `TestLabelsManagerUnit` class to `tests/utils/test_github_operations.py`
- 5 validation tests (initialization, label names, colors)
- **Expected**: Tests FAIL (no implementation yet)

### Step 2: Implementation (Green Phase)
**File**: `pr_info/steps/step_2.md`
- Create `src/mcp_coder/utils/github_operations/labels_manager.py`
- Implement `LabelsManager.__init__()` and validation methods
- Update exports in `__init__.py`
- **Expected**: Step 1 tests PASS

### Step 3: Integration Tests (Red Phase)
**File**: `pr_info/steps/step_3.md`
- Add `TestLabelsManagerIntegration` class to test file
- Add `labels_manager` fixture
- Full lifecycle test (create, list, delete)
- **Expected**: Tests FAIL (CRUD methods not implemented)

### Step 4: CRUD Implementation (Green Phase)
**File**: `pr_info/steps/step_4.md`
- Implement `get_labels()`, `create_label()`, `update_label()`, `delete_label()`
- Add `@log_function_call` decorators
- **Expected**: ALL tests PASS ✅

## 🚀 Using the Implementation Plan

Each step file contains an **LLM Prompt** section. Use it like this:

```bash
# 1. Read the step file
cat pr_info/steps/step_1.md

# 2. Copy the "LLM Prompt" section at the bottom

# 3. Paste into Claude Code or your AI assistant

# 4. Run tests to verify
pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
```

## ✅ Verification Checklist

After each step:
```bash
# Step 1: Unit tests exist and fail
pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
# Expected: 5 FAILED

# Step 2: Unit tests pass
pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
# Expected: 5 PASSED

# Step 3: Integration tests exist and fail
pytest tests/utils/test_github_operations.py::TestLabelsManagerIntegration -v -m github_integration
# Expected: 1 FAILED (requires GitHub config)

# Step 4: All tests pass
pytest tests/utils/test_github_operations.py -k "LabelsManager" -v
# Expected: 6 PASSED (5 unit + 1 integration)
```

## 📦 What Gets Created

**New Files** (1):
- `src/mcp_coder/utils/github_operations/labels_manager.py` (~200 lines)

**Modified Files** (2):
- `src/mcp_coder/utils/github_operations/__init__.py` (2 lines added)
- `tests/utils/test_github_operations.py` (~150 lines added)

**Documentation** (7 files in `pr_info/steps/`):
- `summary.md` - Overview and architecture
- `step_1.md` through `step_4.md` - Detailed steps
- `README.md` - This file
- `FILES.md` - Complete file manifest

## ⚙️ Configuration Required

For integration tests only (unit tests work without):

```toml
# ~/.mcp_coder/config.toml
[github]
token = "ghp_your_personal_access_token_here"
test_repo_url = "https://github.com/your-username/test-repo"
```

## 🎓 Learning Path

1. **Read** `summary.md` first - understand the big picture
2. **Follow** steps 1-4 sequentially - each builds on previous
3. **Test** after each step - verify green/red phases
4. **Reference** existing code - `pr_manager.py` is the template

## 💡 Key Principles

- ✅ **KISS**: Keep it simple - only essential operations
- ✅ **TDD**: Tests first, then implementation
- ✅ **Reuse**: Mirror existing PullRequestManager patterns
- ✅ **Minimal**: No new dependencies, no architectural changes

## 🔗 Related Documentation

- Architecture: `docs/architecture/ARCHITECTURE.md`
- Existing PR Manager: `src/mcp_coder/utils/github_operations/pr_manager.py`
- Existing Tests: `tests/utils/test_github_operations.py`

---

**Ready to start?** Begin with `pr_info/steps/step_1.md` 🚀
