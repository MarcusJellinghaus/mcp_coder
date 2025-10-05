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

**Update in Registry:**
- Existing slow tests with significantly changed timings
- Performance trends summary
- Analysis timestamp and metadata

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
```markdown
## Known Slow Tests Registry
### [Category] (Exceeding Xs threshold)
- `file_path::ClassName::test_method_name` - **XXs** 🚨 SEVERITY
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
- Remove ALL tests not currently slow
- Keep only verified current violations
- Target: >95% accuracy of listed tests

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

| File | Purpose | Content | Update Frequency |
|------|---------|---------|------------------|
| `runtime_statistics.md` | Current baseline | Currently slow tests only | Every run (aggressive cleanup) |
| `issues.md` | Action queue | New problems + recommendations | As needed (completion-based) |

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

## Key Principles
- **Registry**: Current state only, aggressive cleanup
- **Issues**: Action queue, completion-based cleanup
- **Accuracy over history**: Remove resolved problems
- **Actionable focus**: Clear next steps with priorities
