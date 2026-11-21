# Step 6 — Coordinator test templates (Scope 3)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_6.md`).
> Implement Step 6 only: drop the mcp-tools-py probe lines from the coordinator
> test templates and make the Windows template run `mcp-coder verify
> --project-dir %WORKSPACE%\repo`. Tests first, then code. Run format, pylint,
> mypy and the fast pytest set. One commit.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- Tests pinning the templates under `tests/cli/commands/coordinator/` (search
  for `DEFAULT_TEST_COMMAND`)

## WHAT

- `DEFAULT_TEST_COMMAND`: delete `which mcp-tools-py && mcp-tools-py --help`.
- `DEFAULT_TEST_COMMAND_WINDOWS`: delete `where mcp-tools-py` and
  `mcp-tools-py --version`; `mcp-coder verify` → `mcp-coder verify --project-dir %WORKSPACE%\repo`.
  Its exit code stays unchecked, as today.
- Check the docstring near line 164 ("points mcp-tools-py checks at the project
  venv") — keep it if it describes the venv setup lines, which stay.

## HOW

Plain string edits. Step 4 already passes the resolved MCP config path to
`claude mcp list`, so `--project-dir` makes `verify` check the repo's `.mcp.json`.

## DATA

None.

## Tests (write first)

- Neither rendered template contains `mcp-tools-py`.
- The Windows template contains `mcp-coder verify --project-dir %WORKSPACE%\repo`.
