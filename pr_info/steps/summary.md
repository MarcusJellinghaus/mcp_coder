# Summary — Replace bat/sh orchestration with thin launcher + Python `session_setup`

Issue **#695**: retire the generated `.bat`/`.sh` orchestration scripts. The
startup script collapses to a **thin launcher** that bootstraps into Python.
All shell orchestration (env assembly, `install.py` provisioning, session-ID
capture, step chaining, interactive `claude` handoff, banner) moves into a new,
unit-testable module `session_setup.py`.

## Goal

- Kill the fragile per-platform shell templates (`VENV_SECTION_*`,
  `AUTOMATED_SECTION_*`, `AUTOMATED_RESUME_SECTION_*`, `INTERACTIVE_*_SECTION_*`,
  `STARTUP_SCRIPT_*`, `INTERVENTION_SCRIPT_*`).
- Replace them with **one launcher per platform** (Windows `.bat`, POSIX `.sh`).
- Move orchestration into `session_setup.py`, driven by a typed session-spec
  JSON (`.vscodeclaude_session.json`) written at launch time.

## Architectural / design changes

**Launch-time vs run-time boundary (new).**
`workspace.py::create_startup_script` no longer bakes shell logic. It now:
1. resolves `commands` / `emoji` / `mcp_config` / `install.py` path (unchanged
   resolution helpers), 2. serializes a typed `SessionSpec` to
   `<folder>/.vscodeclaude_session.json`, and 3. writes a one-line launcher.
`session_setup.py` is a **pure consumer** of that spec at run time.

**Thin launcher (one per platform, no intervention variant).**
Because `is_intervention` lives in the spec and all branching moved into Python,
the launcher is byte-identical for every session. The only substitution is the
coordinator's Python path:
```bat
@echo off
"{mcp_coder_install_path}\.venv\Scripts\python.exe" -m mcp_coder.workflows.vscodeclaude.session_setup "%CD%" || pause
```
```sh
#!/usr/bin/env bash
"{mcp_coder_install_path}/.venv/bin/python" -m mcp_coder.workflows.vscodeclaude.session_setup "$PWD" || read -r -p "Session failed (Enter to close)..."
```

**Explicit `env` dicts, no PATH-mutation-by-activate.**
`build_subprocess_env` = `os.environ.copy()` + overlay of the four MCP vars
(`MCP_CODER_VENV_PATH`, `MCP_CODER_PROJECT_DIR`, `MCP_CODER_VENV_DIR`,
`VIRTUAL_ENV`), PATH prepend (mcp-coder venv + project venv bin), plus
`MCP_TIMEOUT=30000` and `UV_GIT_SHALLOW=0`. This kills the `#651`/`#694` PATH
bug class. The full-env copy preserves `USERPROFILE`, `SystemRoot`, `TEMP`, etc.
required for `.mcp.json` interpolation.

**Keep delegating to `install.py`.** `session_setup` shells out to `install.py`
with the exact argv used today (`--source local --local-path <CWD> --extras dev
--use-sync --refresh [--skip-overrides]`). The path is resolved at launch via the
existing `_resolve_install_script` and carried in the spec. No install logic is
re-absorbed.

**`skip_github_install` round-trips** `workspace.py → spec JSON → session_setup →
install.py argv` (append `--skip-overrides` iff set). Default overrides-ON.

**Banner rendered in Python** with forced UTF-8 stdout (replaces `chcp 65001`);
reuses the existing `BANNER_TEMPLATE` string.

**Error visibility on both layers.** `main` wraps `run_session`; on any expected
failure it prints the traceback, prompts the user, then **exits 0** (it already
gave the pause) so the launcher's `|| pause` / `|| read` does not double-prompt.
A non-zero exit is reserved for the interpreter-can't-start case, which the
launcher backstop catches.

**KISS decisions.**
- Absolute path for the `mcp-coder` executable (avoids the Windows
  `CreateProcess` PATH-lookup gotcha); `claude` stays PATH-resolved (it is a
  global npm CLI in the inherited PATH).
