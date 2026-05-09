# Step 5 — POSIX templates + `create_startup_script` POSIX path

**Reference:** [summary.md](./summary.md) — issue #963. Depends on Step 2 (`_MCP_CONFIG_FILES`).

## Goal

Add six POSIX template constants paralleling the existing six Windows ones, and replace the `NotImplementedError` branch in `create_startup_script` with a working POSIX path. After this step, `mcp-coder vscodeclaude launch` works end-to-end on macOS and Linux.

## WHERE

- **Modify:** `src/mcp_coder/workflows/vscodeclaude/templates.py` — add POSIX constants.
- **Modify:** `src/mcp_coder/workflows/vscodeclaude/workspace.py` — function `create_startup_script`.
- **Modify:** `tests/workflows/vscodeclaude/test_workspace_startup_script.py` — parametrize over Windows / Darwin / Linux.

## WHAT

### `templates.py` — six new constants

Each parallels its Windows counterpart in role:

| New constant | Mirrors |
|---|---|
| `STARTUP_SCRIPT_POSIX` | `STARTUP_SCRIPT_WINDOWS` |
| `INTERVENTION_SCRIPT_POSIX` | `INTERVENTION_SCRIPT_WINDOWS` |
| `VENV_SECTION_POSIX` | `VENV_SECTION_WINDOWS` |
| `INTERACTIVE_ONLY_SECTION_POSIX` | `INTERACTIVE_ONLY_SECTION_WINDOWS` |
| `AUTOMATED_SECTION_POSIX` | `AUTOMATED_SECTION_WINDOWS` |
| `AUTOMATED_RESUME_SECTION_POSIX` | `AUTOMATED_RESUME_SECTION_WINDOWS` |
| `INTERACTIVE_RESUME_WITH_COMMAND_POSIX` | `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS` |

(Seven total — the table above is paired listing.)

Required content highlights (KISS — POSIX scripts are deliberately shorter than Windows):

- **`STARTUP_SCRIPT_POSIX`** — header inlined at top:
  ```
  #!/usr/bin/env bash
  set -euo pipefail
  trap 'read -r -p "Script failed (Enter to close)..."' ERR
  ```
  Then banner echoes (single-quoted), `{venv_section}`, `{command_sections}`. Banner format slots: `{emoji}`, `{issue_number}`, `{title}`, `{repo}`, `{status}`, `{issue_url}`.

- **`INTERVENTION_SCRIPT_POSIX`** — same 3-line header inlined, banner, `{venv_section}`, intervention warning block, bare `claude` invocation.

- **`VENV_SECTION_POSIX`** — sets:
  - `MCP_CODER_VENV_PATH={mcp_coder_install_path}/.venv/bin`
  - `MCP_CODER_PROJECT_DIR={session_folder_path}`
  - `MCP_CODER_VENV_DIR={session_folder_path}/.venv`
  - `MCP_TIMEOUT=30000`
  - `UV_GIT_SHALLOW=0`
  - Prepends `MCP_CODER_VENV_PATH` to `PATH`.
  - If `.venv/bin/activate` missing → `uv venv` → activate → `uv sync --extra dev`.
  - Else → activate.
  - Re-prepends `MCP_CODER_VENV_PATH` to `PATH` after activation (parallels the Windows comment about activate.bat overwriting PATH).
  - `uv pip install -e . --no-deps`.
  - **No retry loop**, **no GitHub install section**.

- **`INTERACTIVE_ONLY_SECTION_POSIX`** — single command, no step labels:
  ```
  claude "{command} {issue_number}"
  ```

- **`AUTOMATED_SECTION_POSIX`** — first multi-command step. Captures session id:
  ```
  SESSION_ID=$(mcp-coder prompt "{command} {issue_number}" --llm-method claude --output-format session-id --mcp-config {mcp_config} --timeout {timeout})
  if [ -z "$SESSION_ID" ]; then
      echo "ERROR: Failed to get session ID from automated analysis."
      exit 1
  fi
  ```

- **`AUTOMATED_RESUME_SECTION_POSIX`** — middle steps. Tolerant of failure (matches Windows "WARNING ... Continuing"):
  ```
  mcp-coder prompt "{command}" --llm-method claude --session-id "$SESSION_ID" --mcp-config {mcp_config} --timeout {timeout} || echo "WARNING: Step {step_number} encountered an error. Continuing..."
  ```
  The `|| echo` keeps the step non-fatal under `set -e`.

- **`INTERACTIVE_RESUME_WITH_COMMAND_POSIX`** — final step:
  ```
  claude --resume "$SESSION_ID" "{command}"
  ```

