# Implementation Plan: Fix VSCodeClaude Test Dependencies

## Quick Reference

**Issue**: #411 - coordinator vscodeclaude does not install test dependencies  
**Solution**: Change `--extra types` to `--extra dev` in VENV_SECTION_WINDOWS template  
**Impact**: Minimal - one line change in one file  

## Files Modified

### Production Code
- `src/mcp_coder/workflows/vscodeclaude/templates.py` (1 line change)

### Test Code
- `tests/workflows/vscodeclaude/test_templates.py` (new file, ~20 lines)

## Step Sequence

### Step 1: Write Test (TDD Red Phase)
**File**: `pr_info/steps/step_1.md`  
**Action**: Create test that verifies template uses `--extra dev`  
**Result**: Test FAILS (expected - implementation not done yet)  
**Time**: ~5 minutes  

### Step 2: Fix Implementation (TDD Green Phase)
**File**: `pr_info/steps/step_2.md`  
**Action**: Change `uv sync --extra types` to `uv sync --extra dev`  
**Result**: Test PASSES  
**Time**: ~2 minutes  

### Step 3: Verify and Test (TDD Refactor Phase)
**File**: `pr_info/steps/step_3.md`  
**Action**: Run full test suite, verify no regressions  
**Result**: All tests PASS  
**Time**: ~5 minutes  

## Total Effort
**Estimated Time**: ~15 minutes  
**Complexity**: Very Low  
**Risk**: Minimal  

## Quick Start

### For LLM Implementation
Each step has a self-contained LLM prompt at the top. Simply:
1. Read `summary.md` for context
2. Execute each step in order
3. Use the provided LLM prompt for that step

### For Manual Implementation
```bash
# Step 1: Create test
# See step_1.md for test code

# Step 2: Update template
# Change line 14 in templates.py: --extra types → --extra dev

# Step 3: Verify
pytest tests/workflows/vscodeclaude/test_templates.py -v
pytest tests/workflows/vscodeclaude/ -v
```

## Success Criteria
- ✅ Template contains `uv sync --extra dev`
- ✅ New test passes
- ✅ All existing tests pass
- ✅ Only one line changed in production code

## KISS Principles Applied
1. **Minimal Change**: One line in one template
2. **Simple Test**: Direct string assertion, no mocking
3. **No Over-Engineering**: No new abstractions or patterns
4. **Clear Intent**: Change is obvious and self-documenting
5. **Easy Rollback**: Single line to revert if needed

## Dependencies Installed After Fix

### Before (--extra types)
- Main dependencies
- Type stubs (types-* packages)

### After (--extra dev)
- Main dependencies
- Type stubs (types-* packages)
- **Test utilities** (pytest-asyncio, pytest-xdist) ← **FIXES ISSUE**
- MCP servers (mcp group - currently empty)
- Architecture tools (import-linter, pycycle, tach, vulture)

## See Also
- `summary.md` - Detailed overview and architectural context
- `step_1.md` - Test implementation details
- `step_2.md` - Template update details  
- `step_3.md` - Verification procedures
