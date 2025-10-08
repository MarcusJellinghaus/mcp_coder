# Runtime Statistics Review Process

## Overview
Automated process for managing test performance and maintaining accurate slow test registry.

## Execution
```bash
claude -p "Please execute the runtime statistics review process based on the latest performance data in docs/tests/performance_data/"
```

## Prerequisites
- Performance data exists in `docs/tests/performance_data/`
- LLM has MCP tools access

## Process Steps

### 1. Data Collection
- Find latest timestamped file in `docs/tests/performance_data/`
- Extract performance data and metadata (timestamp, branch, test counts)
- Validate data integrity

### 2. Performance Analysis
- Load current registry from `docs/tests/runtime_statistics.md`
- Compare against previous runs if available
- Classify each test:
  - **RESOLVED**: Previously slow, now acceptable
  - **NEW_SLOW**: Now exceeds thresholds
  - **REGRESSION**: >50% slower
  - **IMPROVEMENT**: >25% faster
  - **STABLE_SLOW**: Consistently slow

### 3. File Updates

#### Update `runtime_statistics.md` (Current State Registry)
**Purpose**: Maintain accurate baseline of currently slow tests

**Add to Registry:**
- Tests currently exceeding thresholds
- Current timing and severity level
- Category context (external API, resource-intensive, etc.)

**Remove from Registry:**
- Tests no longer slow (now within thresholds)
- Tests that no longer exist in codebase
- Outdated entries with incorrect timings
- False positives (move to "Known False Positives" section)
- Approved slow tests (move to "Approved Slow Tests" section)

**Update in Registry:**
- Existing slow tests with significantly changed timings
- Performance trends summary
- Analysis timestamp and metadata

**Special Sections:**

1. **Known False Positives** section:
   - pytest-xdist parallelization overhead (random, non-deterministic)
   - Environmental artifacts
   - Tests that are fast serially but slow in parallel

2. **Approved Slow Tests** section (organized by marker):
   - Tests that are legitimately slow but acceptable
   - Organized by pytest marker (git_integration, claude_integration, etc.)
   - Include reference time and justification
   - Distinguish from tests needing optimization

#### Update `issues.md` (Action Queue)
**Purpose**: Track items requiring human review and action

**Add to Issues:**
- NEW_SLOW tests requiring investigation
- REGRESSION tests needing optimization
- Tests exceeding critical thresholds by >2x
- Recommended category reassignments
- Process improvement suggestions

**Remove from Issues:**
- Items that have been addressed/resolved
- Tests that were optimized and no longer slow
- Completed action items

**Update in Issues:**
- Priority levels based on impact and frequency
- Action item status and progress notes

### 4. Documentation Standards

#### Registry Format (`runtime_statistics.md`)

**Known Slow Tests Registry** (needs action/investigation):
```markdown
## Known Slow Tests Registry
### [Category] (Exceeding Xs threshold)
- `file_path::ClassName::test_method_name` - **XXs** 🚨 SEVERITY
```

**Known False Positives** (environmental, no action needed):
```markdown
## Known False Positives
### pytest-xdist Parallelization Overhead
- `file_path::ClassName::test_method_name` - **XXs** parallel, **Ys** serial
- **Pattern**: Heavy mocking causes random slowness in parallel execution
- **Verification**: Run with `-n0` to confirm <0.2s serial time
```

**Approved Slow Tests** (legitimately slow, acceptable):
```markdown
## Approved Slow Tests
### Git Integration Tests (`@pytest.mark.git_integration`)
- `file_path::test_name` - **XXs** ✅ APPROVED
  - **Justification**: Real git repository operations with file I/O
  - **Reference time**: 10-15s acceptable for comprehensive workflow tests
  - **Last verified**: YYYY-MM-DD

### Claude Integration Tests (`@pytest.mark.claude_integration`)
- `file_path::test_name` - **XXs** ✅ APPROVED
  - **Justification**: Real network calls to Claude API
  - **Reference time**: 60-90s acceptable for full integration tests
  - **Last verified**: YYYY-MM-DD
```

#### Issues Format (`issues.md`)
```markdown
## Performance Issues Requiring Review
### High Priority
- [ ] **NEW_SLOW**: `test_path` - XXs (investigate cause)
- [ ] **REGRESSION**: `test_path` - XXs → XXs (50% slower)
```

### 5. Cleanup Criteria

#### Registry Cleanup (Aggressive)
- Remove ALL tests not currently slow from "Known Slow Tests Registry"
- Keep only verified current violations needing investigation
- Target: >95% accuracy of listed tests

