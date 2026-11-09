# Step 2 — Fix stale docs and tach comments

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. Make the comment-only edits to `tach.toml` (no `depends_on` changes) and fix the quality-tool sentence in `docs/architecture/enforcement.md`. Remove the Issue #011 and Issue #008 entries from `docs/tests/issues.md`. Do not touch `docs/tests/runtime_statistics.md`, `docs/tests/performance_data/`, `docs/architecture/dependencies/*` or `.importlinter`. Run the checks listed below and make them pass. Produce one commit.

## Precondition

`src/mcp_coder/mcp_tools_py.py` exports only `resolve_steps` (step 1 is done). If it still defines `has_mypy_errors`, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tach.toml`
- `docs/architecture/enforcement.md`
- `docs/tests/issues.md`

## WHAT

### `tach.toml`: comments only

1. In the cli module's `depends_on` list, change:
   ```
   { path = "mcp_coder.mcp_tools_py" }, # MCP code checking tools
   ```
   to:
   ```
   { path = "mcp_coder.mcp_tools_py" }, # resolve_steps re-export (sole mcp_tools_py importer)
   ```
2. In the `[[modules]]` block with `path = "mcp_coder.mcp_tools_py"`, replace the three comment lines
   ```
   # MCP code checking tool implementation.
   # Infrastructure service for running code quality checks.
   # Standalone module with no internal dependencies (uses only stdlib).
   ```
   with:
   ```
   # Sole importer of the mcp_tools_py package; re-exports resolve_steps.
   ```
3. In that same block, remove only the inline comments; keep the entries:
   ```
   depends_on = [
       { path = "mcp_coder.config" },
       { path = "mcp_coder.constants" },
   ]
   ```

Leave every `depends_on` entry and every other line in `tach.toml` as it is.

### `docs/architecture/enforcement.md`: "Shim boundary" section

Replace the phrase `reached only through the quality-tool boundary, today the \`mcp_coder.mcp_tools_py\` shim.` with:

`reached only through the toolkit (\`utils/toolkit_runner\`); the \`mcp_coder.mcp_tools_py\` shim only re-exports \`resolve_steps\`.`

The rest of the paragraph (the `quality_tools_isolation` and `RULES` sentences) stays as it is.

### `docs/tests/issues.md`

- Delete the whole `### ✅ Issue #011: MyPy Convenience Function Test (RESOLVED Oct 14)` block, through the `---` separator that follows it.
- Delete the whole `### ✅ Issue #008: MyPy Full Check Regression (MASSIVELY IMPROVED Oct 9)` block, through the `---` separator that follows it. The `## Resolved Issues` heading stays, followed by Issue #006.

## HOW

No code changes and no new integration points.

## ALGORITHM

None.

## DATA

None.

## Checks (all must pass)

1. `mcp__mcp-tools-py__run_tach_check` (confirms `tach.toml` still parses and is valid)
2. `mcp__mcp-tools-py__run_pylint_check`
3. `mcp__mcp-tools-py__run_mypy_check`
4. `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`

## Commit

`docs(mcp_tools_py): describe shim as resolve_steps re-export (#1388)`
