# Step 1 — Add --project-dir to all 6 watchdog set-status lines

> **Context:** See [summary.md](summary.md) for issue background.

## LLM Prompt

```
You are fixing issue #746. Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Add --project-dir to all 6 watchdog set-status lines in command_templates.py,
and add a test that asserts --project-dir is present in every watchdog line.

Follow TDD: write the test first (it will fail), then apply the fix.
Run all code quality checks (pylint, mypy, pytest) and ensure they pass.
Commit with message: "fix(coordinator): add --project-dir to watchdog set-status in command templates (#746)"
```

## WHERE

- **Test:** `tests/cli/commands/coordinator/test_commands.py` — class `TestTemplateWatchdogLines`
- **Fix:** `src/mcp_coder/cli/commands/coordinator/command_templates.py`

## WHAT — Test

Add one test method to existing `TestTemplateWatchdogLines` class:

```python
def test_watchdog_lines_include_project_dir(self) -> None:
```

## WHAT — Fix

Edit 6 string literals (watchdog `set-status` lines) to include `--project-dir`:

### Linux templates (3 lines) — add `--project-dir /workspace/repo`

1. `CREATE_PLAN_COMMAND_TEMPLATE`:
   - Before: `mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --force || true`
   - After:  `mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --project-dir /workspace/repo --force || true`

2. `IMPLEMENT_COMMAND_TEMPLATE`:
   - Before: `mcp-coder gh-tool set-status status-06f:implementing-failed --from-status status-06:implementing --force || true`
   - After:  `mcp-coder gh-tool set-status status-06f:implementing-failed --from-status status-06:implementing --project-dir /workspace/repo --force || true`

3. `CREATE_PR_COMMAND_TEMPLATE`:
   - Before: `mcp-coder gh-tool set-status status-09f:pr-creating-failed --from-status status-09:pr-creating --force || true`
   - After:  `mcp-coder gh-tool set-status status-09f:pr-creating-failed --from-status status-09:pr-creating --project-dir /workspace/repo --force || true`

### Windows templates (3 lines) — add `--project-dir %WORKSPACE%\repo`

4. `CREATE_PLAN_COMMAND_WINDOWS`:
   - Before: `mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --force`
   - After:  `mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --project-dir %WORKSPACE%\repo --force`

5. `IMPLEMENT_COMMAND_WINDOWS`:
   - Before: `mcp-coder gh-tool set-status status-06f:implementing-failed --from-status status-06:implementing --force`
   - After:  `mcp-coder gh-tool set-status status-06f:implementing-failed --from-status status-06:implementing --project-dir %WORKSPACE%\repo --force`

6. `CREATE_PR_COMMAND_WINDOWS`:
   - Before: `mcp-coder gh-tool set-status status-09f:pr-creating-failed --from-status status-09:pr-creating --force`
   - After:  `mcp-coder gh-tool set-status status-09f:pr-creating-failed --from-status status-09:pr-creating --project-dir %WORKSPACE%\repo --force`

## HOW — Test Integration

The test method goes in the existing `TestTemplateWatchdogLines` class alongside the other watchdog assertions. It iterates all 6 templates, finds each `set-status` line, and asserts `--project-dir` is present.

## ALGORITHM — Test (5 lines)

```
for each of the 6 workflow templates:
    for each line containing "set-status" and "--from-status":
        assert "--project-dir" is in that line
        if template is a Linux template:
            assert "--project-dir /workspace/repo" is in that line
        else (Windows template):
            assert "--project-dir %WORKSPACE%\repo" is in that line
    assert at least one watchdog line was found (guard against template restructuring)
```

## DATA

- **Inputs:** The 6 template string constants (already imported in test file)
- **Outputs:** Pass/fail assertions only
- **No new data structures**

## Commit

```
fix(coordinator): add --project-dir to watchdog set-status in command templates (#746)
```
