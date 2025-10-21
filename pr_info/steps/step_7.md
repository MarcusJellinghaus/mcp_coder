# Step 7: Delete Old Files and Final Verification

## Objective

Delete the old standalone workflow files and perform final verification that the migration is complete and working correctly.

## Reference

Review `summary.md` for the list of files to delete and the complete migration context.

## WHERE: File Paths

### Files to DELETE
- `workflows/create_plan.py` - Old standalone script (replaced by `src/mcp_coder/workflows/create_plan.py`)
- `workflows/create_plan.bat` - Windows batch wrapper (no longer needed)

### Files to VERIFY
- All new files exist and are functioning
- All tests pass
- CLI command works end-to-end

## WHAT: Deletion Process

### Safe Deletion Steps

1. **Verify new implementation works**
2. **Delete old files**
3. **Run final verification**
4. **Confirm no references remain**

### Files to Remove

**File 1: `workflows/create_plan.py`**
- **Size:** ~485 lines
- **Reason:** Replaced by `src/mcp_coder/workflows/create_plan.py`
- **Safety:** All code migrated, all tests updated

**File 2: `workflows/create_plan.bat`**
- **Size:** ~10 lines
- **Reason:** No longer needed with CLI command
- **Safety:** Functionality replaced by `mcp-coder create-plan` command

## HOW: Deletion and Verification

### Pre-Deletion Verification

**Before deleting files, verify:**

1. **New CLI command works:**
   ```bash
   mcp-coder create-plan --help
   ```
   
2. **New workflow module exists:**
   ```bash
   python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow"
   ```

3. **All tests pass:**
   ```bash
   pytest tests/cli/commands/test_create_plan.py tests/workflows/create_plan/
   ```

### Deletion Process

**Execute deletions:**

```bash
# Delete old workflow script
rm workflows/create_plan.py

# Delete batch wrapper
rm workflows/create_plan.bat
```

**Or using Python:**
```python
from pathlib import Path

# Delete old workflow script
old_workflow = Path("workflows/create_plan.py")
if old_workflow.exists():
    old_workflow.unlink()
    print(f"Deleted: {old_workflow}")

# Delete batch wrapper
old_batch = Path("workflows/create_plan.bat")
if old_batch.exists():
    old_batch.unlink()
    print(f"Deleted: {old_batch}")
```

### Post-Deletion Verification

**After deleting files, verify:**

1. **Files are gone:**
   ```bash
   ls -la workflows/create_plan.py    # Should not exist
   ls -la workflows/create_plan.bat   # Should not exist
   ```

2. **No import references to old files:**
   ```bash
   grep -r "from workflows.create_plan" . --exclude-dir=.git --exclude-dir=.venv
   # Should return no results
   ```

3. **All tests still pass:**
   ```bash
   pytest tests/cli/commands/test_create_plan.py tests/workflows/create_plan/
   ```

4. **CLI command works:**
   ```bash
   mcp-coder create-plan --help
   ```

## ALGORITHM: Verification Process

```python
# Pre-deletion checks
verify_cli_help_works()
verify_new_module_imports()
verify_all_tests_pass()

# Delete files
delete("workflows/create_plan.py")
delete("workflows/create_plan.bat")

# Post-deletion checks
verify_files_deleted()
verify_no_old_imports()
verify_tests_still_pass()
verify_cli_still_works()

# Final verification
run_all_quality_checks()
```

## DATA: Verification Checklist

### Pre-Deletion Checklist
- [ ] ✅ CLI help displays: `mcp-coder create-plan --help`
- [ ] ✅ New module imports: `from mcp_coder.workflows.create_plan import ...`
- [ ] ✅ All tests pass: `pytest tests/.../test_create_plan.py`
- [ ] ✅ Quality checks pass: pylint, mypy, pytest

### Deletion Checklist
- [ ] ✅ Deleted: `workflows/create_plan.py`
- [ ] ✅ Deleted: `workflows/create_plan.bat`

### Post-Deletion Checklist
- [ ] ✅ Files confirmed deleted
- [ ] ✅ No references to old imports found
- [ ] ✅ All tests still pass
- [ ] ✅ CLI command still works
- [ ] ✅ Quality checks still pass

## Implementation Details

### Complete Verification Script

