# Implementation Steps Index

Implementation plan for Issue #149: `mcp-coder coordinator test` Command

## Overview

This directory contains a step-by-step implementation plan following **Test-Driven Development (TDD)** and **KISS principle** for adding Jenkins-based integration testing to MCP Coder.

## Quick Navigation

- **[Summary](summary.md)** - Architecture overview, design decisions, file structure
- **[Step 1](step_1.md)** - Config Template Infrastructure (TDD)
- **[Step 2](step_2.md)** - Repository Config Validation (TDD)
- **[Step 3](step_3.md)** - CLI Command Core Logic (TDD)
- **[Step 4](step_4.md)** - CLI Integration (TDD)
- **[Step 5](step_5.md)** - Documentation & Integration Tests

## Implementation Phases

### Phase 1: Config Template Infrastructure
**File:** `step_1.md`  
**Focus:** Config file auto-creation  
**Lines:** ~120-150  
**Tests:** 6 tests for config template creation

### Phase 2: Repository Config Validation
**File:** `step_2.md`  
**Focus:** Validation helpers and error messages  
**Lines:** ~300-380  
**Tests:** 15 tests for validation logic

### Phase 3: CLI Command Core Logic
**File:** `step_3.md`  
**Focus:** Main command execution  
**Lines:** ~180-230  
**Tests:** 9 tests for command execution

### Phase 4: CLI Integration
**File:** `step_4.md`  
**Focus:** Argument parsing and routing  
**Lines:** ~105-130  
**Tests:** 5 tests for CLI integration

### Phase 5: Documentation & Integration Tests
**File:** `step_5.md`  
**Focus:** CONFIG.md, README, integration tests  
**Lines:** ~390-520  
**Tests:** Integration tests (marked `jenkins_integration`)

## Total Implementation Size

| Component | Lines of Code |
|-----------|---------------|
| Step 1: Config template | ~120-150 |
| Step 2: Validation | ~300-380 |
| Step 3: Command core | ~180-230 |
| Step 4: CLI integration | ~105-130 |
| Step 5: Documentation | ~390-520 |
| **Total** | **~1,095-1,410** |

**Note:** This includes comprehensive tests (~50% of total lines are tests)

**Production code only:** ~500-650 lines

## How to Use This Plan

### For LLM Implementation:

Each step has a dedicated **LLM Prompt** section at the top. Use this exact prompt when implementing:

```
Read pr_info/steps/summary.md for context.
Read pr_info/steps/step_X.md for this step.
Implement following the specifications exactly.
```

### For Human Developers:

1. Read `summary.md` first for architecture overview
2. Implement steps sequentially (1 → 2 → 3 → 4 → 5)
3. Follow TDD: Write tests FIRST, then implementation
4. Run code quality checks after each step
5. Don't proceed to next step until all checks pass

## Step-by-Step Process

### For Each Step:

1. **Read** - Review step file completely
2. **Test First** - Write all tests (TDD approach)
3. **Implement** - Write implementation to pass tests
4. **Verify** - Run tests and verify they pass
5. **Quality** - Run pylint, pytest, mypy
6. **Next** - Only proceed if all checks pass

### Example Workflow (Step 1):

```bash
# 1. Read step file
cat pr_info/steps/step_1.md

# 2. Write tests first (TDD)
# Edit: tests/utils/test_user_config.py

# 3. Run tests (should fail - no implementation yet)
pytest tests/utils/test_user_config.py::TestCreateDefaultConfig -v

# 4. Implement functionality
# Edit: src/mcp_coder/utils/user_config.py

# 5. Run tests again (should pass now)
pytest tests/utils/test_user_config.py::TestCreateDefaultConfig -v

# 6. Run code quality checks
mcp-coder verify  # or use MCP tools directly

# 7. Proceed to Step 2
```

## Code Quality Requirements

Every step must pass:

✅ **Pylint** - No errors  
✅ **Pytest** - All tests pass (fast unit tests)  
✅ **Mypy** - No type errors  

Use MCP code-checker tools:
```python
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not jenkins_integration and not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
mcp__code-checker__run_mypy_check()
```

## Files to Create

### New Files (2):
```
src/mcp_coder/cli/commands/coordinator.py
tests/cli/commands/test_coordinator.py
docs/configuration/CONFIG.md
```

### Modified Files (3):
```
src/mcp_coder/utils/user_config.py
src/mcp_coder/cli/main.py
README.md
```

## Design Principles

### KISS (Keep It Simple, Stupid)
- ✅ Minimal new files (2 vs 6+ in complex approach)
- ✅ No package restructuring
- ✅ Direct integration with existing code
- ✅ Simple dict-based config (no heavy dataclasses)

### TDD (Test-Driven Development)
- ✅ Tests written FIRST for every step
- ✅ Red → Green → Refactor cycle
- ✅ Comprehensive test coverage (>80%)

### DRY (Don't Repeat Yourself)
- ✅ Reuse existing JenkinsClient
- ✅ Reuse existing user_config utilities
- ✅ Follow existing command patterns

## Testing Strategy

### Unit Tests (Fast):
- Mock all external dependencies
- No network calls
- No file system operations (use tmp_path)
- Run in parallel with `-n auto`

### Integration Tests (Slow):
- Marked with `@pytest.mark.jenkins_integration`
- Skip if Jenkins not configured
- Can trigger real Jenkins jobs
- Run separately or in CI

## Success Metrics

### Functional:
- [ ] Command works end-to-end
- [ ] Config auto-creation works
- [ ] Validation catches all errors
- [ ] Job triggering works
- [ ] Output format correct

### Quality:
- [ ] >80% test coverage
- [ ] All pylint checks pass
- [ ] All pytest tests pass
- [ ] All mypy checks pass

### Documentation:
- [ ] CONFIG.md complete
- [ ] README.md updated
- [ ] All examples work

## Comparison: Simple vs Complex Approach

| Aspect | This Plan (Simple) | Original Plan (Complex) |
|--------|-------------------|------------------------|
| New files | 2 | 6+ |
| Code changes | ~500-650 lines | ~800-1000 lines |
| Package restructuring | No | Yes (config/) |
| Dataclass models | No | Yes |
| Workflow package | No | Yes |
| Import updates | 0 | 7+ files |
| Complexity | Low | High |
| Maintenance | Easy | Harder |

**Savings:** ~40% less code, 67% fewer files, no breaking changes

## Timeline Estimate

| Step | Description | Time |
|------|-------------|------|
| 1 | Config template | ~1 hour |
| 2 | Validation logic | ~1.5 hours |
| 3 | CLI command | ~2 hours |
| 4 | CLI integration | ~1 hour |
| 5 | Documentation | ~2 hours |
| **Total** | | **~7.5 hours** |

## Dependencies

### Existing (Reused):
- ✅ `JenkinsClient` from `utils/jenkins_operations/`
- ✅ `get_config_value()` from `utils/user_config.py`
- ✅ Existing CLI command patterns

### New (None):
- ❌ No new external dependencies
- ❌ No new packages required

## Related Documentation

- **Issue #149** - Original GitHub issue with requirements
- **ARCHITECTURE.md** - System architecture documentation
- **CLAUDE.md** - Project-specific Claude instructions
- **README.md** - User-facing documentation

## Questions?

If anything is unclear:
1. Check `summary.md` for architecture overview
2. Check specific step file for details
3. Look at existing code for patterns
4. Refer to issue #149 for original requirements

## Let's Begin!

Start with **[summary.md](summary.md)** to understand the big picture, then proceed to **[step_1.md](step_1.md)** to begin implementation.

Good luck! 🚀
