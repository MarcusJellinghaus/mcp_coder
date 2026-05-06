# Step 2 — Hard-set `MCP_TIMEOUT` in 5 launcher scripts

> Read `pr_info/steps/summary.md` first, then this step.

## Goal

Add `MCP_TIMEOUT=30000` as a hard-set in every root launcher script, next to the existing `DISABLE_AUTOUPDATER=1` line. Same pattern, same location, same density.

This step satisfies AC #2.

## TDD

No automated test for shell scripts. Verification = the file content is correct and existing tests still pass.

## WHERE

| Path | Action |
|---|---|
| `claude.bat` | Modify (1 line + 1 comment) |
| `claude_local.bat` | Modify (same) |
| `icoder_local.bat` | Modify (same) |
| `claude.sh` | Modify (same) |
| `claude_local.sh` | Modify (same) |

## WHAT

### Windows scripts (`claude.bat`, `claude_local.bat`, `icoder_local.bat`)

Locate the existing line:

```bat
set "DISABLE_AUTOUPDATER=1"
```

Insert directly after it:

```bat
REM See src/mcp_coder/llm/claude_settings.py for canonical value
set "MCP_TIMEOUT=30000"
```

### POSIX scripts (`claude.sh`, `claude_local.sh`)

Locate the existing line:

```bash
export DISABLE_AUTOUPDATER=1
```

Insert directly after it:

```bash
# See src/mcp_coder/llm/claude_settings.py for canonical value
export MCP_TIMEOUT=30000
```

## HOW (integration points)

None — pure shell-env hardcode. Hard-set (no parent-env override) matches the existing `DISABLE_AUTOUPDATER=1` pattern in these five scripts. The comment ties readers back to the Python constant if they need to update the value.

## ALGORITHM

n/a — single-line shell edits.

## DATA

n/a — environment variable export, no return values.

## Quality gates before committing

1. Inspect each of the 5 files: the new line is right after `DISABLE_AUTOUPDATER` with the matching comment.
2. `./tools/format_all.sh` (for any incidentally touched Python — should be no-op).
3. `mcp__tools-py__run_pylint_check`
4. `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
5. `mcp__tools-py__run_mypy_check`

All must pass (these are unrelated Python checks, but mandated by CLAUDE.md after every commit).

## Commit message

```
chore(scripts): hard-set MCP_TIMEOUT=30000 in launcher scripts

Adds MCP_TIMEOUT=30000 alongside the existing DISABLE_AUTOUPDATER=1
hard-set in claude.bat, claude.sh, claude_local.bat, claude_local.sh,
and icoder_local.bat. A comment in each file points to
src/mcp_coder/llm/claude_settings.py as the canonical source.

Refs #944
```

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement Step 2 only — add `MCP_TIMEOUT=30000` plus its one-line comment to each of the five root launcher scripts (`claude.bat`, `claude_local.bat`, `icoder_local.bat`, `claude.sh`, `claude_local.sh`), placed immediately after the existing `DISABLE_AUTOUPDATER=1` line. Use Windows `set` syntax for `.bat` files and POSIX `export` for `.sh` files, matching the surrounding code. Run the quality gates (format, pylint, pytest with the standard exclusions, mypy) — all must pass. Make exactly one commit using the message in step_2.md. Do not touch any other files in this step.
