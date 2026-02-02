# Step 7: Cleanup - Delete workflows/ Folder

## LLM Prompt
```
Implement Step 7 of Issue #340. Reference: pr_info/steps/summary.md

Delete the legacy workflows/ folder and its test files.
Verify all tests pass before and after deletion.

This is a cleanup step - no new functionality.
```

---

## WHERE

### Files to Delete

| File | Reason |
|------|--------|
| `workflows/validate_labels.py` | Migrated to define_labels.py |
| `workflows/validate_labels.bat` | Launcher no longer needed |
| `workflows/issue_stats.py` | Migrated to coordinator/issue_stats.py |
| `workflows/issue_stats.bat` | Launcher no longer needed |
| `workflows/__init__.py` | Folder being removed |
| `tests/workflows/test_validate_labels.py` | Tests migrated to test_define_labels.py |
| `tests/workflows/test_issue_stats.py` | Tests migrated to coordinator/test_issue_stats.py |

### Files to Keep

| File | Reason |
|------|--------|
| `tests/workflows/config/test_labels.json` | Used by existing tests as fixture |
| `tests/workflows/config/__init__.py` | Module init for test config |
| `tests/workflows/__init__.py` | Keep if other tests exist in workflows/ |

---

## WHAT

### Pre-Deletion Verification
1. Run full test suite to ensure all tests pass
2. Verify new tests cover migrated functionality
3. Check no imports reference deleted files

### Deletion Steps
1. Delete workflow script files
2. Delete workflow batch files
3. Delete old test files
4. Remove `workflows/` folder if empty (except keep test config)

---

## HOW

### Verification Commands Before Deletion
```bash
# Run all tests
pytest tests/ -v

# Check for imports of deleted modules
grep -r "from workflows" src/
grep -r "import workflows" src/
grep -r "from workflows" tests/
```

### Deletion Commands
```bash
# Delete Python files
rm workflows/validate_labels.py
rm workflows/issue_stats.py
rm workflows/__init__.py

# Delete batch files
rm workflows/validate_labels.bat
rm workflows/issue_stats.bat

# Delete old test files
rm tests/workflows/test_validate_labels.py
rm tests/workflows/test_issue_stats.py

# Remove workflows folder if empty
rmdir workflows  # Only if empty
```

### Post-Deletion Verification
```bash
# Run all tests again
pytest tests/ -v

# Verify no broken imports
python -c "from mcp_coder.cli.commands.define_labels import execute_define_labels"
python -c "from mcp_coder.cli.commands.coordinator.issue_stats import execute_coordinator_issue_stats"
```

---

## ALGORITHM

### Cleanup Process
```
1. Run pytest - all tests must pass
2. Check grep for imports - must be zero hits
3. Delete workflow scripts
4. Delete batch launchers
5. Delete old tests
6. Run pytest again - all tests must pass
7. Verify CLI commands work
```

---

## DATA

### Expected Test Count Changes

| Before | After | Reason |
|--------|-------|--------|
| N tests in test_validate_labels.py | 0 (deleted) | Migrated to test_define_labels.py |
| N tests in test_issue_stats.py | 0 (deleted) | Migrated to coordinator/test_issue_stats.py |
| M tests in test_define_labels.py | M + validation tests | Gained migrated tests |
| 0 tests in coordinator/test_issue_stats.py | P tests | New file with migrated tests |

**Total test count should remain the same or increase.**

---

## VERIFICATION

```bash
# Before deletion - record test count
pytest tests/ --collect-only | tail -5

# After deletion - verify same or more tests
pytest tests/ --collect-only | tail -5

# Full test run
pytest tests/ -v

# CLI verification
mcp-coder define-labels --help
mcp-coder coordinator issue-stats --help
```

---

## NOTES

- The `tests/workflows/` folder may still contain other test files (create_plan, create_pr, implement, vscodeclaude)
- Only delete the specific files mentioned, not the entire tests/workflows/ folder
- The `workflows/` folder at root level should be completely removed
- Keep `tests/workflows/config/` intact as it contains test fixtures
