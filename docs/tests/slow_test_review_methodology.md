Ple# Slow Test Review Methodology

**Quick Reference:**
- **Performance data**: `docs/tests/performance_data/performance_stats_*.txt`
- **Profiling reports**: `docs/tests/performance_data/prof/*.txt`
- **Runtime analysis**: [runtime_statistics.md](runtime_statistics.md)
- **Issue tracking**: [issues.md](issues.md)
- **Review process**: [runtime_statistics_review_process.md](runtime_statistics_review_process.md)

## Key Principle

When tests are slow, don't assume you need to make them faster. Ask: **Are we testing the right things in the right way?**

## 5-Step Process

### 1. Identify Slow Tests

**Where**: `docs/tests/performance_data/performance_stats_YYYYMMDD_HHMMSS.txt`

Look for:
- Tests > 10s execution time
- High variation between runs (30-70s range)
- Test groups with many tests (reduction opportunity)

**Document in**: `runtime_statistics.md` under "Performance Trends"

### 2. Analyze One Representative Test

**Where**: `docs/tests/performance_data/prof/<test_name>_report.txt`

**Compare**:
- Actual pytest time (from performance_stats)
- Profiled time (from prof report)
- Time breakdown (I/O, GC, computation)

**Example**:
```
test_commit_workflows:
  Actual: 67.17s | Profiled: 13.35s | Overhead: 53.82s
  Breakdown: 73% GC, 15% subprocess, 12% test logic
```

**Document in**: `runtime_statistics.md` analysis section

### 3. Classify Root Cause

| Category | Indicators | Action |
|----------|-----------|--------|
| **A: Code Issue** | Inefficient algorithms, missing cache | Optimize code |
| **B: Test Design** | Over-testing wrappers, testing library internals | Reduce tests |
| **C: Environmental** | Disk I/O, antivirus, network overhead | Document & accept |
| **D: Necessary** | Integration tests, real resources needed | Accept & document |

**Document in**: `issues.md` with appropriate priority

### 4. Decide Action

**Decision Tree**:
```
Testing mature library (GitPython, requests)?
  → Reduce to 1 test per function (Category B)

Testing our critical logic?
  → Keep comprehensive coverage

Environmental overhead dominates?
  → Accept & document (Category C)

Code optimization possible?
  → Profile & optimize (Category A)
```

**Document decision in**: `issues.md` with rationale

### 5. Implement & Verify

**For Test Reduction (Category B)**:
1. Audit: Map tests to source functions
2. Design: 1 test per exported function
3. Restructure: Mirror source code layout
4. Measure: Run tests, compare time

**For Code Optimization (Category A)**:
1. Profile: Use `pytest --profile`
2. Optimize: Cache, reduce I/O, minimize objects
3. Re-measure: Verify improvement

**Update After Changes**:
- `runtime_statistics.md` - Update metrics
- `issues.md` - Close or update issue
- `performance_data/` - Save new baseline



## Example: Git Integration Tests (Oct 2025)

**Problem**: 92 tests, 108s, high variation (30-70s)

**Analysis** (`prof/test_commit_workflows_report.txt`):
- 73% time in garbage collection
- Creating 81 Repo objects
- Testing GitPython internals, not our wrappers

**Category**: B (Test Design)

**Action**: Reduce to 1 test per function

**Result**: 22 tests, ~37s (-76% tests, -66% time)

**Documented in**: `issues.md` #013, `runtime_statistics.md` Oct 8 analysis

**Key Learning**: "We were testing that GitPython works, not that our wrappers work."

## Quick Commands

```bash
# Profile specific test
pytest --profile tests/path/to/test.py

# Detailed failure output
pytest -v -s --tb=short tests/path/to/test.py

# Count tests
grep -c "def test_" tests/file.py

# Show slowest tests
pytest tests/ --durations=10
```

## Common Mistakes

❌ Optimizing before profiling  
❌ Ignoring environmental factors  
❌ Over-testing mature libraries  
❌ Removing tests without coverage check  

## Success Checklist

✅ Root cause identified & documented (`issues.md`)  
✅ Decision rationale clear  
✅ Measurable improvement  
✅ Coverage maintained  
✅ Files updated: `runtime_statistics.md`, `issues.md`, `performance_data/`  

---

**See also**: [Runtime Statistics Review Process](runtime_statistics_review_process.md)  
*Last Updated: 2025-10-08 | Based on: Git Integration Test Review (Issue #013)*
