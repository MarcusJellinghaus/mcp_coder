# Issue #359: Refactor vscodeclaude - Use labels.json as Single Source of Truth

## Summary

Consolidate vscodeclaude status label metadata into `labels.json`, eliminating duplicate hardcoded constants in `types.py` and `workspace.py`. This refactoring follows the KISS principle - no new abstractions, just changing where data comes from.

## Problem Statement

The vscodeclaude feature defines status labels in multiple locations:

| Location | Constants |
|----------|-----------|
| `types.py` | `VSCODECLAUDE_PRIORITY`, `HUMAN_ACTION_COMMANDS`, `STATUS_EMOJI`, `STAGE_DISPLAY_NAMES` |
| `workspace.py` | `_get_stage_short()` mapping |
| `labels.json` | `category: "human_action"` (partially used) |

**Current partial integration:** `issues.py` already loads human_action labels from `labels.json` via `get_human_action_labels()`, but sorting still uses hardcoded `VSCODECLAUDE_PRIORITY`.

## Solution Overview

### Architectural Change

**Before:** Multiple hardcoded dictionaries scattered across files
```
types.py (constants) ──► workspace.py, helpers.py, issues.py
```

**After:** Single source of truth in JSON
```
labels.json (with vscodeclaude metadata) ──► issues.py (_load_labels_config) ──► workspace.py, helpers.py
```

### Design Decisions

1. **No new abstractions** - Reuse existing `_load_labels_config()` function
2. **Priority from label name** - Extract numeric prefix with regex `r'status-(\d+):'`
3. **Clean break** - Remove constants entirely (no backwards-compatible wrappers)
4. **Inline lookups** - Each consumer extracts what it needs directly from config

## Data Structure Change

### labels.json Extension

Add `vscodeclaude` object to each `human_action` label:

```json
{
  "internal_id": "created",
  "name": "status-01:created",
  "color": "10b981",
  "description": "Fresh issue, may need refinement",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "📝",
    "display_name": "ISSUE ANALYSIS",
    "stage_short": "new",
    "initial_command": "/issue_analyse",
    "followup_command": "/discuss"
  }
}
```

## Files to Modify

### Source Files

| File | Action |
|------|--------|
| `src/mcp_coder/config/labels.json` | Add `vscodeclaude` object to 4 human_action labels |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | Replace priority sorting with numeric prefix extraction |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Load from config, remove `_get_stage_short()` |
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | Load display names from config |
| `src/mcp_coder/workflows/vscodeclaude/types.py` | Remove 4 constants |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Remove 4 constant exports |

### Test Files

| File | Action |
|------|--------|
| `tests/workflows/vscodeclaude/test_types.py` | Remove constant assertion tests |
| `tests/workflows/vscodeclaude/test_issues.py` | Update to test numeric prefix sorting |
| `tests/workflows/vscodeclaude/test_workspace.py` | Update mocks for config-based lookups |
| `tests/workflows/vscodeclaude/test_helpers.py` | Update to test config-based display names |

## Implementation Steps

| Step | Description | TDD Focus |
|------|-------------|-----------|
| 1 | Extend `labels.json` with vscodeclaude metadata | Schema validation test |
| 2 | Update `issues.py` - numeric prefix sorting | Sorting behavior tests |
| 3 | Update `workspace.py` - config-based lookups | Script generation tests |
| 4 | Update `helpers.py` - config-based display names | Display name tests |
| 5 | Clean up `types.py` and `__init__.py` | Export removal verification |
| 6 | Final test cleanup and verification | All tests pass |

## Acceptance Criteria

- [ ] `labels.json` contains `vscodeclaude` object for all 4 human_action labels
- [ ] `types.py` no longer has hardcoded label lists (only TypedDicts and numeric defaults remain)
- [ ] Constants removed from `__init__.py` exports: `VSCODECLAUDE_PRIORITY`, `HUMAN_ACTION_COMMANDS`, `STATUS_EMOJI`, `STAGE_DISPLAY_NAMES`
- [ ] All vscodeclaude functionality works identically (same emojis, commands, display names)
- [ ] Adding a new human_action label only requires updating `labels.json`
- [ ] All existing tests pass (updated to test config loading)
- [ ] No new hardcoded status label strings introduced

## Constants Being Removed

### From `types.py`:

```python
# REMOVE - will be derived from labels.json
VSCODECLAUDE_PRIORITY = ["status-10:pr-created", "status-07:code-review", ...]
HUMAN_ACTION_COMMANDS = {"status-01:created": ("/issue_analyse", "/discuss"), ...}
STATUS_EMOJI = {"status-01:created": "📝", ...}
STAGE_DISPLAY_NAMES = {"status-01:created": "ISSUE ANALYSIS", ...}

# KEEP - these are not label-related
DEFAULT_MAX_SESSIONS = 3
DEFAULT_PROMPT_TIMEOUT = 300
```

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing tests | Step-by-step updates with mocking |
| Missing label data | Validation in step 1 |
| Performance (repeated file I/O) | `_load_labels_config()` already cached |
