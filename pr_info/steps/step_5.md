# Step 5: Remove Old Files and Final Verification

## Overview

Delete the old standalone script, batch file, documentation, and test file. Run comprehensive verification.

## WHERE

### Files to delete:
- `workflows/define_labels.py`
- `workflows/define_labels.bat`
- `docs/configuration/LABEL_WORKFLOW_SETUP.md`
- `tests/workflows/test_define_labels.py`

## WHAT

### Deletion checklist:

1. **`workflows/define_labels.py`** - Original standalone script (replaced by CLI command)
2. **`workflows/define_labels.bat`** - Windows batch wrapper (no longer needed)
3. **`docs/configuration/LABEL_WORKFLOW_SETUP.md`** - Old documentation (replaced by new guide)
4. **`tests/workflows/test_define_labels.py`** - Old test location (moved to cli/commands/)

### Final verification tasks:

1. Run all tests to ensure nothing is broken
2. Verify CLI command works end-to-end
3. Check for any remaining references to deleted files
4. Verify documentation links work

## HOW

### Search for remaining references:

```bash
# Search for references to old paths
grep -r "workflows/define_labels" --include="*.py" --include="*.md" --include="*.bat"
grep -r "LABEL_WORKFLOW_SETUP" --include="*.md"
```

## ALGORITHM

N/A - Deletion and verification only.

## DATA

N/A - No code changes.

## LLM Prompt

```
Please implement Step 5 of the implementation plan in `pr_info/steps/step_5.md`.

Context: See `pr_info/steps/summary.md` for the overall plan.

Task: Clean up old files and verify the implementation:

1. Delete the following files:
   - `workflows/define_labels.py`
   - `workflows/define_labels.bat`
   - `docs/configuration/LABEL_WORKFLOW_SETUP.md`
   - `tests/workflows/test_define_labels.py`

2. Search the codebase for any remaining references to:
   - `workflows/define_labels`
   - `LABEL_WORKFLOW_SETUP`
   - Update any found references

3. Run verification:
   - `pytest tests/cli/commands/test_define_labels.py -v` - New tests pass
   - `pytest tests/ -v` - All project tests pass
   - `mcp-coder define-labels --help` - CLI help works
   - `mcp-coder help` - Shows define-labels command

4. Verify no import errors:
   - `python -c "from mcp_coder.cli.commands.define_labels import execute_define_labels"`
```

## Verification

### Functional tests:
- [ ] `mcp-coder define-labels --help` displays usage
- [ ] `mcp-coder define-labels --dry-run` works (in a git repo with GitHub token)
- [ ] `mcp-coder help` shows `define-labels` command

### Test suite:
- [ ] `pytest tests/cli/commands/test_define_labels.py -v` - All pass
- [ ] `pytest tests/ -m "not github_integration"` - All pass (excluding live API tests)

### Code quality:
- [ ] `pylint src/mcp_coder/cli/commands/define_labels.py` - No errors
- [ ] `mypy src/mcp_coder/cli/commands/define_labels.py` - No errors

### Cleanup verification:
- [ ] `workflows/define_labels.py` deleted
- [ ] `workflows/define_labels.bat` deleted
- [ ] `docs/configuration/LABEL_WORKFLOW_SETUP.md` deleted
- [ ] `tests/workflows/test_define_labels.py` deleted
- [ ] No remaining references to deleted files

## Acceptance Criteria Check

After this step, all acceptance criteria from the issue should be met:

- [x] `mcp-coder define-labels` syncs labels to GitHub repository
- [x] `mcp-coder define-labels --dry-run` previews changes without applying
- [x] `mcp-coder define-labels --help` shows command description and options
- [x] `mcp-coder help` includes `define-labels` in command list
- [x] All tests pass (unit + mocked integration)
- [x] Documentation complete and cross-referenced
