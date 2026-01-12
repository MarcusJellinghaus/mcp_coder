# Step 3: Update .importlinter and Verify

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.

Update .importlinter to remove the exception rule for base_manager, then verify 
the Git Library Isolation contract passes.

Follow the specifications below exactly.
```

## WHERE

**File to modify:** `.importlinter`

## WHAT

### Remove Exception Rule

**Find this section (around lines 105-115):**
```ini
[importlinter:contract:git_library_isolation]
name = GitPython Library Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    git
ignore_imports =
    mcp_coder.utils.git_operations.** -> git
    # Known violation: github_operations uses git.Repo for repository path
    # TODO: Refactor to use git_operations instead (issue #276)
    mcp_coder.utils.github_operations.base_manager -> git
```

**Change to:**
```ini
[importlinter:contract:git_library_isolation]
name = GitPython Library Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    git
ignore_imports =
    mcp_coder.utils.git_operations.** -> git
```

### Lines to Remove

Remove these 3 lines:
```ini
    # Known violation: github_operations uses git.Repo for repository path
    # TODO: Refactor to use git_operations instead (issue #276)
    mcp_coder.utils.github_operations.base_manager -> git
```

## HOW

This is a configuration file change - simply remove the exception lines.

## ALGORITHM

```
1. Open .importlinter
2. Find git_library_isolation contract section
3. Remove the 3 lines (2 comments + 1 ignore rule)
4. Save file
5. Run lint-imports to verify
```

## DATA

N/A - Configuration file change only.

## Verification

### Run Import Linter
```bash
lint-imports
```

### Expected Output
The `GitPython Library Isolation` contract should pass without the exception.

### Run All Tests
```bash
pytest tests/utils/github_operations/test_base_manager.py -v
```

### Full Test Suite
```bash
pytest
```

## Acceptance Criteria Checklist

After completing all 3 steps, verify:

- [ ] `base_manager.py` has no `import git` statement
- [ ] `base_manager.py` uses `from mcp_coder.utils import git_operations`
- [ ] `base_manager.py` has no `self._repo` attribute
- [ ] `test_base_manager.py` has no `import git` statement
- [ ] `test_base_manager.py` mocks `git_operations` functions
- [ ] `.importlinter` has no exception for `base_manager -> git`
- [ ] `lint-imports` passes
- [ ] All tests pass
- [ ] Error message `"Directory is not a git repository: {project_dir}"` preserved
