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
- `tests/workflows/vscodeclaude/test_workspace.py` (port two content-asserting tests)

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
- **Port `test_workspace.py`** (two tests assert on generated *script content*
  and break under the thin launcher):
  - `test_create_startup_script_windows` asserts `"claude" in content` and
    `"/implementation_review_supervisor" in content` — that command now lives in
    the spec JSON, not the `.bat`. Re-point these to the written session-spec:
    assert `read_session_spec(folder).commands` (or the `build_claude_argv` /
    `build_step_argv` output) contains that command, not the launcher text.
  - `test_create_startup_script_intervention` asserts `"INTERVENTION" in content`
    — the intervention banner is rendered at runtime by `session_setup.py`, not
    baked into the launcher. Re-point to the spec's `is_intervention` flag
    (and/or move the banner-text assertion to the `render_banner` test in
    Step 2/3).
- New: spec round-trips through `create_startup_script` for intervention, 0/1/
  multi-command statuses, on Windows and POSIX.
- **New end-to-end `skip_github_install` round-trip** (real on-disk path,
  `workspace.py → .vscodeclaude_session.json → session_setup → install.py argv`):
  ONE test chaining `create_startup_script(..., skip_github_install=True)` writes
  the spec → `read_session_spec(folder)` → `build_install_argv(spec, folder)`
  **includes** `--skip-overrides`; and the default (overrides-ON) case **omits**
  it. Complements the piece-wise github delegation tests above.

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
> port the two content-asserting tests in `test_workspace.py`
> (`test_create_startup_script_windows`, `test_create_startup_script_intervention`)
> to spec assertions, add the end-to-end `skip_github_install` round-trip test,
> and keep the filename/mode/error-path tests. Do NOT edit `session_launch.py` or
> `session_restart.py`. Use MCP workspace tools. Run pylint, pytest (`-n auto` +
> standard exclusions), mypy; fix all. One commit.