#### False Positives Cleanup (Verification-Based)
- Add tests confirmed as environmental artifacts (pytest-xdist, etc.)
- Remove if pattern changes (e.g., mocking reduced, overhead disappears)
- Verify periodically that serial execution remains fast

#### Approved Slow Tests Cleanup (Review-Based)
- Add tests that are legitimately slow but acceptable
- Include justification and reference time ranges
- Update "Last verified" date on each review
- Remove if timing significantly improves or test is deleted
- Flag for review if timing increases >50% from reference time

#### Issues Cleanup (Completion-Based)
- Remove completed action items
- Archive resolved performance problems
- Keep open investigations and recommendations

### 6. Recommendations
- Tests requiring optimization or splitting
- Category reassignments
- Infrastructure improvements
- Process adjustments

## File Responsibilities

| File | Section | Purpose | Content | Update Frequency |
|------|---------|---------|---------|------------------|
| `runtime_statistics.md` | Known Slow Tests Registry | Action required | Tests exceeding thresholds needing investigation | Every run (aggressive cleanup) |
| `runtime_statistics.md` | Known False Positives | Documentation only | Environmental artifacts (pytest-xdist, etc.) | As identified (verification-based) |
| `runtime_statistics.md` | Approved Slow Tests | Baseline reference | Legitimately slow tests by marker | Periodic review (update "Last verified") |
| `issues.md` | Active Issues | Action queue | New problems + recommendations | As needed (completion-based) |

## Thresholds

| Category | Warning | Critical | Context |
|----------|---------|----------|---------|
| Unit Tests | 0.5s | 1.0s | Fast feedback |
| Claude CLI Integration | 5.0s | 10.0s | Network/CLI overhead |
| Claude API Integration | 10.0s | 30.0s | API latency |
| Git Integration | 5.0s | 10.0s | File I/O |
| Formatter Integration | 3.0s | 8.0s | Code analysis tools |
| GitHub Integration | 10.0s | 30.0s | External API |

## Severity Levels
- 🚨 **EXTREME**: >3x threshold
- ⚠️ **CRITICAL**: >1x threshold, <3x
- ⚠️ **WARNING**: Above warning, below critical
- ✅ **ACCEPTABLE**: Within range

## Success Criteria
- Registry reflects current reality (>95% accuracy)
- All threshold violations documented
- Action items clearly prioritized
- Performance trends updated

## Known False Positives: pytest-xdist Parallelization Overhead

### Pattern Recognition
Tests with **heavy mocking** (8+ nested `@patch` decorators) may show **random slowness** (5-10s) due to pytest-xdist worker overhead, not actual performance issues.

**Characteristics**:
- **Random**: Different test(s) slow on each run (non-deterministic)
- **Inconsistent**: Sometimes one test is 5s+, sometimes all tests are moderately slow (0.2-0.3s)
- **Worker-dependent**: Overhead varies based on which worker processes the test
- **Serial fast**: Same tests run in <0.1s when executed serially (`pytest -n0`)
- **Heavy mocking**: Tests with 8+ `@patch` decorators or complex mock setups

**Verification Steps**:
1. Run suspected test serially: `pytest -vv <test_path> -n0`
2. If serial time is <0.2s but parallel time is >1.0s, it's likely pytest-xdist overhead
3. Check test for heavy mocking (count `@patch` decorators)

**Documentation Strategy (Option 3)**:
- **Accept overhead** as cost of parallel execution
- **Document in registry**: Add note like `- **pytest-xdist overhead, actually 0.08s**`
- **Educate reviewers**: Explain pattern in issues.md
- **No code changes required**: Overhead is environmental, not a test defect

**Example**:
```markdown
#### Unit Tests (Exceeding 1.0s threshold)
- `tests/workflows/implement/test_task_processing.py::TestProcessSingleTask::test_process_single_task_success` - **5.15s** 🚨 EXTREME (5x threshold) - **pytest-xdist overhead, actually 0.08s**
```

**Why Not Fix?**
- Overhead is non-deterministic (can't predict which test will be slow)
- Tests are actually fast when run serially
- Alternative fixes (serial execution marks, refactoring) add complexity
- Documenting false positives helps reviewers understand the pattern

## Key Principles
- **Registry**: Current state only, aggressive cleanup
- **Issues**: Action queue, completion-based cleanup
- **Accuracy over history**: Remove resolved problems
- **Actionable focus**: Clear next steps with priorities
