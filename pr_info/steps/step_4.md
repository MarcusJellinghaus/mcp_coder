# Step 4 — `MCP_TIMEOUT` in coordinator `command_templates.py`

> Read `pr_info/steps/summary.md` first, then this step.

## Goal

Add `MCP_TIMEOUT=30000` to every template in `src/mcp_coder/cli/commands/coordinator/command_templates.py`, in the same spot as the existing `DISABLE_AUTOUPDATER=1` line.

Workflow templates technically don't need it (they go through mcp-coder → Python), but the test templates **do** (they call `claude` directly, bypassing mcp-coder). Adding to all templates matches the existing `DISABLE_AUTOUPDATER` pattern in this same file.

This step satisfies AC #4.

## TDD

No automated test asserts the template body verbatim. Any existing tests in `tests/cli/commands/` for coordinator should still pass — verify after the change.

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Modify (8 templates, one line each) |

## WHAT

Eight templates total. For each, insert the new line **immediately after** the existing `DISABLE_AUTOUPDATER` line, using matching shell syntax. No comment required (these templates already lack comments next to `DISABLE_AUTOUPDATER`).

> **Anchor note:** the test templates (`DEFAULT_TEST_COMMAND`, `DEFAULT_TEST_COMMAND_WINDOWS`) have a different surrounding context than the workflow templates (e.g., they call `claude` directly and may have different setup lines around the env block). The rule is the same — `MCP_TIMEOUT=30000` goes immediately after `DISABLE_AUTOUPDATER=1` — but **do not** assume the surrounding lines are identical to the workflow templates. Anchor on the `DISABLE_AUTOUPDATER` line in each template independently.

### Linux templates (4) — `export MCP_TIMEOUT=30000`

| Constant | Existing anchor line |
|---|---|
| `DEFAULT_TEST_COMMAND` | `export DISABLE_AUTOUPDATER=1` |
| `CREATE_PLAN_COMMAND_TEMPLATE` | `export DISABLE_AUTOUPDATER=1` |
| `IMPLEMENT_COMMAND_TEMPLATE` | `export DISABLE_AUTOUPDATER=1` |
| `CREATE_PR_COMMAND_TEMPLATE` | `export DISABLE_AUTOUPDATER=1` |

Insert directly below each anchor:

```bash
export MCP_TIMEOUT=30000
```

### Windows templates (4) — `set MCP_TIMEOUT=30000`

| Constant | Existing anchor line |
|---|---|
| `DEFAULT_TEST_COMMAND_WINDOWS` | `set DISABLE_AUTOUPDATER=1` |
| `CREATE_PLAN_COMMAND_WINDOWS` | `set DISABLE_AUTOUPDATER=1` |
| `IMPLEMENT_COMMAND_WINDOWS` | `set DISABLE_AUTOUPDATER=1` |
| `CREATE_PR_COMMAND_WINDOWS` | `set DISABLE_AUTOUPDATER=1` |

Insert directly below each anchor:

```bat
set MCP_TIMEOUT=30000
```

## HOW (integration points)

- Templates are consumed via `.format(...)` from `coordinator/commands.py` and `coordinator/core.py`. No call-site changes — placeholders are unchanged.
- The new line lives at shell level inside the rendered job script run by Jenkins / coordinator. No Python imports.

## ALGORITHM

n/a — eight identical one-line insertions.

## DATA

n/a — string constants; each gains one line.

## Quality gates before committing

1. `./tools/format_all.sh`
2. `mcp__tools-py__run_pylint_check`
3. `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
4. `mcp__tools-py__run_mypy_check`

All must pass. Pay attention to `tests/cli/commands/` results.

## Commit message

```
chore(coordinator): set MCP_TIMEOUT=30000 in all command templates

Adds MCP_TIMEOUT=30000 next to the existing DISABLE_AUTOUPDATER=1 line
in every workflow and test template (Linux + Windows). The test
templates need it because they invoke `claude` directly; workflow
templates get it for symmetry with the DISABLE_AUTOUPDATER pattern in
the same file.

Refs #944
```

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement Step 4 only — in `src/mcp_coder/cli/commands/coordinator/command_templates.py`, add a single line setting `MCP_TIMEOUT=30000` immediately after the existing `DISABLE_AUTOUPDATER=1` line in each of the 8 templates listed in step_4.md (4 Linux with `export`, 4 Windows with `set`). Do not add comments — the existing templates don't have them next to `DISABLE_AUTOUPDATER`. Run the quality gates (format, pylint, pytest with standard exclusions, mypy) — all must pass. Make exactly one commit using the message in step_4.md. Do not touch any other files in this step.
