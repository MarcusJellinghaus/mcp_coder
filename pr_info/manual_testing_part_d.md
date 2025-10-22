# Part D: Manual Functional Testing Guide

## Overview
This guide provides manual tests to verify the `create-pr` CLI command works correctly.

## Prerequisites
- Ensure you're in the virtual environment where mcp-coder is installed
- Be in the mcp_coder project directory

## Test 1: Verify Main Help Shows create-pr Command

**Command:**
```bash
mcp-coder --help
```

**Expected Output:**
- Should see "create-pr" in the list of available commands
- Look for a line like: `create-pr              Create pull request with AI-generated summary`

**Pass Criteria:**
✅ The word "create-pr" appears in the output  
✅ Has a description about creating pull requests  

---

## Test 2: Verify create-pr Specific Help

**Command:**
```bash
mcp-coder create-pr --help
```

**Expected Output:**
```
usage: mcp-coder create-pr [-h] [--project-dir PROJECT_DIR] [--llm-method METHOD]

Create pull request with AI-generated summary

optional arguments:
  -h, --help            show this help message and exit
  --project-dir PROJECT_DIR
                        Project directory path (default: current directory)
  --llm-method METHOD   LLM method to use (default: claude_code_cli)
```

**Pass Criteria:**
✅ Shows usage information without errors  
✅ Lists `--project-dir` option  
✅ Lists `--llm-method` option with choices (claude_code_cli, claude_code_api)  
✅ Shows default values  
✅ No import errors or exceptions  

---

## Test 3: Test Command Accessibility (No Import Errors)

**Command:**
```bash
mcp-coder create-pr --help
```

**Pass Criteria:**
✅ Command executes without Python import errors  
✅ No `ModuleNotFoundError` or `ImportError`  
✅ No `AttributeError` about missing functions  
✅ Help text displays correctly  

---

## Test 4: Verify Error Handling (Optional)

**Command:**
```bash
mcp-coder create-pr --project-dir /nonexistent/path
```

**Expected Behavior:**
- Should show a clear error message about invalid project directory
- Should exit with non-zero exit code
- Should NOT crash with unhandled exception

**Pass Criteria:**
✅ Shows user-friendly error message  
✅ Exits gracefully (no stack trace)  

---

## Code Review Verification ✅

**Already verified through code inspection:**

1. ✅ **Command registered in main.py** (lines 244-256)
   - Subcommand name: `create-pr`
   - Help text: "Create pull request with AI-generated summary"
   - Arguments: `--project-dir`, `--llm-method`

2. ✅ **Command routing in main.py** (line 301)
   - Routes to `execute_create_pr(args)`

3. ✅ **Implementation in create_pr.py**
   - Imports workflow: `run_create_pr_workflow`
   - Uses shared utilities: `resolve_project_dir`, `parse_llm_method_from_args`
   - Proper error handling
   - Returns binary exit codes

4. ✅ **Import chain verified**
   - All imports are correct
   - No circular dependencies
   - All modules exist

---

## Summary

**Tests to Run:**
1. ✅ `mcp-coder --help` (shows create-pr)
2. ✅ `mcp-coder create-pr --help` (displays options)
3. ✅ No import errors when accessing command

**Code Verification Complete:**
- All implementation is in place
- All imports are correct
- Error handling is proper
- Integration with CLI main is correct

---

## Testing Instructions for User

Please run the following commands in your terminal:

```bash
# Activate virtual environment (if not already active)
# On Windows:
.venv\Scripts\activate

# Test 1: Check main help
mcp-coder --help | findstr "create-pr"

# Test 2: Check create-pr specific help
mcp-coder create-pr --help

# Test 3: Verify no import errors (same as Test 2)
mcp-coder create-pr --help
```

After running these commands, confirm:
- [ ] Test 1 shows "create-pr" in output
- [ ] Test 2 displays help without errors
- [ ] Test 3 shows no import errors

If all tests pass, Part D is complete! ✅
