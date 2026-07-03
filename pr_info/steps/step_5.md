# Step 5 — Rewrite `create_startup_script` to write spec + launcher

Read `pr_info/steps/summary.md` first. This is the pivot: `create_startup_script`
stops generating shell orchestration and instead serializes a `SessionSpec` and
writes the thin launcher. Both call sites (`session_launch.py`,
`session_restart.py`) keep the same signature, so they are **not** modified.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` (rewrite one function;
  delete `_escape_batch_title`)
- `tests/workflows/vscodeclaude/test_workspace_startup_script.py` (trim)
- `tests/workflows/vscodeclaude/test_workspace_startup_script_github.py` (port)
- `tests/workflows/vscodeclaude/test_startup_script_mcp_coder_path.py` (rewrite)

## WHAT
Keep the existing signature:
```python
def create_startup_script(folder_path, issue_number, issue_title, status,
    repo_name, issue_url, is_intervention, timeout=DEFAULT_PROMPT_TIMEOUT,
    mcp_coder_install_path=None, session_folder_path=None,
    skip_github_install=False) -> Path
```
New body: resolve config → build `SessionSpec` → `write_session_spec` → write
launcher (`.bat`/`.sh`). Remove the intervention fork and all command-section
building. Delete `_escape_batch_title` (banner escaping now happens in Python).

## HOW
- Import `SessionSpec`, `write_session_spec` from `.types`; `LAUNCHER_WINDOWS`,
  `LAUNCHER_POSIX` from `.templates`.
- Keep the existing helpers/behaviour: `get_vscodeclaude_config`, the `commands`
  list/str validation (raise `ValueError`), the POSIX `mcp_config`-exists check
  (`FileNotFoundError`), `get_mcp_coder_install_path` fallback + `RuntimeError`,
  and `_resolve_install_script`.
- `session_folder_path` param is now unused (CWD is the runtime source of truth);
  keep it for signature stability with `# pylint: disable=unused-argument`.
- POSIX: `chmod(0o755)` on the `.sh` as today.

## ALGORITHM
```
is_windows = platform.system() == "Windows"
mcp_config = _MCP_CONFIG_FILES.get(platform.system(), ".mcp.json")
config = get_vscodeclaude_config(status)
commands = config.get("commands", []) if config else []
emoji = config["emoji"] if config else "📋"
validate commands is list[str] else ValueError
if not is_windows and not (folder/mcp_config).exists(): raise FileNotFoundError
install = mcp_coder_install_path or get_mcp_coder_install_path() or RuntimeError
spec = SessionSpec(issue_number, issue_title, repo_name, status, issue_url,
                   emoji, list(commands), timeout, mcp_config,
                   str(_resolve_install_script(install)), str(install),
                   skip_github_install, is_intervention)
write_session_spec(folder_path, spec)
name, tmpl = (".vscodeclaude_start.bat", LAUNCHER_WINDOWS) if is_windows
             else (".vscodeclaude_start.sh", LAUNCHER_POSIX)
p = folder_path / name
p.write_text(tmpl.format(mcp_coder_install_path=str(install)), encoding="utf-8")
if not is_windows: p.chmod(0o755)
return p
```

## DATA
- Returns `Path` to the launcher script (unchanged contract).
- Side effect: writes `.vscodeclaude_session.json` next to the launcher.

## TESTS
Port / trim (write/adjust before implementing):
- **Keep** (adapt to new reality): filename `.bat`/`.sh`, POSIX shebang &
  `chmod` bit, POSIX missing-mcp-config raises `FileNotFoundError`, `ValueError`
  for bad `commands` config, `RuntimeError` when install path unresolved.
- **Port github delegation** (`test_workspace_startup_script_github.py`): assert
  on the written spec instead of bat text — `read_session_spec(folder)
  .skip_github_install` is `False`/`True`, and
  `build_install_argv(spec, folder)` contains / omits `--skip-overrides`.
- **Delete obsolete** shell-string assertions (activate.bat, `PATH=%MCP_CODER_
  VENV_PATH%`, `mcp-coder prompt`, step labels, `--session-id %SESSION_ID%`,
  batch/quote escaping, `chcp`, PATH-twice) in `test_workspace_startup_script.py`
  and `test_startup_script_mcp_coder_path.py`. Replace their intent with a spec
  assertion (e.g. `read_session_spec(folder).commands` matches config,
  `is_intervention` set) where still meaningful.
- New: spec round-trips through `create_startup_script` for intervention, 0/1/
  multi-command statuses, on Windows and POSIX.

## LLM PROMPT
> Implement Step 5 from `pr_info/steps/step_5.md` (context in
> `pr_info/steps/summary.md`). Rewrite `create_startup_script` in
> `src/mcp_coder/workflows/vscodeclaude/workspace.py` to build a `SessionSpec`,
> call `write_session_spec`, and write the thin launcher (`LAUNCHER_WINDOWS`/
> `LAUNCHER_POSIX`); remove the intervention fork, the command-section building,
> and `_escape_batch_title`. Keep the signature (mark `session_folder_path`
> unused). Port the two github delegation tests to assert on the spec +
> `build_install_argv`, delete the now-obsolete shell-string tests in
> `test_workspace_startup_script.py` and `test_startup_script_mcp_coder_path.py`,
> and keep the filename/mode/error-path tests. Do NOT edit `session_launch.py` or
> `session_restart.py`. Use MCP workspace tools. Run pylint, pytest (`-n auto` +
> standard exclusions), mypy; fix all. One commit.
