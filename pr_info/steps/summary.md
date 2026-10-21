# Summary — #1247 Configurable `post_install_checks` for `mcp-coder install`

## Goal

Fail `mcp-coder install` right after provisioning when the project venv is broken,
instead of minutes later during the real work (the #1243 symptom). Each target repo
declares its own checks; when none are declared, nothing is checked.

```toml
[tool.mcp-coder.install]
extras = "dev"
post_install_checks = [
    ["mcp-coder", "--version"],
    ["mcp-workspace", "--version"],
    ["mcp-tools-py", "--version"],
]
```

## Architectural / design changes

- **New pyproject key** `[tool.mcp-coder.install] post_install_checks`: a list of argv
  lists. The reader `get_post_install_checks` (`utils/pyproject_config.py`) follows
  the `get_install_extras` pattern: in strict mode it raises `ValueError`, otherwise it
  warns and returns `()`. A missing file, section or key, and `[]`, all mean "no checks".
- **`InstallConfig` gains `post_install_checks: tuple[tuple[str, ...], ...]`**. It is
  read strictly in `from_args`, so a malformed value aborts **before** provisioning
  through the existing `ValueError` → exit 1 path.
- **New sixth install phase** `phase_post_install_checks(config, bin_dir)` in
  `install/_phases.py`. `install()` calls it after the version report and the
  `--extra-packages` step, and before the `OK ... complete` line, which is not
  printed on failure.
  - Resolving `argv[0]` (helper `_resolve_check_executable`):
    - A path form (the name contains a path separator) is used as-is when absolute,
      or joined to `local_path` when relative. It must exist.
    - A bare name becomes one candidate: the name unchanged if it already ends in
      `.exe` (any case), otherwise `exe(name)`. The helper looks for that candidate in
      the venv `bin_dir` first, then in each `PATH` entry in order. The current
      directory is never searched, so `shutil.which` is not used: on Windows it adds
      the cwd to the search path.
    - Nothing found → "not found", decided **before** spawning. Nothing is run.
  - Runner: `execute_subprocess` from the `mcp_coder.utils.subprocess_runner` shim,
    with `CommandOptions(cwd=str(local_path), timeout_seconds=300,
    capture_output=False, env={"PATH": f"{bin_dir}{os.pathsep}{PATH}"})`.
  - Result order: `timed_out` → `execution_error` → `return_code`. All checks run;
    then one summary is printed and the phase calls `sys.exit(1)`.
  - Echo: each check is printed with the existing `run(cmd, dry=True, cwd=...)`, which
    prints the `"> ..."` line and nothing else, so no new print helper is needed. In
    `--check` (dry-run) mode, the declared argv is echoed unresolved and nothing runs.
- **`validate_target_repo`** (VSCodeClaude launch) also reads the key inside its
  existing strict `try`. A malformed value hits the existing `except ValueError`
  warning; an absent key gives no warning.
- `REPORT_BINARIES` / `phase_report_versions` stay unchanged and informational.
- Known limit (KISS): on Windows, a bare name only matches a `.exe` file. A
  `.cmd`/`.bat` launcher must be declared by path.

## Files

### Modified
- `src/mcp_coder/utils/pyproject_config.py`: `get_post_install_checks`
- `src/mcp_coder/install/_env.py`: `InstallConfig.post_install_checks`, read in `from_args`
- `src/mcp_coder/install/_phases.py`: `phase_post_install_checks`, `_resolve_check_executable`, `POST_INSTALL_CHECK_TIMEOUT_SECONDS`, module docstring "six"
- `src/mcp_coder/install/__init__.py`: wire the phase into `install()`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`: read the key in `validate_target_repo`
- `pyproject.toml`: this repo's three `--version` checks
- `tests/utils/test_pyproject_config.py`: `TestGetPostInstallChecks`
- `tests/install/test_install_env.py`: `from_args` reads the key
- `tests/workflows/vscodeclaude/test_validate_target_repo.py`: warning cases
- `docs/configuration/config.md`, `docs/cli-reference.md`,
  `docs/repository-setup/README.md`, `docs/repository-setup/python.md`,
  `docs/architecture/architecture.md`

### Created
- `tests/install/test_install_post_checks.py`

## Steps (one commit each)

1. Config reader `get_post_install_checks` + tests
2. `InstallConfig.post_install_checks` read strictly in `from_args` + tests
3. `validate_target_repo` reads the key + tests
4. `phase_post_install_checks` + wiring in `install()` + tests
5. This repo's `pyproject.toml` declares the three checks
6. Documentation
