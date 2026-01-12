# Step 2: Update .importlinter Configuration

## LLM Prompt
```
Implement Step 2 of Issue #277. Reference: pr_info/steps/summary.md

Remove the ignore_imports exception from the external_services contract in .importlinter.
Remove the "Known violation" comments.
Run lint-imports to verify the contract passes.
```

## WHERE

**File to modify:**
- `.importlinter`

## WHAT

Remove the exception that was allowing the architectural violation.

**Current configuration (lines ~72-82):**
```ini
# Known violation (issue #277):
# - mcp_coder.utils.github_operations.pr_manager imports from mcp_coder.utils
#   which transitively imports jenkins_operations via __init__.py
#   -> Solution: Refactor utils/__init__.py to not re-export all submodules
# -----------------------------------------------------------------------------
[importlinter:contract:external_services]
name = External Service Integrations Independence
type = independence
modules =
    mcp_coder.utils.github_operations
    mcp_coder.utils.jenkins_operations
ignore_imports =
    mcp_coder.utils.github_operations.pr_manager -> mcp_coder.utils
```

**New configuration:**
```ini
# -----------------------------------------------------------------------------
[importlinter:contract:external_services]
name = External Service Integrations Independence
type = independence
modules =
    mcp_coder.utils.github_operations
    mcp_coder.utils.jenkins_operations
```

## HOW

1. Open `.importlinter`
2. Find the `[importlinter:contract:external_services]` section
3. Remove the 4-line "Known violation" comment block
4. Remove the `ignore_imports` line and its value

## ALGORITHM

```
1. Locate external_services contract section
2. Delete comment lines starting with "# Known violation (issue #277)"
3. Delete "ignore_imports =" line
4. Delete "    mcp_coder.utils.github_operations.pr_manager -> mcp_coder.utils" line
5. Run lint-imports to verify
```

## DATA

No data structures. Configuration file change only.

## TEST VERIFICATION

Run import linter:
```bash
lint-imports
```

Expected output should show all contracts passing, including "External Service Integrations Independence".

## ACCEPTANCE CRITERIA

- [ ] "Known violation" comments removed
- [ ] `ignore_imports` exception removed from `external_services` contract
- [ ] `lint-imports` command passes without errors
- [ ] Full test suite passes: `pytest tests/ -v`
