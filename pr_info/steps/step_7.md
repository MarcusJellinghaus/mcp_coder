# Step 7: Session launcher calls `mcp-coder setup`; env built after setup; CI job

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_7.md`) only. Steps 4 and 6 must be done: if `mcp-coder setup` is not registered or `mcp_coder.utils.executable.venv_python` does not exist, write one line to `pr_info/.blocked.txt` and stop.
Write/adjust the tests first, then the implementation. Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Modify `src/mcp_coder/workflows/vscodeclaude/session_setup.py`
- Modify `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — the comment above `launch_vscode(...)` (MCP_CODER_VENV_DIR now names the tool env)
- Modify `.github/workflows/ci.yml` — job `vscodeclaude-template-install` (keep the job name; it is a required check)
- Modify `tests/workflows/vscodeclaude/test_session_setup_env.py`, `tests/workflows/vscodeclaude/test_session_setup_flow.py`
- Modify `docs/environments/environments.md`, `docs/coordinator-vscodeclaude.md` — session provisioning now via `mcp-coder setup`; `MCP_CODER_VENV_DIR` = tool env; `VIRTUAL_ENV` only when the project venv exists

## WHAT

```python
def build_subprocess_env(spec: SessionSpec, cwd: Path, *, with_project_venv: bool = True) -> dict[str, str]:
    """Session env; the setup call passes with_project_venv=False."""

def build_install_argv(spec: SessionSpec, cwd: Path) -> list[str]:
    """[<coordinator mcp-coder>, "setup", "--project-dir", str(cwd), "--refresh"] (+ "--skip-overrides")."""
```

## ALGORITHM (`build_subprocess_env`)

```
env = os.environ.copy(); tool_venv = Path(spec.mcp_coder_install_path) / ".venv"; coder_bin = _venv_bin_dir(tool_venv)
env |= {MCP_CODER_VENV_PATH: coder_bin, MCP_CODER_PROJECT_DIR: cwd, MCP_CODER_VENV_DIR: tool_venv, MCP_TIMEOUT, UV_GIT_SHALLOW: "0"}
env.pop("VIRTUAL_ENV", None); prefix = [coder_bin]
if with_project_venv and venv_python(cwd / ".venv") is not None: env["VIRTUAL_ENV"] = str(cwd / ".venv"); prefix.append(_venv_bin_dir(cwd / ".venv"))
env["PATH"] = os.pathsep.join([*map(str, prefix), env.get("PATH", "")])
return env
```

## HOW

- `run_session`: run setup with `build_subprocess_env(spec, cwd, with_project_venv=False)` and `check=True`, **then** build `env = build_subprocess_env(spec, cwd)` and call `orchestrate(spec, cwd, env)`.
- Import `venv_python` from `...utils.executable`. Update module/function docstrings (the "Invariant: VIRTUAL_ENV == <cwd>/.venv" line goes).
- CI job: replace the `mcp-coder install . --source local --local-path . --use-sync --refresh` call with `mcp-coder setup --project-dir . --refresh`; update the comment (mirrors `build_install_argv`, now `setup`). Keep `UV_GIT_SHALLOW: "0"` in the job env (the bootstrap `uv pip install` of siblings needs it) and keep the `.venv` smoke checks.

## Tests

- Setup argv: `argv[1:] == ["setup", "--project-dir", str(cwd), "--refresh"]`; `--skip-overrides` iff `skip_github_install`.
- Env (both platforms via `sys.platform` monkeypatch): `MCP_CODER_VENV_DIR == /coord/.venv`; with an interpreter in `<cwd>/.venv` → `VIRTUAL_ENV` set and PATH = coder bin, project bin, rest; without → no `VIRTUAL_ENV` even if inherited, PATH starts with coder bin only; `with_project_venv=False` → no overlay even when the venv exists.
- Flow (`test_session_setup_flow.py`): the setup call's env has no `VIRTUAL_ENV`; the env passed to `orchestrate` is built after setup (e.g. setup fake creates the venv interpreter → orchestrate env has `VIRTUAL_ENV`).

## DATA

`dict[str, str]` env; `list[str]` argv.
