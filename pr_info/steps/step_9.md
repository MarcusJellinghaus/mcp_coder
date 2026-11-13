# Step 9: Linux Jenkins templates run `mcp-coder setup`

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_9.md`) only. Step 4 must be done: if `mcp-coder setup` is not a registered CLI command, write one line to `pr_info/.blocked.txt` and stop.
Write the tests first, then the implementation. Windows templates must stay byte-identical. Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Modify `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- Create `tests/cli/commands/coordinator/test_command_templates_setup.py`
- Adjust `tests/cli/commands/coordinator/test_command_templates.py` only where an existing assertion contradicts the new text

## WHAT

```python
def _watchdog(failed: str, current: str) -> str:
    """mcp-coder gh-tool set-status <failed> --from-status <current> --project-dir /workspace/repo --force || true"""

def _linux_setup_template(command: str, failed: str, current: str, *, archive_plan_sessions: bool = True) -> str:
    """Full Linux template for a workflow that needs the project set up."""

IMPLEMENT_COMMAND_TEMPLATE = _linux_setup_template("implement", "status-06f:implementing-failed", "status-06:implementing")
FIX_CI_COMMAND_TEMPLATE = _linux_setup_template("fix-ci", "status-83:ci-fix-failed", "status-82:fixing-ci")
FIX_CONFLICT_COMMAND_TEMPLATE = _linux_setup_template("fix-conflict", "status-73:merge-conflict-failed", "status-72:fixing-merge-conflict", archive_plan_sessions=False)
REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE = _linux_setup_template("review-implementation", "status-17f:code-review-failed", "status-17i:code-reviewing")
```

## Rendered shape (before `str.format`)

```
git checkout {branch_name}
git pull
if ! mcp-coder setup --project-dir /workspace/repo; then
<watchdog>
exit 1
fi
if [ -x .venv/bin/python ]; then export VIRTUAL_ENV=/workspace/repo/.venv; fi
export DISABLE_AUTOUPDATER=1
export MCP_TIMEOUT=30000
which mcp-coder && mcp-coder --version
which claude && claude --version
mcp-coder --log-level {log_level} <command> --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?
echo RC=$RC

<watchdog>

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions      # omitted for fix-conflict
ls -la logs

exit $RC
```

## HOW

- Build the text with plain string concatenation (or f-strings with doubled braces) so `{branch_name}` / `{log_level}` remain `str.format` placeholders.
- New lines contain no `$`, braces or backticks (AutoRunner's outer `bash -c "…"`); `set -e` safety comes from the `if !` / `if [ … ]` blocks.
- Implement's old `VIRTUAL_ENV` line before `which` moves to after setup (its explanatory comment moves to the helper).
- `DEFAULT_TEST_COMMAND`: `source .venv/bin/activate` → `if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi`.
- create-plan, create-pr, review-plan Linux templates and all Windows templates unchanged.

## Tests

- For each of the four: setup line appears after `git pull` and before the workflow command; the failure block contains the template's own watchdog line and `exit 1`; `VIRTUAL_ENV` line comes after setup; the watchdog line appears twice; `.format(log_level="info", branch_name="b", issue_number=1)` succeeds; the new lines contain no `$`, `{`, `}` or backtick.
- create-plan / create-pr / review-plan Linux templates contain no `mcp-coder setup`.
- Windows templates contain no `mcp-coder setup`.
- Test template uses the conditional activation and no bare `source .venv/bin/activate` line.

## DATA

Module-level `str` constants (unchanged names and `WORKFLOW_TEMPLATES` mapping).
