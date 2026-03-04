# Summary: Add Uncommitted Changes to compact-diff

## Issue Reference
**Issue #477**: git-tool compact-diff should show uncommitted changes

## Overview
Enhance `mcp-coder git-tool compact-diff` to show uncommitted changes (staged, unstaged, and untracked files) by default, in addition to committed changes. Add `--committed-only` flag to opt-out and preserve existing behavior.

## User Impact
- **Before**: Only shows committed changes between branches, silently ignoring local work
- **After**: Shows committed changes (compact format) + uncommitted changes (full format)
- **Opt-out**: Use `--committed-only` flag to get old behavior

## Architectural Changes

### Design Philosophy: KISS Principle
**Keep complexity in the CLI layer, not the core library.**

- ✅ **No changes to `compact_diffs.py`** - Preserve single responsibility (compacting diffs)
- ✅ **All logic in `git_tool.py`** - CLI orchestration layer handles combining outputs
- ✅ **Reuse existing functions** - Leverage `get_git_diff_for_commit()` and `get_full_status()`

### Component Responsibilities

```
CLI Layer (git_tool.py)
├── Orchestrate: Get committed diff → Get uncommitted diff → Combine
├── Apply exclude patterns to both diffs
└── Format output with section headers

Core Library (compact_diffs.py)
└── Unchanged - Continues to compact committed diffs only

Utility Functions (diffs.py, readers.py)
└── Unchanged - Reused as-is for uncommitted changes
```

### Data Flow

```
User runs: mcp-coder git-tool compact-diff

                    ┌─────────────────────┐
                    │   execute_compact   │
                    │      _diff()        │
                    └──────────┬──────────┘
                               │
                ┏━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┓
                ▼                              ▼
    ┌────────────────────┐          ┌──────────────────────┐
    │ get_compact_diff() │          │ get_git_diff_for_    │
    │ (committed changes)│          │   commit()           │
    │                    │          │ (uncommitted changes)│
    └────────────────────┘          └──────────────────────┘
                │                              │
                │                              │
                │                    ┌─────────▼─────────┐
                │                    │ apply_exclude_    │
                │                    │  patterns_to_     │
                │                    │  uncommitted()    │
                │                    └─────────┬─────────┘
                │                              │
                └──────────────┬───────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Format & Combine   │
                    │  - Committed first  │
                    │  - Uncommitted next │
                    └─────────────────────┘
                               │
                               ▼
                         Print result
```

## Files to Create or Modify

### Modified Files (3)
1. **`src/mcp_coder/cli/parsers.py`**
   - Add `--committed-only` flag to `compact-diff` subcommand
   - Type: Argument parser configuration

2. **`src/mcp_coder/cli/commands/git_tool.py`**
   - Add helper function: `_apply_exclude_patterns_to_uncommitted_diff()`
   - Modify: `execute_compact_diff()` to append uncommitted changes
   - Type: CLI command logic

3. **`docs/cli-reference.md`**
   - Update `git-tool compact-diff` section with new flag and behavior
   - Add examples showing uncommitted changes
   - Type: Documentation

### New Test Cases (1 file)
4. **`tests/cli/commands/test_git_tool.py`**
   - Add new test class: `TestCompactDiffUncommittedChanges`
   - Tests for default behavior, `--committed-only` flag, exclude patterns
   - Type: CLI integration tests

### Unchanged Files (Key Dependencies)
- ✅ `src/mcp_coder/utils/git_operations/compact_diffs.py` - No changes (KISS!)
- ✅ `src/mcp_coder/utils/git_operations/diffs.py` - Reused as-is
- ✅ `src/mcp_coder/utils/git_operations/readers.py` - Reused as-is
- ✅ `tests/utils/git_operations/test_compact_diffs.py` - No changes needed

## Key Design Decisions

### 1. Where to Put the Logic?
**Decision**: CLI layer (`git_tool.py`), not core library (`compact_diffs.py`)

**Rationale**:
- Single Responsibility: Compact diff library stays focused on compacting
- Lower Risk: No changes to battle-tested compacting algorithm
- Easier Testing: Only CLI-level integration tests needed
- Clearer Separation: "What to show" (CLI) vs "How to compact" (library)

### 2. Exclude Patterns for Uncommitted Changes?
**Decision**: Yes, apply exclude patterns to uncommitted changes

**Rationale**:
- Consistency: Users expect `--exclude` to work everywhere
- Use Case: Exclude temp files, logs, etc. from all diffs
- Complexity: Minimal (10-15 line helper function)

### 3. Format of Uncommitted Changes?
**Decision**: Full diffs (not compacted)

**Rationale**:
- Issue Requirement: Explicitly states "full diff" for uncommitted
- User Expectation: Local changes are already small, no need to compact
- Simplicity: Reuse `get_git_diff_for_commit()` output directly

### 4. Output Structure?
**Decision**: Committed first, then uncommitted (with clear separator)

**Format**:
```
[compact diff of committed changes]

=== UNCOMMITTED CHANGES ===
=== STAGED CHANGES ===
[full diff of staged files]

=== UNSTAGED CHANGES ===
[full diff of modified files]

=== UNTRACKED FILES ===
[full diff of new files]
```

**Edge Cases**:
- No committed changes: Show "No committed changes" message
- Clean working directory: Skip uncommitted section entirely
- `--committed-only` flag: Skip uncommitted section entirely

## Implementation Strategy

### Test-Driven Development Approach
1. **Step 1**: Add `--committed-only` flag (test parser change)
2. **Step 2**: Test uncommitted changes display (write failing tests first)
3. **Step 3**: Implement uncommitted changes logic (make tests pass)
4. **Step 4**: Test exclude patterns on uncommitted (write failing tests first)
5. **Step 5**: Implement exclude pattern filtering (make tests pass)
6. **Step 6**: Update documentation

### Complexity Budget
- **New code**: ~40-50 lines (helper function + orchestration)
- **Test code**: ~100-150 lines (comprehensive coverage)
- **Changed files**: 3 source files + 1 test file + 1 doc file
- **Risk**: Low (no core library changes)

## Success Criteria

### Functional Requirements ✅
- [ ] Show uncommitted changes by default
- [ ] `--committed-only` flag suppresses uncommitted changes
- [ ] Uncommitted changes shown in full (not compacted)
- [ ] Exclude patterns apply to both committed and uncommitted
- [ ] Skip uncommitted section if working directory is clean
- [ ] Show "No committed changes" when appropriate
- [ ] Exit codes unchanged (uncommitted changes are informational)

### Non-Functional Requirements ✅
- [ ] KISS principle applied (minimal complexity)
- [ ] Single responsibility preserved in libraries
- [ ] Comprehensive test coverage (>90%)
- [ ] Clear documentation with examples
- [ ] No performance regression

## Timeline Estimate
- **Step 1-2**: Parser flag + basic tests (30 min)
- **Step 3**: Core implementation (45 min)
- **Step 4-5**: Exclude pattern logic + tests (30 min)
- **Step 6**: Documentation (15 min)
- **Total**: ~2 hours for experienced developer

## Rollback Plan
If issues arise:
1. Revert parser changes (restore `parsers.py`)
2. Revert CLI changes (restore `git_tool.py`)
3. Core library unchanged - zero risk there

## Related Issues / Future Work
- Consider applying compact diff logic to uncommitted changes (future enhancement)
- Add `--uncommitted-only` flag (if requested)
- Support custom section headers (if requested)
