# Step 5: `tools/reinstall_local.bat` — New Developer Install Script

## Context

See `pr_info/steps/summary.md` for full context. This is step 5 of 5.

## Goal

Create `tools/reinstall_local.bat` for developers: editable install with dev deps + GitHub overrides for MCP sub-packages.

**Purpose:** Editable install for development, with MCP packages from GitHub (latest) instead of PyPI (released).

## WHERE

- `tools/reinstall_local.bat` (new file)

## WHAT

Nearly identical to `p_tools/tools/reinstall_local.bat` — that script was already written for mcp-coder's use case. Adapt it for this repo's location.

### Sections

1. **Venv guard** — verify `VIRTUAL_ENV` matches `%CD%\.venv`
2. **Prereqs** — check `uv`, create `.venv` if missing
3. **Uninstall** — `mcp-coder`, `mcp-tools-py`, `mcp-config`, `mcp-workspace`
4. **Editable install** — `uv pip install -e ".[dev]"` (editable with dev deps)
5. **GitHub overrides** — reinstall MCP packages from GitHub `--no-deps`
6. **LangChain/MLflow** — install additional deps
7. **Entry point verification** — file existence + `--help` checks
8. **Activate** — escape `setlocal`, activate venv for caller

## HOW

Use `p_tools/tools/reinstall_local.bat` as the direct template. The logic is identical — the p_tools version already installs mcp-coder editable and overrides MCP packages from GitHub.

**Differences from p_tools version:**
- Header comment says "mcp-coder" instead of "mcp-tools-py"
- Script lives at `tools/reinstall_local.bat` in this repo

**Differences from `tools/reinstall.bat` (step 4):**
- Editable install (`-e ".[dev]"`) instead of non-editable
- Adds GitHub override step for MCP sub-packages
- Adds LangChain/MLflow install step

## ALGORITHM

```
1. Resolve PROJECT_DIR, VENV_DIR from script location
2. If VIRTUAL_ENV set and != VENV_DIR → error
3. Check uv; create .venv if missing
4. uv pip uninstall mcp-coder mcp-tools-py mcp-config mcp-workspace
5. uv pip install -e ".[dev]" --python VENV_SCRIPTS\python.exe
6. uv pip install --no-deps mcp-tools-py@git+https://...  (+ mcp-workspace, mcp-config)
7. uv pip install langchain langchain-anthropic mlflow
8. Verify .exe entry points exist and --help works
9. endlocal & activate venv
```

## DATA

No return values. Side effects:
- Packages editable-installed in `%CD%\.venv`
- MCP packages overridden from GitHub
- Venv activated in caller's shell

## Testing

- **TDD**: Not applicable (batch file)
- **Manual verification**:
  1. Run from project root → should install everything and verify entry points
  2. Run with wrong venv → should error
  3. After install: `pip show mcp-coder` should show `Editable project location`
  4. After install: `pip show mcp-tools-py` should show GitHub source

## Commit

```
chore: add tools/reinstall_local.bat for developer editable installs

New script for developers: editable install with dev deps, MCP packages
overridden from GitHub, entry point verification. Based on p_tools pattern.
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md for context.
Also read p_tools/tools/reinstall_local.bat (via read_reference_file) as
the direct template.

Create tools/reinstall_local.bat following the algorithm in step_5.md.
Key points:
- Copy p_tools/tools/reinstall_local.bat structure almost exactly
- Update header comment to say "mcp-coder" instead of "mcp-tools-py"
- Same venv guard, same layered install, same GitHub overrides
- Same entry point verification and setlocal escape pattern
- GitHub URLs: MarcusJellinghaus/mcp-tools-py, mcp-workspace, mcp-config
```
