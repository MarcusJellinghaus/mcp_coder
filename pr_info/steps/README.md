# Implementation Steps Quick Reference

## Overview
Refactor LLM modules for better separation of concerns - 11 incremental, testable steps.

## Steps Summary

| Step | Title | Focus | Risk | Lines |
|------|-------|-------|------|-------|
| 1 | Create Package Structure | Setup directories | Low | - |
| 2 | Move Core Modules | Move types, interface, serialization | Low | - |
| 3 | Move Providers | Move llm_providers/ | Low | - |
| 4 | Extract SDK Utilities | Extract 5 functions to formatting | Medium | ~200 |
| 5 | Extract Formatters | Extract 3 formatters | Medium | ~300 |
| 6 | Extract Storage | Extract storage/finder functions | Medium | ~200 |
| 7 | Extract Session Logic | Move parse_llm_method | Low | ~50 |
| 8 | Move Core Tests | Reorganize test structure | Medium | - |
| 9 | Extract Formatting Tests | Extract formatting tests | Medium | ~300 |
| 10 | Extract Storage Tests | Extract storage/session tests | Medium | ~400 |
| 11 | Final Verification | Verify, document, cleanup | Critical | - |

## Progress Tracking

Use this checklist to track implementation progress:

```
[ ] Step 1: Create Package Structure
[ ] Step 2: Move Core Modules  
[ ] Step 3: Move Providers
[ ] Step 4: Extract SDK Utilities
[ ] Step 5: Extract Formatters
[ ] Step 6: Extract Storage
[ ] Step 7: Extract Session Logic
[ ] Step 8: Move Core Tests
[ ] Step 9: Extract Formatting Tests
[ ] Step 10: Extract Storage Tests
[ ] Step 11: Final Verification
```

## Key Principles

1. **TDD**: Run tests after every step
2. **KISS**: Keep it simple - just move code
3. **Incremental**: Each step is self-contained
4. **Reversible**: Easy to rollback each step
5. **Zero Behavior Changes**: Pure refactoring only

## Expected Outcomes

### Code Reduction
- `prompt.py`: 800 → 100 lines (87% reduction)
- `test_prompt.py`: 800 → 200 lines (75% reduction)

### Structure
```
Before:                          After:
llm_types.py                    llm/
llm_interface.py                ├── types.py
llm_serialization.py            ├── interface.py  
llm_providers/                  ├── serialization.py
cli/llm_helpers.py              ├── formatting/
cli/commands/prompt.py (800)    ├── storage/
                                ├── session/
                                └── providers/
                                cli/commands/prompt.py (100)
```

### Test Organization
```
Before:                          After:
test_llm_*.py                   llm/
llm_providers/                  ├── test_types.py
test_prompt.py (800)            ├── test_interface.py
test_prompt_sdk_utilities.py    ├── formatting/
                                ├── storage/
                                ├── session/
                                └── providers/
                                cli/commands/test_prompt.py (200)
```

## Quick Commands

### After Each Step
```bash
# Run tests
pytest tests/ -v

# Check imports
python -c "from mcp_coder.llm import ask_llm; print('✓ OK')"

# Count lines
wc -l src/mcp_coder/cli/commands/prompt.py
```

### Final Verification
```bash
# Complete test suite
pytest tests/ -v

# Static analysis
pylint src/mcp_coder/llm/
mypy src/mcp_coder/llm/

# Manual CLI test
mcp-coder prompt "test" --verbosity=verbose
```

## LLM Prompt Template

For each step, use this template:

```
I'm implementing Step [N] of the LLM module refactoring.

Reference: pr_info/steps/summary.md and pr_info/steps/step_[N].md

Task: [Brief description from step file]

Please follow the implementation details in step_[N].md exactly.

After implementation, run the verification tests specified in the step.
```

## Success Criteria

- [ ] All tests pass (100%)
- [ ] `prompt.py` < 150 lines
- [ ] `test_prompt.py` < 250 lines
- [ ] Static analysis passes
- [ ] CLI behavior unchanged
- [ ] Documentation updated
- [ ] Zero regressions
