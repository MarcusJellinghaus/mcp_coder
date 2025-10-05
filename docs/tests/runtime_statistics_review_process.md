# Runtime Statistics Review Process

## Overview
This document defines the automated process for managing test performance and detecting slow tests in the MCP Coder project.

## Prerequisites
- `tools/get_pytest_performance_stats.bat` has been executed
- Performance data exists in `docs/tests/performance_data/`
- LLM has access to project files via MCP tools

## Process Steps

### Step 1: Data Collection
1. **Read Latest Performance Data**
   - Find the newest timestamped file in `docs/tests/performance_data/`
   - Parse performance statistics for all test categories
   - Extract git branch information from the report

### Step 2: Baseline Comparison
1. **Load Current Baselines**
   - Read `docs/tests/runtime_statistics.md` for known slow tests and thresholds
   - If file doesn't exist, initialize with default thresholds

2. **Analyze Performance Changes**
   - Identify new tests exceeding thresholds
   - Detect tests that became significantly slower/faster
   - Flag unusual patterns or outliers

### Step 3: Classification and Decision Making
For each flagged test, categorize as:
- **NEW_SLOW**: Previously fast test now exceeds threshold
- **REGRESSION**: Known test became significantly slower
- **IMPROVEMENT**: Previously slow test became faster
- **NEW_TEST**: First-time measurement of a test

### Step 4: Update Documentation
1. **Update Runtime Statistics**
   - Add new slow tests to known registry with **COMPLETE TEST IDENTIFIERS**
   - Include full file path, class name, and test method name
   - Format: `file_path::ClassName::test_method_name` for easy navigation
   - Update performance trends
   - Record analysis timestamp and branch

2. **Update Issues Queue**
   - Add new review items to `docs/tests/issues.md` with complete test paths
   - Include file locations for immediate developer action
   - Prioritize by impact and test execution frequency

### Step 5: Generate Recommendations
Provide actionable recommendations:
- Tests to split or optimize
- Marker reassignments (e.g., promote to integration test)
- Infrastructure improvements
- Process adjustments

## Thresholds (Default)
- **Unit Tests**: 0.5s warning, 1.0s critical
- **Integration Tests**: 5.0s warning, 10.0s critical
- **External API Tests**: 10.0s warning, 30.0s critical

## Output Format
The process should update:
1. `docs/tests/runtime_statistics.md` - Current state and baselines
2. `docs/tests/issues.md` - Action items requiring human review

## Execution Command
```bash
# Run this process after executing performance stats
claude-code "Please execute the runtime statistics review process based on the latest performance data in docs/tests/performance_data/"
```

## Success Criteria
- All performance data processed without errors
- New slow tests identified and documented
- Actionable recommendations provided
- Documentation updated with current analysis
