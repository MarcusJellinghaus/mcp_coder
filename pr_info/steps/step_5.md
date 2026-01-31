# Step 5: Final Verification

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #358.

Implement Step 5: Run all verification checks to ensure the 
refactoring is complete and correct.

This is the final validation step before the PR is ready.
```

---

## WHERE

### Verification Commands
- `./tools/lint_imports.sh` - Architecture boundary checks
- `./tools/tach_check.sh` - Layer dependency checks
- `mcp__code-checker__run_pylint_check` - Code quality
- `mcp__code-checker__run_mypy_check` - Type checking  
- `mcp__code-checker__run_pytest_check` - All tests pass

---

## WHAT

### Acceptance Criteria Checklist

From issue #358:

- [ ] All source files moved to `workflows/vscodeclaude/`
- [ ] Templates moved to `workflows/vscodeclaude/templates.py`
- [ ] `get_cache_refresh_minutes()` moved to `utils/user_config.py`
- [ ] `_get_coordinator()` pattern removed, replaced with direct imports
- [ ] `cli/commands/coordinator/vscodeclaude.py` deleted
- [ ] Coordinator `__init__.py` cleaned up (removed vscodeclaude + cache re-exports)
- [ ] Tests updated to patch at new locations
- [ ] No imports from CLI layer in workflows layer
- [ ] `./tools/lint_imports.sh` passes
- [ ] `./tools/tach_check.sh` passes
- [ ] `mcp__code-checker__run_pylint_check` passes
- [ ] `mcp__code-checker__run_mypy_check` passes
- [ ] `mcp__code-checker__run_pytest_check` passes
- [ ] `utils/vscodeclaude/` deleted entirely

---

## HOW

### Step-by-Step Verification

1. **Import Linter Check:**
   ```bash
   ./tools/lint_imports.sh
   ```
   Expected: All contracts pass, no violations

2. **Tach Layer Check:**
   ```bash
   ./tools/tach_check.sh
   ```
   Expected: No layer violations

3. **Pylint Check:**
   ```bash
   mcp__code-checker__run_pylint_check
   ```
   Expected: No errors or fatal issues

4. **Mypy Check:**
   ```bash
   mcp__code-checker__run_mypy_check
   ```
   Expected: No type errors

5. **Pytest Check:**
   ```bash
   mcp__code-checker__run_pytest_check
   ```
   Expected: All tests pass

---

## ALGORITHM

```
1. Run lint_imports.sh
   - If fails: fix import violations in workflows/vscodeclaude/
   
2. Run tach_check.sh  
   - If fails: check layer dependencies are correct

3. Run pylint check
   - If fails: fix code quality issues

4. Run mypy check
   - If fails: fix type annotations

5. Run pytest
   - If fails: fix test patches or logic

6. All pass → PR ready for review
```

---

## DATA

### Expected Output Summary

| Check | Expected Result |
|-------|-----------------|
| lint_imports | "All contracts passed" |
| tach_check | "No violations found" |
| pylint | No errors (E) or fatal (F) |
| mypy | "Success: no issues found" |
| pytest | All tests pass |

---

## Troubleshooting

### Common Issues

**lint_imports fails with "workflows imports from cli":**
- Check that all `_get_coordinator()` calls are removed
- Verify no imports from `mcp_coder.cli.*` in `workflows/vscodeclaude/`

**Tests fail with "module not found":**
- Verify patch paths updated from `utils.vscodeclaude` to `workflows.vscodeclaude`
- Check imports in test files match new module locations

**mypy fails with "cannot find module":**
- Ensure `__init__.py` files exist in new directories
- Check that all exports are properly defined

---

## Completion

When all checks pass, the refactoring is complete. Create a PR with:
- Title matching issue: "Refactor vscodeclaude: Move from utils to workflows layer"
- Reference issue #358
- Summary of changes made
