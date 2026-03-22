# Step 4: Update remaining test comments + full quality checks

> **Context**: Read `pr_info/steps/summary.md` for the full design. This step updates test comments and runs final verification.

## 4a. Update `tests/workflows/vscodeclaude/test_issues.py`

**WHERE**: `tests/workflows/vscodeclaude/test_issues.py` — class `TestIsStatusEligibleForSession`

**WHAT**: Update comments only (no logic changes — the code under test was already updated in step 2).

- Comment `# Eligible statuses (have initial_command)` → `# Eligible statuses (have commands)`
- Comment `# Ineligible - pr-created (has config but null initial_command)` → `# Ineligible - pr-created (has config but no commands)`

## 4b. Update `tests/workflows/vscodeclaude/test_cleanup.py`

**WHERE**: `tests/workflows/vscodeclaude/test_cleanup.py`

**WHAT**: Update comments that reference `initial_command`:
- Any comment mentioning `initial_command` → `commands`
- Search for `initial_command` in test comments and docstrings

Note: The cleanup test code itself uses `is_status_eligible_for_session()` which was already updated in step 2. The test mocks patch that function, so no mock changes are needed — only comment text.

## 4c. Full quality checks

Run all three quality checks to verify the complete implementation:

```
mcp__tools-py__run_pylint_check()
mcp__tools-py__run_mypy_check()
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
```

All checks must pass. Fix any issues found before completing.

## Completion checklist

- [ ] `labels.json` uses `commands` list (no `initial_command`/`followup_command`)
- [ ] `templates.py` has new templates, old ones removed
- [ ] `workspace.py` generates correct scripts for single-command and multi-command flows
- [ ] `issues.py` eligibility checks `commands` list
- [ ] All docstrings updated (cleanup.py, __init__.py)
- [ ] All test assertions updated (test_types.py, test_workspace.py)
- [ ] All test comments updated (test_issues.py, test_cleanup.py)
- [ ] pylint passes
- [ ] mypy passes
- [ ] pytest passes