Format slots required: `{command}`, `{issue_number}`, `{timeout}`, `{step_number}`, `{mcp_config}`, plus the venv-section slots `{mcp_coder_install_path}` and `{session_folder_path}`.

### `workspace.py` — `create_startup_script`

Replace the `else: raise NotImplementedError(...)` branch with a POSIX path. Signature unchanged.

Resolution outline:

1. `mcp_config_filename = _MCP_CONFIG_FILES.get(platform.system(), ".mcp.json")` — must be `.mcp.macos.json` or `.mcp.linux.json` here.
2. Verify `(folder_path / mcp_config_filename).exists()`; raise `FileNotFoundError` with a clear message if missing. (Belt-and-braces — `validate_mcp_json` already checks this earlier in the workflow, but `create_startup_script` is also called from `regenerate_session_files`.)
3. Resolve `mcp_coder_install_path` (same as Windows path: argument or `get_mcp_coder_install_path()`).
4. Use `session_folder_path or folder_path`.
5. Format `VENV_SECTION_POSIX` with `{mcp_coder_install_path}` and `{session_folder_path}`. **Do not** call `_build_github_install_section()` — `skip_github_install` is a no-op on POSIX.
6. Escape title for single-quote-wrapped echoes: `title_display = (issue_title[:58] if len(issue_title) > 58 else issue_title).replace("'", "'\\''")`. No new helper function. Apply the same `'` escape to `{repo}`, `{status}`, `{issue_url}`, `{emoji}` defensively (use a tiny inline lambda or a one-liner helper inside the function — local scope only, do NOT add a module-level escape helper). The simplest form is one inline `replace` per substituted value.
7. Build `command_sections` using the same single / multi / no-command logic as Windows, substituting POSIX templates and passing `mcp_config=mcp_config_filename` to `AUTOMATED_SECTION_POSIX` / `AUTOMATED_RESUME_SECTION_POSIX`.
8. Compose `script_content` from `STARTUP_SCRIPT_POSIX` (or `INTERVENTION_SCRIPT_POSIX`).
9. Write to `folder_path / ".vscodeclaude_start.sh"`.
10. `script_path.chmod(0o755)`.
11. Return `script_path`.

The intervention path follows the same shape minus command-section logic.

## HOW

- POSIX detection: `platform.system() in {"Darwin", "Linux"}` (or simply `not is_windows` since unsupported platforms would fail at `_MCP_CONFIG_FILES` lookup anyway).
- The Windows code path is unchanged structurally — only the `else` branch is replaced.
- The MCP config filename is baked literally into the relevant section templates via `.format(mcp_config=...)`. This keeps `STARTUP_SCRIPT_POSIX` itself agnostic of the filename — it only sees pre-formatted `command_sections`.

## ALGORITHM (POSIX branch only)

```
mcp_config = _MCP_CONFIG_FILES[platform.system()]
if not (folder_path / mcp_config).exists(): raise FileNotFoundError(...)
install_path = mcp_coder_install_path or get_mcp_coder_install_path()
session_path = session_folder_path or folder_path
venv_section = VENV_SECTION_POSIX.format(mcp_coder_install_path=install_path, session_folder_path=session_path)

# title + banner field escaping
def q(s): return str(s).replace("'", "'\\''")    # local helper, function-scope
fields = {emoji, issue_number, title, repo, status, issue_url}  -> apply q() to text fields, truncate title to 58

if is_intervention:
    content = INTERVENTION_SCRIPT_POSIX.format(**fields, venv_section=venv_section)
else:
    validate commands list (same as Windows)
    if len == 1:   sections = INTERACTIVE_ONLY_SECTION_POSIX.format(command=cmd, issue_number=...)
    elif len > 1:  for i, cmd in commands:
                       if i == 0:           AUTOMATED_SECTION_POSIX.format(..., mcp_config=mcp_config)
                       elif not last:       AUTOMATED_RESUME_SECTION_POSIX.format(..., mcp_config=mcp_config)
                       if last:             INTERACTIVE_RESUME_WITH_COMMAND_POSIX.format(...)
    else:          sections = ""
    content = STARTUP_SCRIPT_POSIX.format(**fields, venv_section=venv_section, command_sections=sections)

path = folder_path / ".vscodeclaude_start.sh"
path.write_text(content, encoding="utf-8")
path.chmod(0o755)
return path
```

## DATA

- Return type unchanged: `Path`.
- New file produced: `.vscodeclaude_start.sh`, mode `0o755` (where supported).

## Tests (write first)

In `tests/workflows/vscodeclaude/test_workspace_startup_script.py`, parametrize the existing tests over `("Windows", "Darwin", "Linux")` where the assertions are platform-relevant. For new POSIX-specific assertions, cover:

