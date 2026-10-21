# Step 4 — New install phase `phase_post_install_checks`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` only.
> TDD: write `tests/install/test_install_post_checks.py` first, then the phase and its
> wiring. Run pylint, mypy, lint-imports, tach and the fast unit pytest set (see
> CLAUDE.md). All must pass. Run the formatter, then make one commit.
>
> Precondition: `mcp_coder.utils.subprocess_runner` exports `execute_subprocess` and
> `CommandOptions`. If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE
- `src/mcp_coder/install/_phases.py`: constant, resolver, phase; module docstring "five" → "six"
- `src/mcp_coder/install/__init__.py`: import and call the phase
- `tests/install/test_install_post_checks.py` (new)

## WHAT
```python
POST_INSTALL_CHECK_TIMEOUT_SECONDS = 300

def _resolve_check_executable(
    name: str, bin_dir: Path, local_path: Path
) -> Path | None:
    """Resolve argv[0] of a post-install check; None means not found."""

def phase_post_install_checks(config: InstallConfig, bin_dir: Path) -> None:
    """Phase 7: run [tool.mcp-coder.install] post_install_checks; exit 1 on any failure."""
```
New imports in `_phases.py`: `os`, `sys`, and
`from ..utils.subprocess_runner import CommandOptions, execute_subprocess`.

## HOW
- `install()` in `__init__.py`: call `phase_post_install_checks(config, bin_dir)` after
  `phase_report_versions(...)` and before `print(f"\nOK  mcp-coder install complete: ...")`.
- Echo each check with the existing `run(cmd, dry=True, cwd=config.local_path)`. It
  prints the `"> ..."` line only, so no new print helper is needed.
- Tests patch `_phases.execute_subprocess` with `monkeypatch.setattr` and return
  `CommandResult` objects (import `CommandResult` from the shim). Do not import
  `subprocess`; no hanging process is needed for the timeout case.
- The cwd test: `monkeypatch.chdir(tmp_dir_with_fake_exe)`, with that dir absent from
  `PATH` → "not found".

## ALGORITHM — resolver
```
if os.sep in name or (os.altsep and os.altsep in name):
    p = Path(name) if Path(name).is_absolute() else local_path / name
    return p if p.is_file() else None
cand = name if name.lower().endswith(".exe") else exe(name)
for d in [bin_dir, *(Path(e) for e in os.environ.get("PATH", "").split(os.pathsep) if e)]:
    if (d / cand).is_file(): return d / cand
return None
```

## ALGORITHM — phase
```
if not config.post_install_checks: return
print("\n--- post-install checks")
if config.check: run(list(argv), dry=True, cwd=local_path) for each; return
for argv in checks: resolve → None ⇒ failures += (argv, "not found"); continue
    cmd = [str(path), *argv[1:]]; run(cmd, dry=True, cwd=local_path)
    r = execute_subprocess(cmd, CommandOptions(cwd=str(local_path), timeout_seconds=300,
            capture_output=False, env={"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"}))
    r.timed_out ⇒ "timed out after 300 s"; elif r.execution_error ⇒ its text; elif r.return_code ⇒ f"exit code {rc}"
if failures: print summary (one line per failed argv + reason); sys.exit(1)
```

## DATA
- `failures: list[tuple[tuple[str, ...], str]]`, holding the declared argv and its reason.
- Summary format, for example:
  ```
  ERROR: 2 of 3 post-install checks failed:
    mcp-workspace --version: exit code 1
    mcp-tools-py --version: not found
  ```

## Tests (`tests/install/test_install_post_checks.py`)
Call the phase directly with `InstallConfig.from_args(namespace(target=tmp_path))` built
from a `tmp_path/pyproject.toml` that declares the checks, and a `bin_dir` under `tmp_path`.
- no checks declared → nothing printed, runner not called
- all pass → no exit; runner called once per check with the resolved venv path, `cwd=str(local_path)`, `timeout_seconds=300`, `capture_output=False`, and `env["PATH"]` starting with `bin_dir`
- one fails (return_code 2) → `SystemExit(1)`, summary contains `exit code 2`
- several fail → all checks run, exactly one summary listing each
- timeout (`timed_out=True`, `return_code=1`) → reason "timed out after 300 s"
- execution error (`execution_error="PermissionError: ..."`) → its text in the summary
- not found → runner never called for that check, reason "not found"
- resolution: venv beats `PATH`; `PATH` fallback; `.exe`-suffixed name gets no double `.exe` (Windows-style; use `monkeypatch.setattr(_phases, "exe", ...)` or skip on POSIX); relative path resolved against `local_path`; absolute path used as-is; cwd is never searched
- dry-run (`check=True`) → declared argv echoed as `"> ..."` lines, runner not called
- `install()` driver: on failure the `OK ... complete` line is not printed (patch `ensure_system_uv` and the earlier phases, as `test_install_phases.py` does)
