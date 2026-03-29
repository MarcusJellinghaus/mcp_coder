# Step 4: `tools/reinstall.bat` — Restructure for End-Users

## Context

See `pr_info/steps/summary.md` for full context. This is step 4 of 5.

## Goal

Restructure `tools/reinstall.bat` following the p_tools `reinstall_local.bat` pattern: venv guard, layered install, entry point verification. Change from editable to non-editable PyPI install.

**Purpose:** Non-editable PyPI install (`uv pip install mcp-coder[dev]`) for end-users.

**Note:** This changes from editable to non-editable install. Developers should use `tools\reinstall_local.bat` (step 5) instead. Consider printing a guidance message during install.

## WHERE

- `tools/reinstall.bat`

## WHAT

Replace the current verbose 7-step script with the cleaner p_tools pattern:

### Sections

1. **Venv guard** — verify `VIRTUAL_ENV` matches `%CD%\.venv` (or no venv active)
2. **Prereqs** — check `uv` available, create `.venv` if missing
3. **Uninstall** — clean slate for mcp-coder + MCP packages
4. **Install** — `uv pip install mcp-coder[dev]` (non-editable, from PyPI)
5. **Entry point verification** — check `mcp-tools-py.exe`, `mcp-workspace.exe`, `mcp-coder.exe` exist
6. **CLI verification** — run `--help` on each to confirm they work
7. **Activate** — escape `setlocal` and activate the venv for the caller

## HOW

Follow `p_tools/tools/reinstall_local.bat` structure (read via `read_reference_file`).

**Key differences from p_tools version:**
- `uv pip install mcp-coder[dev]` instead of `-e ".[dev]"` (non-editable)
- No GitHub override step (end-users use PyPI versions)
- No LangChain/MLflow step (pulled in by `[dev]` extra)

**Key differences from current `tools/reinstall.bat`:**
- Adds wrong-venv guard at the top
- Non-editable instead of editable install
- Uses `--python` flag for explicit venv targeting (like p_tools)
- Adds file-existence checks for entry points
- Escapes `setlocal` to persist venv activation to caller

## ALGORITHM

```
1. Resolve PROJECT_DIR and VENV_DIR from script location
2. If VIRTUAL_ENV set and != VENV_DIR → error with guidance
3. Check uv available; create .venv if missing
4. uv pip uninstall mcp-coder mcp-tools-py mcp-config mcp-workspace
5. uv pip install mcp-coder[dev] --python VENV_SCRIPTS\python.exe
6. Verify mcp-tools-py.exe, mcp-workspace.exe, mcp-coder.exe exist in VENV_SCRIPTS
7. Run --help on each; endlocal & activate venv for caller
```

## DATA

No return values. Side effects:
- Packages installed in `%CD%\.venv`
- Venv activated in caller's shell

## Testing

- **TDD**: Not applicable (batch file)
- **Manual verification**:
  1. Run with correct venv active → should complete successfully
  2. Run with wrong venv active → should error with guidance
  3. Run with no venv → should create `.venv` and install

## Commit

```
chore: restructure reinstall.bat with venv guard and non-editable install

Add wrong-venv guard, switch to non-editable PyPI install, add entry
point file-existence verification following p_tools pattern.
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for context.
Also read the current tools/reinstall.bat and p_tools/tools/reinstall_local.bat
(via read_reference_file) as the template to follow.

Restructure tools/reinstall.bat following the algorithm in step_4.md.
Key points:
- Follow p_tools reinstall_local.bat structure closely
- Use non-editable install: uv pip install mcp-coder[dev]
- No GitHub override step (that's for reinstall_local.bat)
- Add wrong-venv guard at the top
- Use --python flag for explicit venv targeting
- Escape setlocal scope to persist activation to caller
```
