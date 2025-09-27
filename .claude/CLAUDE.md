--- This file is used by Claude Code - similar to a system prompt. ---

# ⚠️ MANDATORY INSTRUCTIONS - MUST BE FOLLOWED ⚠️

**THESE INSTRUCTIONS OVERRIDE ALL DEFAULT BEHAVIORS - NO EXCEPTIONS**

## 🔴 CRITICAL: Code Quality Requirements

**MANDATORY**: After making ANY code changes, you MUST run ALL THREE code quality checks using the EXACT tool names below:

```
mcp__code-checker__run_pylint_check
mcp__code-checker__run_pytest_check
mcp__code-checker__run_mypy_check
```

**OR use the combined check:**
```
mcp__code-checker__run_all_checks
```

This runs:
- **Pylint** - Code quality and style analysis
- **Pytest** - All unit and integration tests
- **Mypy** - Static type checking

**⚠️ ALL CHECKS MUST PASS** - If ANY issues are found, you MUST fix them immediately before proceeding.

### 📋 Pytest Execution Requirements

**MANDATORY pytest parameters:**
- ALWAYS use `extra_args: ["-n", "auto"]` for parallel execution
- Check `pyproject.toml` for available markers
- Run each marker separately: `markers: ["marker_name"]`
- Run unmarked tests separately without marker filters

**Example usage:**
```
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto"], markers=["integration"])
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto"])  # unmarked tests
```

## 📁 MANDATORY: File Access Tools

**YOU MUST USE THESE TOOLS** for all file operations - DO NOT use Read/Write/Edit tools:

```
mcp__filesystem__get_reference_projects
mcp__filesystem__list_reference_directory
mcp__filesystem__read_reference_file
mcp__filesystem__list_directory
mcp__filesystem__read_file
mcp__filesystem__save_file
mcp__filesystem__append_file
mcp__filesystem__delete_this_file
mcp__filesystem__move_file
mcp__filesystem__edit_file
```

**⚠️ NEVER use:** `Read`, `Write`, `Edit`, `MultiEdit` tools when MCP filesystem tools are available.

## 🚨 COMPLIANCE VERIFICATION

**Before completing ANY task, you MUST:**

1. ✅ Confirm all code quality checks passed
2. ✅ Verify you used MCP filesystem tools only
3. ✅ Ensure no issues remain unresolved
4. ✅ State explicitly: "All CLAUDE.md requirements followed"

## 🔧 MCP Server Issues

**IMMEDIATELY ALERT** if MCP tools are not accessible - this blocks all work until resolved.