1. **Filename**: POSIX produces `.vscodeclaude_start.sh`, not `.bat`.
2. **Shebang**: first line is `#!/usr/bin/env bash`.
3. **Failure UX**: `set -euo pipefail` and `trap 'read -r -p "Script failed (Enter to close)..."' ERR` are present.
4. **MCP config baking**: Darwin → `--mcp-config .mcp.macos.json`; Linux → `--mcp-config .mcp.linux.json`. Use a multi-command status (e.g. `status-01:created`) so `AUTOMATED_SECTION_POSIX` is invoked and the substitution is observable.
5. **Venv activation form**: contains `source .venv/bin/activate` (POSIX) and not `activate.bat` (POSIX-only assertion).
6. **No GitHub install section on POSIX**: even when `_build_github_install_section()` would normally emit content, POSIX scripts must not contain `uv pip install --no-deps` patterns from the GitHub override path. Verify by writing a fake `pyproject.toml` with `[tool.mcp-coder.install-from-github]` configured and confirming the section's marker (`=== GitHub override installs ===` or equivalent) is absent on POSIX.
7. **Executable bit**: `stat.S_IXUSR` is set on the resulting file. **Must** be marked `pytest.mark.skipif(sys.platform == "win32", reason="...")` because Windows ignores `chmod(0o755)` for the executable bit on regular files.
8. **Single-command flow on POSIX**: contains `claude "<command> <issue>"`, no `mcp-coder prompt`, no step labels, no `--session-id`.
9. **Multi-command flow on POSIX**: contains `mcp-coder prompt "..."`, captures `SESSION_ID=$(...)`, last step uses `claude --resume "$SESSION_ID"`.
10. **Title escaping**: pass an issue title containing a single quote, e.g. `"It's broken"`, and assert it appears as `'It'\''s broken'` inside the generated script. Confirm the script's first banner echo is still syntactically valid (single-quoted, balanced).
11. **Per-platform test fixture**: tests must write a fake `.mcp.macos.json` / `.mcp.linux.json` into `tmp_path` so the new existence check in `create_startup_script` doesn't fail.
12. **Missing platform MCP config**: Darwin without `.mcp.macos.json` in the folder → `FileNotFoundError` with a clear message naming the file.

Existing Windows tests keep passing unchanged after parametrization. Where a test is fundamentally Windows-only (e.g. asserts `errorlevel`), keep it pinned to `"Windows"`.

## Acceptance

- All new and parametrized tests pass on Windows.
- POSIX-only tests (executable bit) are skipped on Windows; the rest run via `monkeypatch` of `platform.system`.
- Existing `.bat` content and existing tasks.json Windows behavior are unchanged.
- pylint, mypy, pytest (with the standard exclusion marker set) clean.
- Manual verification (if accessible to the implementer): `mcp-coder vscodeclaude launch` on macOS produces a working session — script created, executable, runs via `tasks.json`, hits `claude` / `mcp-coder` against the issue. (If no Mac is available, document the limitation in the PR description.)

## LLM prompt

> Implement Step 5 from `pr_info/steps/step_5.md`, using `pr_info/steps/summary.md` for context.
>
> In `src/mcp_coder/workflows/vscodeclaude/templates.py`, add seven new POSIX template constants (`STARTUP_SCRIPT_POSIX`, `INTERVENTION_SCRIPT_POSIX`, `VENV_SECTION_POSIX`, `INTERACTIVE_ONLY_SECTION_POSIX`, `AUTOMATED_SECTION_POSIX`, `AUTOMATED_RESUME_SECTION_POSIX`, `INTERACTIVE_RESUME_WITH_COMMAND_POSIX`) following the content spec in the step doc.
>
> In `src/mcp_coder/workflows/vscodeclaude/workspace.py`, replace the `NotImplementedError` branch in `create_startup_script` with the POSIX path described in the step's ALGORITHM section. Use `_MCP_CONFIG_FILES` (from Step 2) to resolve the platform's MCP config filename and bake `--mcp-config <filename>` into the relevant section templates. Inline single-quote escaping (`replace("'", "'\\''")`) — do NOT introduce a `_escape_posix_title` helper. Skip `_build_github_install_section()` entirely on POSIX. Write the script to `.vscodeclaude_start.sh` and `chmod(0o755)`.
>
> Write the parametrized tests in `tests/workflows/vscodeclaude/test_workspace_startup_script.py` **first**, covering all twelve cases listed in the step doc. Mark the executable-bit test with `pytest.mark.skipif(sys.platform == "win32")`.
>
> Run the three required quality checks per `.claude/CLAUDE.md`. One commit, message: `Add POSIX startup script support to vscodeclaude (#963)`.