```python
"""Verification script for create-plan migration."""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run command and report result."""
    print(f"\n{'='*60}")
    print(f"Checking: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✓ PASSED: {description}")
            return True
        else:
            print(f"✗ FAILED: {description}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ ERROR: {description}")
        print(f"Exception: {e}")
        return False


def check_file_deleted(filepath: str) -> bool:
    """Check that file is deleted."""
    path = Path(filepath)
    if not path.exists():
        print(f"✓ File deleted: {filepath}")
        return True
    else:
        print(f"✗ File still exists: {filepath}")
        return False


def main() -> int:
    """Run complete verification."""
    print("\n" + "="*60)
    print("CREATE-PLAN MIGRATION VERIFICATION")
    print("="*60)
    
    checks_passed = 0
    checks_total = 0
    
    # Pre-deletion checks
    print("\n### PRE-DELETION CHECKS ###")
    
    checks_total += 1
    if run_command(
        ["mcp-coder", "create-plan", "--help"],
        "CLI help displays"
    ):
        checks_passed += 1
    
    checks_total += 1
    if run_command(
        ["python", "-c", "from mcp_coder.workflows.create_plan import run_create_plan_workflow"],
        "New module imports"
    ):
        checks_passed += 1
    
    checks_total += 1
    if run_command(
        ["pytest", "tests/cli/commands/test_create_plan.py", "tests/workflows/create_plan/", "-v"],
        "All tests pass"
    ):
        checks_passed += 1
    
    # File deletion
    print("\n### FILE DELETION ###")
    
    old_workflow = Path("workflows/create_plan.py")
    old_batch = Path("workflows/create_plan.bat")
    
    if old_workflow.exists():
        old_workflow.unlink()
        print(f"Deleted: {old_workflow}")
    
    if old_batch.exists():
        old_batch.unlink()
        print(f"Deleted: {old_batch}")
    
    # Post-deletion checks
    print("\n### POST-DELETION CHECKS ###")
    
    checks_total += 1
    if check_file_deleted("workflows/create_plan.py"):
        checks_passed += 1
    
    checks_total += 1
    if check_file_deleted("workflows/create_plan.bat"):
        checks_passed += 1
    
    checks_total += 1
    if run_command(
        ["pytest", "tests/cli/commands/test_create_plan.py", "tests/workflows/create_plan/", "-v"],
        "Tests still pass after deletion"
    ):
        checks_passed += 1
    
    checks_total += 1
    if run_command(
        ["mcp-coder", "create-plan", "--help"],
        "CLI still works after deletion"
    ):
        checks_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    print(f"Checks passed: {checks_passed}/{checks_total}")
    
    if checks_passed == checks_total:
        print("\n✓ ALL VERIFICATIONS PASSED")
        print("Migration completed successfully!")
        return 0
    else:
        print(f"\n✗ {checks_total - checks_passed} VERIFICATION(S) FAILED")
        print("Please review and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## Verification Steps

### Manual Verification

1. **Test CLI Help:**
   ```bash
   mcp-coder create-plan --help
   ```
   Expected: Help text displays with all options

2. **Test CLI with Mock Issue:**
   ```bash
   # This should fail gracefully (issue doesn't exist)
   # but verifies command routing works
   mcp-coder create-plan 99999 --log-level DEBUG
   ```
   Expected: Error about issue not found (not command not found)

3. **Check File System:**
   ```bash
   # Old files should not exist
   ls -la workflows/create_plan.py    # Not found
   ls -la workflows/create_plan.bat   # Not found
   
   # New files should exist
   ls -la src/mcp_coder/cli/commands/create_plan.py       # Exists
   ls -la src/mcp_coder/workflows/create_plan.py          # Exists
   ls -la tests/cli/commands/test_create_plan.py          # Exists
   ```

4. **Run All Tests:**
   ```bash
   pytest tests/cli/commands/test_create_plan.py tests/workflows/create_plan/ -v
   ```
   Expected: All tests pass

5. **Final Quality Checks:**
   ```bash
   # Run all quality checks one more time
   mcp__code-checker__run_all_checks(
       extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
   )
   ```
   Expected: All checks pass

## Success Criteria

**Migration is complete when:**
- ✅ Old files deleted: `workflows/create_plan.py`, `workflows/create_plan.bat`
- ✅ New files working: CLI command, workflow module, tests
- ✅ All tests passing: CLI tests + workflow tests
- ✅ Quality checks passing: pylint, mypy, pytest
- ✅ No references to old imports
- ✅ CLI command functional: `mcp-coder create-plan --help`

## Next Steps

**Migration Complete!** 

Create commit with changes:
```bash
git add .
git commit -m "Migrate create_plan workflow to CLI command

- Add CLI command: mcp-coder create-plan
- Migrate workflow module to src/mcp_coder/workflows/
- Update all tests with new import paths
- Delete old standalone script and batch file
- All tests passing, quality checks pass"
```

Then push and create pull request.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md and pr_info/steps/step_7.md.

Implement Step 7: Delete Old Files and Final Verification

Requirements:
1. Verify new CLI command works: mcp-coder create-plan --help
2. Verify new module imports correctly
3. Verify all tests pass
4. Delete old files: workflows/create_plan.py and workflows/create_plan.bat
5. Verify files are deleted
6. Verify no references to old imports remain
7. Run final quality checks

Execute verification script or manual checks:

1. Pre-deletion:
   - Test: mcp-coder create-plan --help
   - Test: python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow"
   - Test: pytest tests/cli/commands/test_create_plan.py tests/workflows/create_plan/

2. Delete files:
   - rm workflows/create_plan.py
   - rm workflows/create_plan.bat

3. Post-deletion:
   - Verify files are gone
   - Check no old imports: grep -r "from workflows.create_plan" .
   - Test: pytest tests/.../test_create_plan.py
   - Test: mcp-coder create-plan --help

4. Final checks:
   - Run: mcp__code-checker__run_all_checks()

After completion:
1. Confirm all verifications pass
2. Report final status
3. Migration is complete!

All CLAUDE.md requirements followed.
```
