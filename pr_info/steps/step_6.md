# Step 6 — Documentation: `MCP_TIMEOUT` row in environments table

> Read `pr_info/steps/summary.md` first, then this step.

## Goal

Add an `MCP_TIMEOUT` row to the Environment Variables Reference table in `docs/environments/environments.md`, sibling to the existing `DISABLE_AUTOUPDATER` row.

This step satisfies AC #6.

## TDD

No automated test for documentation. Verification = the table renders with one extra row and the existing rows are unchanged.

## WHERE

| Path | Action |
|---|---|
| `docs/environments/environments.md` | Modify (add 1 row to Environment Variables Reference table) |

## WHAT

Locate the existing table row:

```markdown
| `DISABLE_AUTOUPDATER` | `1` | Prevents Claude CLI auto-updates during automation | `command_templates.py`, batch launchers | Claude CLI |
```

Insert directly after it:

```markdown
| `MCP_TIMEOUT` | `30000` (ms) | MCP server startup timeout for Claude CLI; raises the default 5 s window so cold-start servers are not marked failed | `claude_settings.py`, `env.py`, `command_templates.py`, `templates.py` (vscodeclaude), batch launchers | Claude CLI |
```

Keep column alignment as a markdown table — exact spacing is not load-bearing because markdown renderers ignore inner alignment, but try to match the visual style of the surrounding rows.

## HOW (integration points)

- Pure docs change. No code, no imports.
- Cross-references: the "Set by" column lists all the places this PR touches — keep it in sync if anyone moves files later.

## ALGORITHM

n/a — documentation row insertion.

## DATA

n/a — Markdown table row.

## Quality gates before committing

1. Render-check: open the file in any markdown preview and confirm the new row appears with correct columns. (Optional but recommended.)
2. `./tools/format_all.sh` (no-op on `.md`).
3. `mcp__tools-py__run_pylint_check`
4. `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
5. `mcp__tools-py__run_mypy_check`

All must pass.

## Commit message

```
docs(environments): add MCP_TIMEOUT row to env vars reference table

Documents MCP_TIMEOUT (default 30000 ms) in the Environment Variables
Reference table in docs/environments/environments.md, sibling to the
existing DISABLE_AUTOUPDATER row.

Refs #944
```

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement Step 6 only — in `docs/environments/environments.md`, add a single new row to the Environment Variables Reference table immediately after the existing `DISABLE_AUTOUPDATER` row. Use the row content provided in step_6.md. Run the quality gates (format, pylint, pytest with standard exclusions, mypy) — all must pass. Make exactly one commit using the message in step_6.md. Do not touch any other files in this step.
