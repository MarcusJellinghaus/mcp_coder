# Issue #305: Remove Duplicate labels.json - Implementation Summary

## Problem Statement

Two identical `labels.json` files exist:
- `src/mcp_coder/config/labels.json` - Bundled with package (source of truth)
- `workflows/config/labels.json` - Duplicate local copy

This creates maintenance burden, divergence risk, and confusion about the source of truth.

## Solution

Delete `workflows/config/labels.json` and simplify test fixtures to use the bundled config directly.

## Architectural/Design Changes

**None.** The existing two-location resolution design in `label_config.py` is preserved for external projects. We're only removing mcp_coder's own unnecessary local override.

The `get_labels_config_path()` function continues to:
1. Check `project_dir/workflows/config/labels.json` (for external project customization)
2. Fall back to bundled `mcp_coder/config/labels.json`

This change makes mcp_coder "eat its own dog food" by using the bundled config.

## Files Modified

| File | Action | Description |
|------|--------|-------------|
| `workflows/config/labels.json` | DELETE | Remove duplicate config |
| `workflows/config/__init__.py` | DELETE | Remove empty module |
| `workflows/config/` | DELETE | Remove empty directory |
| `tests/conftest.py` | MODIFY | Simplify `labels_config_path` fixture |
| `tests/workflows/conftest.py` | MODIFY | Simplify `labels_config_path` fixture |

## Files NOT Modified (Preserved)

| File | Reason |
|------|--------|
| `src/mcp_coder/config/labels.json` | Single source of truth (kept) |
| `src/mcp_coder/utils/github_operations/label_config.py` | Two-location design preserved for external projects |
| `tests/workflows/config/test_labels.json` | Test fixture with subset of labels (different purpose) |
| `tests/workflows/config/__init__.py` | Test package marker (kept) |

## Implementation Steps

1. **Step 1**: Delete duplicate files and directory
2. **Step 2**: Simplify test fixtures in both conftest.py files
3. **Step 3**: Verify all tests pass and CLI command works

## Acceptance Criteria

- [x] Only one `labels.json` exists: `src/mcp_coder/config/labels.json`
- [x] All tests pass using bundled config
- [x] Tests that verify the override mechanism still work
- [x] `mcp-coder define-labels` command works correctly
