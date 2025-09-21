# Performance Test Management - Complete Workflow

## Quick Start Guide

### Step 1: Gather Slow Test Data
```cmd
.\tools\pytest_wf_1_gather_slow_tests.bat
```
This creates an output file in `tests\performance_management\output\` with slow test data.

### Step 2: Analyze with LLM
Copy the output from Step 1 and use this prompt:

**LLM Prompt:**
```
Analyze this pytest duration output and provide:

[PASTE PYTEST DURATION OUTPUT HERE]

1. **Top 10 Slowest Tests**: List with execution times and likely causes (integration, file I/O, etc.)
2. **Optimization Recommendations**: Specific suggestions for the slowest tests
3. **Marker Strategy**: Use markers defined in pyproject.toml for categorizing tests
4. **Priority Assessment**: Which tests to optimize first (high impact, low effort)

Format with clear sections and actionable recommendations.
```

### Step 3: Analyze Test Markers
```cmd
.\tools\pytest_wf_4_analyze_markers.bat
```

### Step 4: Update Documentation
Update `slow_tests_inventory.md` with:
- Discovered slow tests and execution times
- Recommended markers and categories
- Optimization priorities

### Step 5: Implement & Validate
```cmd
.\tools\pytest_wf_10_validate_improvements.bat
```

## Advanced Analysis Prompts

### For Specific Test Code Analysis
```
Analyze this slow test code and suggest optimizations:

TEST: [test_name] 
TIME: [execution_time]
CODE:
```python
[paste test code here]
```

Provide:
1. What makes this test slow
2. Specific optimization strategies
3. Appropriate pytest markers
4. Code refactoring options
```

### For Infrastructure Analysis
```
Analyze our test infrastructure for performance issues:

CONFTEST.PY:
[paste conftest.py content]

SLOW TEST PATTERNS:
[paste common patterns from slow tests]

Provide:
1. Expensive setup/teardown operations
2. Fixture optimization opportunities (scope, caching)
3. Test organization improvements
4. Priority order for changes
```

## Recommended Marker Strategy

Use the markers defined in `pyproject.toml`:
- See `[tool.pytest.ini_options]` section for current marker definitions
- Add appropriate markers to slow tests based on their category
- Follow the usage comments in pyproject.toml for CI exclusion patterns

## CI Integration Commands

Use the patterns defined in `pyproject.toml`:

```cmd
# Fast CI (exclude integration tests) - as documented in pyproject.toml
pytest -m "not git_integration and not claude_integration"

# Full test run
pytest

# Run specific integration test groups
pytest -m "git_integration"
pytest -m "claude_integration"
pytest -m "git_integration or claude_integration"
```

## Files to Update

1. **slow_tests_inventory.md** - Add discovered slow tests with details
2. **performance_analysis.md** - Document findings and recommendations
3. **Test files** - Add appropriate markers to slow tests

## Success Metrics

- Reduced overall test suite execution time
- Proper test categorization with markers
- Faster CI/CD feedback loops
- Clear optimization roadmap

## Quick Reference

| Command | Purpose |
|---------|---------|
| `.\tools\pytest_wf_1_gather_slow_tests.bat` | Initial discovery |
| `.\tools\pytest_wf_4_analyze_markers.bat` | Marker analysis |
| `.\tools\pytest_wf_10_validate_improvements.bat` | Validation |

**Next Step**: Run the first command and analyze the results with the LLM prompt above.
