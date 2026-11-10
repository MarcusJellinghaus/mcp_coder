# Step 7: Linux implement template points the checks at the project venv

mcp-tools-py runs checks in the project env only when `VIRTUAL_ENV` points at it. On the Linux executor this is a no-op until #1204 / AutoRunner#59 provide a venv.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`. Implement step 7 only: add the tests to `tests/cli/commands/coordinator/test_command_templates.py` first, then add the `VIRTUAL_ENV` line to `IMPLEMENT_COMMAND_TEMPLATE`. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `tests/cli/commands/coordinator/test_command_templates.py`

## WHAT
Insert one line in `IMPLEMENT_COMMAND_TEMPLATE`, after `export MCP_TIMEOUT=30000` and before the `mcp-coder ... implement` line:
```bash
if [ -x .venv/bin/python ]; then export VIRTUAL_ENV=/workspace/repo/.venv; fi
```
Optionally define it as a module constant `_PROJECT_VENV_LINE` and reference it in the test; the template itself stays a literal string.

## HOW
- No `$`, `${...}` or backticks in this line: `str.format` forbids braces, and AutoRunner embeds the template in an outer `bash -c "…"` where `$` and backticks expand on the Jenkins host.
- `if` block, not `[ ] && export`, because the executor runs under `set -e`.
- Guard on the interpreter: a `.venv` without `bin/python` would make mcp-tools-py raise.
- `PATH` is not touched, so `mcp-coder` stays the tool install.
- Only the Linux template; `IMPLEMENT_COMMAND_WINDOWS` is unchanged.

## ALGORITHM
None.

## DATA
Unchanged template signature (`{branch_name}`, `{log_level}`).

## Tests (write first)
- The exact line is present in `IMPLEMENT_COMMAND_TEMPLATE`.
- It comes before the line containing `mcp-coder --log-level {log_level} implement`.
- That line contains no `$` and no backtick. Assert on that line only — the template already has `RC=$?` elsewhere.
- `IMPLEMENT_COMMAND_TEMPLATE.format(branch_name="b", log_level="INFO")` still works (existing tests likely cover this).
