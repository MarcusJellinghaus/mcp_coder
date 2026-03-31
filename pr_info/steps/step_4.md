# Step 4: Batch Files — icoder.bat + icoder_local.bat

> **Reference:** See `pr_info/steps/summary.md` for full context.

## Goal

Create `icoder.bat` (production) and `icoder_local.bat` (dev) following the exact
pattern of `claude.bat` / `claude_local.bat`. Only the final launch command differs.

## WHERE

- **Create:** `icoder.bat`
- **Create:** `icoder_local.bat`

## WHAT

### `icoder.bat` — Production launcher

Copy `claude.bat` exactly, changing only:
- Header comment: reference iCoder instead of Claude Code
- Echo line: "Starting iCoder with:" instead of "Starting Claude Code with:"
- **Final launch line:** `mcp-coder icoder %*` instead of `C:\Users\%USERNAME%\.local\bin\claude.exe %*`

Everything else (tool env discovery, project env activation, MCP tool verification,
env var setup) remains identical.

### `icoder_local.bat` — Dev launcher

Copy `claude_local.bat` exactly, changing only:
- Header comment: reference iCoder instead of Claude Code
- Echo line: "Starting iCoder (developer mode) with:" instead of "Starting Claude Code (developer mode) with:"
- **Final launch line:** `.venv\Scripts\python -m mcp_coder icoder %*` instead of `C:\Users\%USERNAME%\.local\bin\claude.exe %*`

Everything else (Step 0 .venv check, tool env discovery, editable install verification,
MCP tool verification, env var setup) remains identical.

## HOW

No integration points — these are standalone batch files in the project root.

## ALGORITHM

No algorithm — these are configuration/launcher files.

## DATA

No data structures. The batch files set these env vars (same as existing):
- `MCP_CODER_VENV_PATH`, `MCP_CODER_VENV_DIR`, `MCP_CODER_PROJECT_DIR`
- `DISABLE_AUTOUPDATER=1`

## Testing

No automated tests — batch files are verified manually. The existing `claude.bat`
pattern is already established and trusted.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for full context.

Implement step 4: Create icoder.bat and icoder_local.bat by copying claude.bat and
claude_local.bat respectively, changing only the header comments, echo messages, and
final launch commands as specified. Run all three MCP code quality checks after changes.
Commit message: "icoder: add icoder.bat and icoder_local.bat launchers"
```
