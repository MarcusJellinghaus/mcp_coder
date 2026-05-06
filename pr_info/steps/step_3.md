# Step 3 — `MCP_TIMEOUT` in VSCodeClaude `VENV_SECTION_WINDOWS` template

> Read `pr_info/steps/summary.md` first, then this step.

## Goal

Hard-set `MCP_TIMEOUT=30000` in the Windows venv-setup template that VSCodeClaude bakes into generated startup scripts.

This step satisfies AC #3.

**Important nuance:** unlike the launcher scripts and the coordinator templates, this template does **not** currently set `DISABLE_AUTOUPDATER`. We only add `MCP_TIMEOUT` here — adding `DISABLE_AUTOUPDATER` is out of scope for this issue.

## TDD

No automated test for the template body. Existing VSCodeClaude tests in `tests/workflows/vscodeclaude/` should still pass after the change (they assert structural elements, not the exact body).

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Modify (1 line + 1 comment in `VENV_SECTION_WINDOWS`) |

## WHAT

In `VENV_SECTION_WINDOWS`, find the block:

```bat
REM Set MCP environment variables (for MCP server configuration)
set "MCP_CODER_PROJECT_DIR={session_folder_path}"
set "MCP_CODER_VENV_DIR={session_folder_path}\.venv"
```

Insert directly after the `MCP_CODER_VENV_DIR` line, **before** the next blank line / next section:

```bat

REM See src/mcp_coder/llm/claude_settings.py for canonical value
set "MCP_TIMEOUT=30000"
```

(Pick a placement consistent with the surrounding "Set MCP environment variables" block. Adjust whitespace to match the existing style — no extra blank lines beyond what the surrounding block uses.)

## HOW (integration points)

- Affects any `.vscodeclaude_start.bat` generated after this change. No call-site changes — `VENV_SECTION_WINDOWS` is consumed via `.format(...)` from `STARTUP_SCRIPT_WINDOWS` / `INTERVENTION_SCRIPT_WINDOWS`.
- No format-string placeholders introduced — `30000` is hard-coded.
- VSCodeClaude tests assert template structure; check that none of them encode the exact byte length / line count of `VENV_SECTION_WINDOWS` (a quick `grep` on `tests/workflows/vscodeclaude/` for `VENV_SECTION_WINDOWS` and similar fixed-string assertions). If any do, update accordingly — but expect this not to be needed.

## ALGORITHM

n/a — single-line template edit.

## DATA

n/a — `VENV_SECTION_WINDOWS` remains a `str` constant; one extra line in the body.

## Quality gates before committing

1. `./tools/format_all.sh`
2. `mcp__tools-py__run_pylint_check`
3. `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
4. `mcp__tools-py__run_mypy_check`

All must pass. Pay attention to `tests/workflows/vscodeclaude/` results.

## Commit message

```
chore(vscodeclaude): hard-set MCP_TIMEOUT in VENV_SECTION_WINDOWS

Generated VSCodeClaude startup scripts now export MCP_TIMEOUT=30000
alongside the other MCP_CODER_* variables. A comment points to
src/mcp_coder/llm/claude_settings.py as the canonical source.

Refs #944
```

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement Step 3 only — in `src/mcp_coder/workflows/vscodeclaude/templates.py`, modify the `VENV_SECTION_WINDOWS` raw-string template to add `set "MCP_TIMEOUT=30000"` (with a one-line comment pointing to `claude_settings.py`) right after the existing `MCP_CODER_VENV_DIR` set. Do **not** add `DISABLE_AUTOUPDATER` to this template — that's intentionally out of scope. Run the quality gates (format, pylint, pytest with standard exclusions, mypy) — all must pass. If any vscodeclaude test fails because it encodes the exact body, update the test to reflect the new line. Make exactly one commit using the message in step_3.md. Do not touch any other files in this step.
