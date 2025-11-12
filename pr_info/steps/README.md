# Windows Support Implementation Plan - Overview

## Quick Start

This implementation plan adds Windows batch script support to coordinator commands using a simplified, test-driven approach.

## Implementation Steps

Execute in order:

1. **[summary.md](summary.md)** - Read this first for architecture overview
2. **[step_1.md](step_1.md)** - Add Windows template constants (no tests)
3. **[step_2.md](step_2.md)** - Update config loading and validation (TDD)
4. **[step_3.md](step_3.md)** - Add template selection logic (TDD)
5. **[step_4.md](step_4.md)** - Update default config template (no tests)
6. **[step_5.md](step_5.md)** - Integration validation and final testing

## Key Principles

- **KISS**: Minimal changes, no unnecessary complexity
- **TDD**: Write tests first, then implement (Steps 2-3)
- **Backward Compatible**: Defaults to Linux, no breaking changes
- **Self-Contained**: Each step has complete implementation instructions

## Files Modified

### Implementation Files (3 files)
1. `src/mcp_coder/cli/commands/coordinator.py` - Add templates and selection logic
2. `src/mcp_coder/utils/user_config.py` - Update config template
3. `tests/cli/commands/test_coordinator.py` - Add validation tests

### Documentation Files (7 files)
1. `pr_info/steps/README.md` (this file)
2. `pr_info/steps/summary.md` - Architecture overview
3. `pr_info/steps/step_1.md` - Template constants
4. `pr_info/steps/step_2.md` - Config loading (TDD)
5. `pr_info/steps/step_3.md` - Template selection (TDD)
6. `pr_info/steps/step_4.md` - Config template
7. `pr_info/steps/step_5.md` - Final validation

## Architecture Summary

### New Configuration Field
```toml
[coordinator.repos.my_repo]
executor_os = "windows"  # or "linux" (default)
```

### Template Selection
```python
if executor_os == "windows":
    template = WINDOWS_TEMPLATE
else:
    template = LINUX_TEMPLATE  # default
```

## Implementation Time Estimate

- **Step 1**: 10 minutes (copy-paste templates)
- **Step 2**: 20 minutes (TDD: tests + config validation)
- **Step 3**: 30 minutes (TDD: tests + template selection)
- **Step 4**: 5 minutes (update config template)
- **Step 5**: 15 minutes (run all quality checks)

**Total**: ~1.5 hours

## Quality Gates

Each step must pass:
- ✅ Pylint (code quality)
- ✅ Pytest (all tests)
- ✅ Mypy (type checking)

## Using the Implementation Plan

### For AI/LLM Implementation

Each step includes a complete **LLM Prompt** at the end. Simply:
1. Read summary.md
2. Read the specific step file
3. Copy the LLM prompt to your AI assistant
4. Execute and validate

### For Manual Implementation

Each step includes:
- **WHERE**: Exact file paths and line numbers
- **WHAT**: Function signatures and data structures
- **HOW**: Integration points and imports
- **ALGORITHM**: Pseudocode for logic (when applicable)
- **DATA**: Return values and structures

## Success Criteria

Implementation is complete when:
1. All tests pass (pytest)
2. All quality checks pass (pylint, mypy)
3. Windows templates selected when `executor_os = "windows"`
4. Linux templates selected by default
5. Invalid `executor_os` values rejected with clear error
6. Config template documents new field
7. No regressions in existing functionality

## Validation Commands

```bash
# Run tests (excluding slow integration tests)
mcp-coder coordinator test mcp_coder main

# Verify config generation
rm ~/.config/mcp_coder/config.toml  # Remove old config
mcp-coder coordinator test mcp_coder main  # Triggers new config creation
cat ~/.config/mcp_coder/config.toml  # Verify executor_os in template
```

## Rollback Plan

If issues occur:
1. Revert changes to modified files
2. Config field is optional (defaults to "linux")
3. No database migrations or breaking changes

## Support

- **Issue**: #174
- **Documentation**: See `summary.md` for detailed architecture
- **Questions**: Each step has complete implementation details
