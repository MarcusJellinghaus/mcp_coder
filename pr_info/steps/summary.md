# Summary: Subprocess Library Isolation (#357)

## Overview

Enforce an architectural constraint that all `subprocess` module usage must go through the centralized subprocess wrapper (`src/mcp_coder/utils/subprocess_runner.py`).

## Why This Matters

The subprocess wrapper provides critical functionality:
- **Timeout handling** with process tree cleanup (prevents orphaned processes)
- **Cross-platform compatibility** (Windows/Unix differences handled internally)
- **STDIO isolation** for Python commands (critical for MCP protocol)
- **UTF-8 encoding** with `errors="replace"` (prevents crashes on invalid characters)
- **Centralized logging** and error handling

Without enforcement, developers may accidentally use raw `subprocess` calls, bypassing these protections.

## Architectural Changes

### Before
```
Production Code ──┬──> subprocess_runner.py ──> subprocess
                  └──> subprocess (direct)     ← PROBLEM

Test Code ────────────> subprocess (direct)    ← PROBLEM
```

### After
```
Production Code ──────> subprocess_runner.py ──> subprocess ✓

Test Code ────────────> subprocess_runner.py ──> subprocess ✓
```

### Design Decisions

1. **Re-export exceptions**: `CalledProcessError`, `SubprocessError`, `TimeoutExpired` are re-exported from `subprocess_runner.py` so modules can catch these without importing `subprocess` directly.

2. **Import-linter enforcement**: A forbidden contract prevents any module (production or test) from importing `subprocess` except the wrapper itself.

3. **No fallback patterns**: Code that previously had fallback `subprocess.run()` calls will rely solely on `execute_command()`. The wrapper is robust enough.

## Scope

| Scope | Included |
|-------|----------|
| `src/` | All production code |
| `tests/` | All test files |
| `tools/` | **Exempt** (standalone scripts) |

## Files to Modify

### Production Code

| File | Change Type |
|------|-------------|
| `src/mcp_coder/utils/subprocess_runner.py` | Add exception re-exports |
| `src/mcp_coder/utils/git_operations/commits.py` | Use `execute_command()` |
| `src/mcp_coder/llm/providers/claude/claude_executable_finder.py` | Remove fallback subprocess calls |
| `src/mcp_coder/workflows/implement/task_processing.py` | Change import |
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | Change import |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Change import |
| `src/mcp_coder/formatters/black_formatter.py` | Change import |
| `src/mcp_coder/formatters/isort_formatter.py` | Change import |

### Test Code

| File | Change Type |
|------|-------------|
| `tests/utils/github_operations/test_issue_manager_label_update.py` | Use `execute_command()` |
| `tests/workflows/test_create_pr_integration.py` | Remove unused import |
| `tests/cli/test_main.py` | Remove unused import |
| `tests/utils/test_git_encoding_stress.py` | Delete redundant test |
| `tests/llm/providers/claude/test_claude_code_api.py` | Change import |
| `tests/llm/providers/claude/test_claude_code_api_error_handling.py` | Change import |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Change import |

### Configuration

| File | Change Type |
|------|-------------|
| `.importlinter` | Add subprocess isolation contract |

## Implementation Steps

1. **Step 1**: Re-export exceptions and migrate production code
2. **Step 2**: Migrate test files and add import-linter contract

## Acceptance Criteria

- [ ] Exception classes re-exported from `subprocess_runner.py`
- [ ] All production code uses wrapper or imports exceptions from wrapper
- [ ] All test code uses wrapper or imports exceptions from wrapper
- [ ] Import-linter contract enforces the constraint
- [ ] `lint-imports` passes
- [ ] All tests pass
