# Slow Tests Inventory

*Last Updated: [DATE] - [Update this when modifying]*

## Summary Statistics
- **Total Slow Tests Identified**: [TO BE FILLED]
- **Average Execution Time**: [TO BE FILLED]
- **Most Time-Consuming Category**: [TO BE FILLED]

## Slow Tests by Execution Time

### Critical (>10 seconds)
*Tests that significantly impact CI/CD pipeline*

| Test Name | File Location | Execution Time | Markers | Priority | Notes |
|-----------|---------------|----------------|---------|----------|--------|
| [Example] | tests/example.py::test_slow | 15.2s | integration, slow | High | Database operations |

### High (5-10 seconds)
*Tests with moderate performance impact*

| Test Name | File Location | Execution Time | Markers | Priority | Notes |
|-----------|---------------|----------------|---------|----------|--------|
| | | | | | |

### Medium (2-5 seconds)
*Tests with minor performance impact*

| Test Name | File Location | Execution Time | Markers | Priority | Notes |
|-----------|---------------|----------------|---------|----------|--------|
| | | | | | |

## Tests by Category

### Integration Tests
*Tests that interact with external systems*

| Test Name | Execution Time | Systems Involved | Optimization Notes |
|-----------|----------------|------------------|-------------------|
| | | | |

### Database Tests
*Tests that perform database operations*

| Test Name | Execution Time | Database Operations | Optimization Notes |
|-----------|----------------|-------------------|-------------------|
| | | | |

### Network/API Tests
*Tests that make network calls*

| Test Name | Execution Time | External Dependencies | Optimization Notes |
|-----------|----------------|----------------------|-------------------|
| | | | |

### File I/O Tests
*Tests that perform significant file operations*

| Test Name | Execution Time | File Operations | Optimization Notes |
|-----------|----------------|----------------|-------------------|
| | | | |

## Marker Analysis

### Current Markers Found
*Pytest markers are defined in pyproject.toml*

- See `[tool.pytest.ini_options]` section in pyproject.toml for current marker definitions
- Check marker usage patterns in actual test files below
- [Update counts after analysis]

### Recommended Marker Strategy
*Use markers from pyproject.toml*

1. **Follow pyproject.toml definitions**:
   - See `[tool.pytest.ini_options]` markers section for current definitions
   - Use the CI patterns documented in the comments

2. **CI exclusion patterns** (from pyproject.toml):
   ```bash
   # Fast CI run (exclude integration tests)
   pytest -m "not git_integration and not claude_integration"
   
   # Run integration test groups
   pytest -m "git_integration or claude_integration"
   ```

## Optimization Opportunities

### High Priority
*Tests that should be optimized first*

1. [Test Name] - [Reason] - [Estimated Impact]

### Medium Priority
*Tests for future optimization*

1. [Test Name] - [Reason] - [Estimated Impact]

### Low Priority
*Tests that are acceptable as-is*

1. [Test Name] - [Reason]

## Change Log

### [DATE] - Initial Inventory
- Created initial inventory structure
- [Add specific changes]

### [DATE] - [Description]
- [Change details]

## Next Steps
*Action items for test performance improvements*

1. [ ] Complete initial slow test discovery
2. [ ] Implement standardized markers
3. [ ] Optimize top 5 slowest tests
4. [ ] Set up CI exclusion patterns
5. [ ] Regular performance monitoring
