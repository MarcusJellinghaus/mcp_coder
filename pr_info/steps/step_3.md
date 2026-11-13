# Step 3: Setup step runner in `install/project_setup.py`

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_3.md`) only. Steps 1–2 must be done: if `mcp_coder.utils.executable.resolve_executable` or `mcp_coder.utils.setup_config.load_setup_config` does not exist, write one line to `pr_info/.blocked.txt` and stop.
Write the tests first (fake steps, all subprocess / install / git calls mocked), then the implementation. Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Create `src/mcp_coder/install/project_setup.py`
- Modify `src/mcp_coder/utils/executable.py` — add `venv_search_path`
- Modify `src/mcp_coder/install/__init__.py` — module docstring: the package also backs `mcp-coder setup` (language-neutral steps); `install()` itself stays Python-only. No code change.
- Modify `tach.toml` — `mcp_coder.install` `depends_on` gains `{ path = "mcp_coder.mcp_workspace_git" }` (changed-files check)
- Create `tests/install/test_project_setup.py`

## WHAT

```python
# utils/executable.py
def venv_search_path(project_dir: Path) -> str:
    """get_bin_dir(project_dir / ".venv") + os.pathsep + os.environ PATH."""
    # build on mcp_coder.utils.mcp_verification.get_bin_dir

# install/project_setup.py
class SetupError(Exception):
    """A setup step failed or setup changed files; message is user-facing."""

def run_setup(project_dir: Path, *, refresh: bool, skip_overrides: bool) -> None:
    """Run [tool.mcp-coder.setup] steps in order.

    Raises ValueError (config) or SetupError (step failure, git error, changed files).
    """

def _run_python_builtin(project_dir: Path, refresh: bool, skip_overrides: bool) -> None: ...
def _run_argv_step(step: SetupStep, project_dir: Path, overlay: dict[str, str]) -> None: ...
def _dirty_paths(project_dir: Path) -> set[str] | None: ...   # None = not a git repo

_BUILTINS = {"python": _run_python_builtin}
```

## ALGORITHM (`run_setup`)

```
os.environ.setdefault("UV_GIT_SHALLOW", "0")
config = load_setup_config(project_dir)
if not config.steps: logger.info("No setup steps for %s; nothing to do", project_dir); return
before = _dirty_paths(project_dir); overlay = {}
for step in config.steps:  log label; builtin -> _BUILTINS[name](...); overlay = {"PATH": venv_search_path(project_dir), "VIRTUAL_ENV": str(project_dir / ".venv")}; argv -> _run_argv_step(step, project_dir, overlay)
if before is not None and (new := _dirty_paths(project_dir) - before): raise SetupError("Setup changed or created files: " + ", ".join(sorted(new)))
```

## HOW

- `_run_python_builtin`: build `argparse.Namespace(target=project_dir, source="local", ref="main", local_path=project_dir, extras=None, extra_packages="", use_sync=True, skip_overrides=..., refresh=..., clean=False, python=sys.executable, check=False)`, then `install(InstallConfig.from_args(ns))` (imports from `mcp_coder.install`). Catch `ValueError` → `SetupError`; catch `SystemExit` with `code not in (None, 0)` → `SetupError(f"python: install failed ({code})")`.
- `_run_argv_step`: `exe = resolve_executable(argv[0], project_dir, path=overlay.get("PATH"))`; `None` → `SetupError(f"{label}: {argv[0]!r} not found")`. Run `execute_subprocess([exe, *argv[1:]], CommandOptions(cwd=str(project_dir), timeout_seconds=step.timeout, capture_output=False, env=overlay or None))` from `mcp_coder.utils.subprocess_runner`. `timed_out` / `execution_error` / non-zero `return_code` → `SetupError` naming the label.
- `_dirty_paths`: `is_git_repository(project_dir)` false → `logger.info("…not a git repository; changed-files check skipped")`, return `None`. Else `get_working_tree_status(project_dir)` (both from `mcp_coder.mcp_workspace_git`); `success` false → `SetupError` with `status["error"]`; else `set(staged) | set(modified) | set(untracked)`. Never use `is_working_directory_clean` / `get_full_status`.
- The first failing step raises; later steps don't run.

## Tests (`tests/install/test_project_setup.py`)

Patch `project_setup.load_setup_config`, `project_setup.install`, `project_setup.InstallConfig`, `project_setup.execute_subprocess`, `project_setup.resolve_executable`, `project_setup.is_git_repository`, `project_setup.get_working_tree_status`.

- Steps run in order; first failure stops the rest; non-zero exit, timeout, execution error, unresolved `argv[0]` each raise `SetupError` naming the step.
- `npm ci` config runs with no Python venv: no install call, `env=None`, `VIRTUAL_ENV` not set.
- Built-in: Namespace carries `refresh` / `skip_overrides`; `SystemExit(1)` and `ValueError` become `SetupError`; steps after it get `PATH` starting with the venv bin dir and `VIRTUAL_ENV`, and `resolve_executable` gets that `path`.
- `UV_GIT_SHALLOW` set to `"0"` when unset, preserved when set (use `monkeypatch.delenv/setenv`).
- Empty steps → returns, logs "nothing to do".
- Changed files: new untracked file → `SetupError` listing it; file already dirty before → passes; not a git repo → skipped with log; git status failure in a repo → `SetupError`.
- Config `ValueError` propagates.

## DATA

`run_setup` returns `None`; failures raise `SetupError(str)` or `ValueError(str)`.
