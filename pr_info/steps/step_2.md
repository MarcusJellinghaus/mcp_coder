# Step 2 — `session_setup.py` pure helpers (env, argv, banner)

Read `pr_info/steps/summary.md` first. This step adds the **pure** building
blocks of the orchestrator — no `subprocess`, no `main` yet. Everything here is
directly unit-testable without mocking.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_setup.py` (new)
- `tests/workflows/vscodeclaude/test_session_setup_env.py` (new)

## WHAT
```python
MCP_TIMEOUT_MS = "30000"   # see llm/claude_settings.py for canonical value

def _venv_bin_dir(venv_root: Path) -> Path            # Scripts (win) / bin (posix)
def _mcp_coder_exe(spec: SessionSpec) -> Path         # abs mcp-coder(.exe)
def _coordinator_python(spec: SessionSpec) -> Path    # abs python(.exe)
def build_subprocess_env(spec: SessionSpec, cwd: Path) -> dict[str, str]
def build_install_argv(spec: SessionSpec, cwd: Path) -> list[str]
def build_step_argv(spec, command: str, *, session_id: str | None,
                    issue_number: int | None) -> list[str]
def build_claude_argv(spec, *, prompt: str | None = None,
                      session_id: str | None = None) -> list[str]
def render_banner(spec: SessionSpec) -> str
```

## HOW
- Platform: derive Scripts/bin from `sys.platform == "win32"` inside
  `_venv_bin_dir` (single monkeypatch point for both-platform tests).
- `_mcp_coder_exe` / `_coordinator_python` are **absolute** (built from
  `spec.mcp_coder_install_path / ".venv"`) to avoid the Windows CreateProcess
  PATH-lookup gotcha. `claude` stays the literal `"claude"` (global npm CLI in
  inherited PATH).
- `render_banner` reuses `BANNER_TEMPLATE` from `.templates` (import inside the
  function to avoid a heavy top-level import). The old 58-char title truncation
  and shell-escaping (`_escape_batch_title` / POSIX quoting) are **intentionally
  dropped**: the banner is now printed by Python (no shell), so escaping is
  unnecessary; truncation was cosmetic and is not reproduced.
- **Shared env for `install.py` (Option B).** The one `build_subprocess_env`
  dict is reused for **every** subprocess, including the Step-3 `install.py`
  call. This is safe because `install.py` forwards env untouched; its
  `uv pip install` commands are immune (pinned via `--python <abs venv python>`),
  and the only env-sensitive command (`uv sync`, our `--use-sync` path) targets
  `<cwd>/.venv`. Setting `VIRTUAL_ENV=<cwd>/.venv` (rather than leaking the
  coordinator venv's `VIRTUAL_ENV`) makes `uv sync` match and avoids uv's
  "VIRTUAL_ENV does not match" warning. **Invariant to preserve:**
  `VIRTUAL_ENV == <cwd>/.venv == target`.

## ALGORITHM
```
build_subprocess_env:
    env = os.environ.copy()
    coder_bin = _venv_bin_dir(install/.venv); proj = cwd/.venv
    env |= {MCP_CODER_VENV_PATH: coder_bin, MCP_CODER_PROJECT_DIR: cwd,
            MCP_CODER_VENV_DIR: proj, VIRTUAL_ENV: proj,
            MCP_TIMEOUT: MCP_TIMEOUT_MS, UV_GIT_SHALLOW: "0"}
    env[PATH] = coder_bin + os.pathsep + _venv_bin_dir(proj) + os.pathsep + env[PATH]

build_install_argv:
    [coordinator_python, install_script_path, cwd, "--source","local",
     "--local-path",cwd,"--extras","dev","--use-sync","--refresh"]
     + (["--skip-overrides"] if spec.skip_github_install else [])

build_step_argv (session_id None => first step):
    prompt = f"{command} {issue_number}" if session_id is None else command
    base = [mcp_coder_exe,"prompt",prompt,"--llm-method","claude"]
    if session_id is None: base += ["--output-format","session-id"]
    else:                  base += ["--session-id", session_id]
    base += ["--mcp-config", spec.mcp_config, "--timeout", str(spec.timeout)]

build_claude_argv:
    a = ["claude","--mcp-config",spec.mcp_config,"--strict-mcp-config"]
    if prompt is None: return a                      # intervention
    if session_id: a += ["--resume", session_id]     # multi last
    return a + [prompt]                              # 1-cmd or resume
```

## DATA
- `build_subprocess_env` -> `dict[str,str]` (full env + overlay).
- `build_*_argv` -> `list[str]`.
- `render_banner` -> `str`.

## TESTS (write first, parametrize platform where it matters)
- Env: all four MCP vars set to CWD-derived paths; `VIRTUAL_ENV == cwd/.venv`;
  `MCP_TIMEOUT=30000`, `UV_GIT_SHALLOW=0`; PATH starts with coder bin then proj
  bin; a pre-existing key (e.g. `USERPROFILE`) survives. Parametrize win/posix
  (assert `Scripts` vs `bin`).
- `build_install_argv`: exact flags; `--skip-overrides` present iff
  `skip_github_install`.
- `build_step_argv`: first step has `--output-format session-id`, prompt
  `"<cmd> <issue>"`, no `--session-id`; resume step has `--session-id <id>`,
  prompt `<cmd>`, no `--output-format`.
- `build_claude_argv`: intervention (bare, no prompt), 1-cmd (prompt, no
  `--resume`), resume (`--resume <id>` + prompt). `--strict-mcp-config` always.
- `render_banner`: contains emoji, issue number, title, repo, status, url.

## LLM PROMPT
> Implement Step 2 from `pr_info/steps/step_2.md` (context in
> `pr_info/steps/summary.md`). Create
> `src/mcp_coder/workflows/vscodeclaude/session_setup.py` with the pure helpers
> listed (env dict, `_venv_bin_dir`, absolute exe/python resolvers, the three
> argv builders, `render_banner`). No `subprocess` and no `main` in this step.
> Write `tests/workflows/vscodeclaude/test_session_setup_env.py` first,
> parametrizing win/posix for the path-sensitive cases. Use MCP workspace tools.
> After each edit run pylint, pytest (`-n auto` with the standard integration
> exclusions), and mypy; fix everything. One commit.