- Project/session dir is the launcher's `%CD%` / `$PWD` argument — the single
  source of truth. `session_folder_path` is **not** stored in the spec (it always
  equalled the CWD). The `session_folder_path` parameter of
  `create_startup_script` stays for signature stability but is unused.
- Orchestration is expressed as **pure argv-builder functions** + one thin loop,
  so flag fidelity is asserted without mocking subprocess.
- Runtime platform detection via a single `_venv_bin_dir` helper (Scripts vs
  bin); platform is not stored in the spec.

## Flow shapes preserved (per status `commands` + intervention)

| Shape | Behaviour |
|-------|-----------|
| intervention | bare `claude --mcp-config <f> --strict-mcp-config` |
| 0 commands | venv provisioning only |
| 1 command | interactive `claude --mcp-config <f> --strict-mcp-config "<cmd> <issue>"` |
| multi | step 1 automated (`mcp-coder prompt ... --output-format session-id`) → middle steps `--session-id` (non-fatal) → last interactive `claude --resume <id> "<cmd>"` |

Per-flag rules kept: `--strict-mcp-config` on `claude` only; `--output-format
session-id` on step 1 only; `--timeout`/`--session-id` on `mcp-coder prompt`
steps; middle steps continue on error.

## Files created / modified

**Created**
- `src/mcp_coder/workflows/vscodeclaude/session_setup.py`
- `tests/workflows/vscodeclaude/test_session_spec.py`
- `tests/workflows/vscodeclaude/test_session_setup_env.py`
- `tests/workflows/vscodeclaude/test_session_setup_flow.py`
- `pr_info/steps/summary.md` + `step_1.md` … `step_6.md`

**Modified**
- `src/mcp_coder/workflows/vscodeclaude/types.py` — add `SessionSpec` + spec
  read/write helpers.
- `src/mcp_coder/workflows/vscodeclaude/templates.py` — add `LAUNCHER_WINDOWS` /
  `LAUNCHER_POSIX`, extend `GITIGNORE_ENTRY`, delete the 12 orchestration
  constants.
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — rewrite
  `create_startup_script` (write spec + launcher); drop `_escape_batch_title`.
- `tests/workflows/vscodeclaude/test_templates.py` — launcher tests; drop
  removed-constant tests.
- `tests/workflows/vscodeclaude/test_workspace_startup_script.py` — drop obsolete
  shell-string assertions; keep filename/mode/spec-level assertions.
- `tests/workflows/vscodeclaude/test_workspace_startup_script_github.py` — port
  delegation tests to the spec field + `build_install_argv`.
- `tests/workflows/vscodeclaude/test_startup_script_mcp_coder_path.py` —
  rewrite/delete (asserted removed shell content).
- `tests/workflows/vscodeclaude/test_workspace.py` — port the two
  content-asserting tests (`test_create_startup_script_windows`,
  `test_create_startup_script_intervention`) to spec assertions.
- `docs/coordinator-vscodeclaude.md` — Generated-Files table (+ session json).
- `.github/workflows/ci.yml` — update the `vscodeclaude-template-install`
  drift-guard comment to point at `session_setup.build_install_argv`
  (comment-only).

**Unchanged (verified)**
- `session_launch.py` — both `create_startup_script` call sites (~lines 195 and
  450) live here; `session_restart.py` has no direct call. Signature is unchanged
  either way, so no call-site edits.
- `__init__.py` — `session_setup` is invoked via `python -m`, not exported.

## Step overview (one commit each, TDD)

1. `SessionSpec` dataclass + `read_session_spec` / `write_session_spec` helpers.
2. `session_setup.py` pure helpers: env dict, venv-bin, argv builders, banner.
3. `session_setup.py` orchestration + `main` (subprocess, session-id, flows).
4. `templates.py`: add launcher constants + gitignore entry (additive).
5. `workspace.py`: rewrite `create_startup_script`; port/trim workspace tests.
6. Delete retired orchestration templates + their tests; update docs.
