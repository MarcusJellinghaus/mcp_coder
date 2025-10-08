read f# Runtime Statistics Review Process

## Quick Start
```bash
claude -p "Please execute the runtime statistics review process based on the latest performance data in docs/tests/performance_data/"
```

**Prerequisites**: Performance data in `docs/tests/performance_data/`, MCP tools access

## Generating Profiler Data

Before analyzing performance issues, you may want to generate detailed profiler data to understand where time is being spent in slow tests.

### Running the Test Profiler

**Full profiling run** (profiles all tests, generates reports for tests >1s):
```batch
tools\test_profiler.bat
```

This will:
1. Clean the profiling output directory
2. Run all tests with profiling enabled (serial execution, no `-n auto`)
3. Generate detailed text reports for tests taking >1 second
4. Create a summary of all slow tests

**Regenerate reports only** (if pytest already ran but you want new reports):
```batch
tools\test_profiler_generate_only.bat
```

### Profiler Output Location

All profiler data is saved to:
```
docs\tests\performance_data\prof\
```

**Files generated:**
- `*.prof` - Binary profile data for ALL tests (can be analyzed with Python profiler tools)
- `*_report.txt` - Human-readable text reports for tests >1 second only
- `summary.txt` - Overview of all slow tests with durations
- `durations.json` - Machine-readable JSON with all test timings

### Analyzing Profiler Reports

**Step 1: Check the summary**
```
type docs\tests\performance_data\prof\summary.txt
```

This shows all slow tests sorted by duration.

**Step 2: Read individual test reports**

For a specific slow test, open its report file:
```
type docs\tests\performance_data\prof\<test_name>_report.txt
```

Each report contains:
- **Summary**: Total function calls and execution time
- **Top functions by cumulative time**: Where total time is spent (including subcalls)
- **Top functions by internal time**: Where time is spent in the function itself
- **Caller information**: What called these slow functions

**Step 3: Identify bottlenecks**

Look for:
- Functions with high `cumtime` (cumulative time) - total time including subcalls
- Functions with high `tottime` (total time) - time in function itself
- Network I/O operations (socket reads, SSL operations)
- `time.sleep()` calls (rate limiting, retries)
- Database or file system operations

### Example Analysis

For the slowest test (175 seconds), the profiler shows:
- **103 seconds** - SSL socket reads (network I/O)
- **66 seconds** - `time.sleep()` calls (rate limiting)
- **6 seconds** - actual processing

This indicates the test is slow due to real API calls and rate limiting, not code inefficiency.

### Configuration

To change the threshold for "slow" tests (default: 1 second), edit:
```python
# In tools\test_profiler_plugin\__init__.py
DURATION_THRESHOLD_SECONDS = 1.0  # Change this value
```

Then run `tools\test_profiler_generate_only.bat` to regenerate reports with the new threshold.

## Process Overview

### 1. Data Collection
- Find latest timestamped file in `docs/tests/performance_data/`
- Extract performance data and metadata
- Validate data integrity

### 2. Performance Analysis
Compare against previous runs and classify:
- **RESOLVED**: Previously slow, now acceptable
- **NEW_SLOW**: Now exceeds thresholds
- **REGRESSION**: >50% slower
- **IMPROVEMENT**: >25% faster
- **STABLE_SLOW**: Consistently slow

### 3. Update Files

#### `runtime_statistics.md` - Three Sections

**A. Known Slow Tests Registry** (action required):
- Currently exceeding thresholds
- Remove: tests now within thresholds, false positives, approved tests
- Update: significantly changed timings, trends

**B. Known False Positives** (no action):
- pytest-xdist overhead, environmental artifacts
- Tests fast serially but slow in parallel
- Verification command included

**C. Approved Slow Tests** (baseline reference):
- Organized by pytest marker
- Justification + reference time + last verified date
- Flag if >50% slower than reference

#### `issues.md` - Action Queue
- **Add**: NEW_SLOW, REGRESSION, critical threshold violations
- **Remove**: Resolved items, completed actions
- **Update**: Priority levels, progress notes

### 4. File Formats

**Registry - Slow Tests**:
```markdown
## Known Slow Tests Registry
### [Category] (Exceeding Xs threshold)
- `file::Class::test` - **XXs** 🚨 SEVERITY
```

**Registry - False Positives**:
```markdown
## Known False Positives
### pytest-xdist Parallelization Overhead
- `file::Class::test` - **XXs** parallel, **Ys** serial
- **Pattern**: Heavy mocking (8+ `@patch`) causes random slowness
- **Verification**: `pytest -vv <path> -n0` confirms <0.2s serial
```

**Registry - Approved Tests**:
```markdown
## Approved Slow Tests
### Git Integration (`@pytest.mark.git_integration`)
- `file::test` - **XXs** ✅
  - **Justification**: Real git operations + file I/O
  - **Reference time**: 10-20s
  - **Last verified**: 2025-10-07
```

**Issues**:
```markdown
## Performance Issues Requiring Review
### High Priority
- [ ] **NEW_SLOW**: `test_path` - XXs (investigate)
- [ ] **REGRESSION**: `test_path` - XXs → XXs (50% slower)
```

## Cleanup Rules

| Section | Strategy | Action |
|---------|----------|--------|
| Known Slow Tests | Aggressive | Remove all tests now within thresholds |
| False Positives | Verification | Add confirmed artifacts, verify periodically |
| Approved Slow Tests | Review-based | Update dates, flag >50% increases |
| Issues | Completion | Remove resolved items |

## Thresholds & Severity

| Category | Warning | Critical | Context |
|----------|---------|----------|---------|
| Unit Tests | 0.5s | 1.0s | Fast feedback |
| Claude CLI/API Integration | 5.0s/10.0s | 10.0s/30.0s | Network overhead |
| Git Integration | 5.0s | 10.0s | File I/O |
| Formatter Integration | 3.0s | 8.0s | Code analysis |
| GitHub Integration | 10.0s | 30.0s | External API |

**Severity**: 🚨 EXTREME (>3x), ⚠️ CRITICAL (>1x, <3x), ⚠️ WARNING (above warning, below critical), ✅ ACCEPTABLE

## pytest-xdist False Positives

**Pattern**: Tests with 8+ `@patch` decorators show random 5-10s slowness in parallel execution

**Characteristics**:
- Non-deterministic (different test(s) slow each run)
- Inconsistent (5s+ or 0.2-0.3s per run)
- Fast serially (<0.1s with `pytest -n0`)

**Verification**:
1. Run serially: `pytest -vv <test_path> -n0`
2. If <0.2s serial but >1.0s parallel → pytest-xdist overhead
3. Count `@patch` decorators (8+ confirms pattern)

**Documentation**: Accept overhead, document as: `- **pytest-xdist overhead, actually 0.08s**`

## Success Criteria
- Registry >95% accurate (current state only)
- All violations documented with context
- Action items prioritized
- Trends updated

## Key Principles
- **Accuracy over history**: Remove resolved problems
- **Actionable focus**: Clear next steps with priorities
- **Three-tier system**: Action required / False positives / Approved baselines
