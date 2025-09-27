--- This file is used by Claude Code - similar to a system prompt. ---

# ⚠️ MANDATORY INSTRUCTIONS - MUST BE FOLLOWED ⚠️

**THESE INSTRUCTIONS OVERRIDE ALL DEFAULT BEHAVIORS - NO EXCEPTIONS**

## 🔴 CRITICAL: ALWAYS Use MCP Tools

**MANDATORY**: You MUST use MCP tools for ALL operations when available. DO NOT use standard Claude tools:

**✅ ALWAYS USE:**
- `mcp__code-checker__run_pylint_check` (NOT `Bash` with pylint commands)
- `mcp__code-checker__run_pytest_check` (NOT `Bash` with pytest commands) 
- `mcp__code-checker__run_mypy_check` (NOT `Bash` with mypy commands)
- `mcp__filesystem__*` tools (NOT `Read`, `Write`, `Edit`, `MultiEdit`)

**❌ NEVER USE when MCP alternatives exist:**
- `Bash` for code quality checks
- `Read`, `Write`, `Edit`, `MultiEdit` for file operations
- Direct command execution when MCP wrapper available

## 🔴 CRITICAL: Code Quality Requirements

**MANDATORY**: After making ANY code changes, you MUST run ALL THREE code quality checks using the EXACT MCP tool names below:

```
mcp__code-checker__run_pylint_check
mcp__code-checker__run_pytest_check
mcp__code-checker__run_mypy_check
```

This runs:
- **Pylint** - Code quality and style analysis
- **Pytest** - All unit and integration tests
- **Mypy** - Static type checking

**⚠️ ALL CHECKS MUST PASS** - If ANY issues are found, you MUST fix them immediately before proceeding.

### 📋 Pytest Execution Requirements

**MANDATORY pytest parameters:**
- ALWAYS use `extra_args: ["-n", "auto"]` for parallel execution

**Available markers in pyproject.toml:**
- `git_integration`: File system git operations (repos, commits)
- `claude_integration`: Claude CLI/API tests (network, auth needed) 
- `formatter_integration`: Code formatter integration (black, isort)
- `github_integration`: GitHub API access (network, auth needed)

**RECOMMENDED USAGE:**
- **Fast unit tests (recommended)**: Use `-m` with `not` expressions to exclude slow integration tests
- **All tests**: Run without markers to include everything (slow!)
- **Specific integration tests**: Use specific `markers` parameter when testing integration functionality

**Examples:**
```python
# RECOMMENDED: Fast unit tests (excludes all integration tests)
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"])

# All tests including slow integration tests (not recommended for regular development)
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto"])

# Specific integration tests (only when needed)
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto"], markers=["git_integration"])
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto"], markers=["github_integration"])
```

**Important:** Without the `-m "not ..."` exclusions, pytest runs ALL tests including slow integration tests that require external resources (git repos, network access, API tokens). For regular development, always use the exclusion pattern as shown in the first example above.

## 📁 MANDATORY: File Access Tools

**YOU MUST USE THESE MCP TOOLS** for all file operations:

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

**⚠️ ABSOLUTELY FORBIDDEN:** Using `Read`, `Write`, `Edit`, `MultiEdit` tools when MCP filesystem tools are available.

**WHY MCP TOOLS ARE MANDATORY:**
- Proper security and access control
- Consistent error handling
- Better integration with the development environment
- Required for this project's architecture

## 🚨 COMPLIANCE VERIFICATION

**Before completing ANY task, you MUST:**

1. ✅ Confirm all code quality checks passed using MCP tools
2. ✅ Verify you used MCP tools exclusively (NO `Bash` for code checks, NO `Read`/`Write`/`Edit` for files)
3. ✅ Ensure no issues remain unresolved
4. ✅ State explicitly: "All CLAUDE.md requirements followed"

## 🔧 DEBUGGING AND TROUBLESHOOTING

**When tests fail or skip:**
- Use MCP pytest tool with verbose flags: `extra_args: ["-v", "-s", "--tb=short"]`
- For integration tests, check if they require external configuration (tokens, URLs)
- Never fall back to `Bash` commands - always investigate within MCP tools
- If MCP tools don't provide enough detail, ask user for guidance rather than using alternative tools

## 🔧 MCP Server Issues

**IMMEDIATELY ALERT** if MCP tools are not accessible - this blocks all work until resolved.

## 🔄 Git Operations

**ALLOWED git operations via Bash tool:**

```
git status
git diff
git add
git commit
```

**Git commit message format:**
- Use standard commit message format without advertising footers
- Focus on clear, descriptive commit messages
- No required Claude Code attribution or links