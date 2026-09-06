# Summary — Issue #1151: make the installer package code, move target-repo policy to the target repo

## Goal

`tools/install.py` ships and runs in production but lives outside the package, so no
quality gate (black, isort, ruff, pylint, `mypy --strict`) ever sees it. It also
hardcodes policy that belongs to the *target* project (`CLI_BINARIES`, `--extras dev`).

This refactor moves the installer into `src/mcp_coder/install/`, drives it through a new
`mcp-coder install` subcommand, and pushes per-target policy into the target repo's
`pyproject.toml`.

## Architectural / design changes

**1. The installer becomes ordinary package code (domain layer).**
`tools/install.py` → `src/mcp_coder/install/` (`__init__.py`, `_env.py`, `_phases.py`).
It is now covered by CI's `src tests` scoping, so the class of breakage behind #1153
(a stale constant nobody type-checked) becomes catchable. Dropping the stdlib-only
constraint lets it reuse `utils.pyproject_config` instead of duplicating TOML parsing.

**2. The entry point becomes a CLI subcommand, not a script path.**
`mcp-coder install <target> …`, invoked through the existing `_mcp_coder_exe(spec)`
helper. This deletes an entire resolution mechanism: the wheel `data-files` entry,
`workspace._resolve_install_script`, `SessionSpec.install_script_path` and
`session_setup._coordinator_python`. The standalone curl-bootstrap recipe is retired —
`pip install mcp-coder` first, then `mcp-coder install`.

**3. Target-project policy moves to the target project.**
Extras come from `[tool.mcp-coder.install] extras` in the target's `pyproject.toml`
(fallback `"dev"`), next to the `install-from-github` section the installer already
reads. `build_install_argv` stops emitting `--extras`, so `SessionSpec` gains no field.

**4. The required-CLI check is dropped, not redirected.**
`CLI_BINARIES` / `OPTIONAL_CLI_BINARIES` / `EXTRA_VERSION_QUERIES` collapse into one
report list; the installer reports versions and never fails on a missing binary.
The assertion moves to the caller — CI's smoke block gains `mcp-tools-py --version`
and `mcp-workspace --version` against the *project* venv.

**5. The target-repo contract becomes executable.**
`validate_mcp_json` at `session_launch.py:175` grows into `validate_target_repo`:
the `.mcp.json` row stays fatal, three new rows (extras declared, GitHub-override
section present, venv at `<repo>/.venv`) warn only.

**6. TOML reading is consolidated in `mcp_coder.utils`.**
`_format_toml_error` becomes public `format_toml_error` in its own module, imported by
both `user_config` and `pyproject_config`. `pyproject_config` gains a shared
`_load_pyproject(project_dir, *, strict=False)` and the three existing readers collapse
onto it.

**7. New module registered in the architecture contracts.**
`mcp_coder.install` → tach layer `domain` (`depends_on = [utils]`, mirroring
`mcp_coder.prompts`); its own row in the import-linter `layered_architecture` contract
between `mcp_coder.prompts` and `mcp_coder.utils`; a wildcard pair of `subprocess`
exemptions (raw `subprocess.run` is deliberate — see below).

### Deliberate non-changes

- **Raw `subprocess.run` stays.** `execute_command` captures output and defaults to a
  120-second timeout (wrong for an install pulling git deps); `stream_subprocess` is
  line-based, which mangles `uv`'s carriage-return progress. Keep inherited stdio and
  take the import-linter exemption `session_setup` already carries.
- **`config/label_config.py:114`'s duplicate TOML boilerplate stays** — `mcp_coder.config`
  sits *below* `mcp_coder.utils` and cannot import `pyproject_config`. Add a comment.
- **No flag removals.** `--check`, `--clean`, `--python`, `--ref`, `--extra-packages`
  all survive; only `--extras` changes, and only its default (`None`, so "not passed"
  stays distinguishable from an explicit `--extras ""`).

### Two mechanical notes on the Decisions

- **Decision 11/12 (layout):** `InstallConfig` is *defined* in `_env.py` and re-exported
  from `__init__.py`. Defining it in `__init__.py` while `_phases.py` annotates against
  it creates an import cycle; a `TYPE_CHECKING` guard would hide the cycle from mypy but
  not from `pycycle`. The public shape — `from mcp_coder.install import InstallConfig,
  install` — is exactly as the Decision specifies.
- **Decision 13 (strict load):** exactly one strict call site, in
  `InstallConfig.from_args`. It runs before any phase, so a malformed target
  `pyproject.toml` aborts before `get_github_install_config` is ever reached — that
  reader therefore needs no `strict` parameter.

## Steps

| # | Step | Commit contains |
|---|---|---|
| 1 | [step_1.md](./step_1.md) | Shared TOML plumbing in `mcp_coder.utils` |
| 2 | [step_2.md](./step_2.md) | `mcp_coder.install` package + `mcp-coder install` subcommand |
| 3 | [step_3.md](./step_3.md) | vscodeclaude switchover (atomic: spec field + argv + resolver removal) |
| 4 | [step_4.md](./step_4.md) | `validate_target_repo` |
| 5 | [step_5.md](./step_5.md) | Delete `tools/install.*`, rewrite `reinstall_local.*`, update CI |
| 6 | [step_6.md](./step_6.md) | Documentation |

Ordering rule: the new installer is added and wired **before** the old script is
deleted, so every intermediate commit has a working `session_setup` and a green CI.
Steps 5's three parts are one commit by necessity — `ci.yml:172` is the last consumer
of `tools/install.py`, so deleting the file without updating CI fails that commit's own
CI run.

## Files created / modified / deleted

### Created

| Path | Step |
|---|---|
| `src/mcp_coder/utils/toml_utils.py` | 1 |
| `src/mcp_coder/install/__init__.py` | 2 |
| `src/mcp_coder/install/_env.py` | 2 |
| `src/mcp_coder/install/_phases.py` | 2 |
| `src/mcp_coder/cli/commands/install.py` | 2 |
| `tests/install/__init__.py` | 2 |
| `tests/install/test_install_config.py` | 2 |
| `tests/install/test_install_phases.py` | 2 |
| `tests/install/test_install_cli.py` | 2 |
| `tests/workflows/vscodeclaude/test_validate_target_repo.py` | 4 |

### Modified

| Path | Step | Change |
|---|---|---|
| `src/mcp_coder/utils/user_config.py` | 1 | Import `format_toml_error`; drop the private copy |
| `src/mcp_coder/utils/pyproject_config.py` | 1 | `_load_pyproject`, `get_install_extras`, collapse boilerplate |
| `src/mcp_coder/config/label_config.py` | 1 | Comment only (why its boilerplate stays) |
| `tests/utils/test_user_config.py` | 1 | Import + 10 call sites renamed |
| `tests/utils/test_pyproject_config.py` | 1 | New cases for the two new functions |
| `src/mcp_coder/cli/parsers.py` | 2 | `add_install_parser` |
| `src/mcp_coder/cli/main.py` | 2 | Import, call, dispatch |
| `src/mcp_coder/cli/command_catalog.py` | 2 | `install` description + SETUP category |
| `tach.toml` | 2 | `mcp_coder.install` module; `cli` and `tests` `depends_on` |
| `.importlinter` | 2 | Layer row, `subprocess` wildcard pair, `tests.install` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | 3 | Delete `_resolve_install_script`; drop the spec field |
| `src/mcp_coder/workflows/vscodeclaude/types.py` | 3 | Retire `install_script_path`; drop unknown keys |
| `src/mcp_coder/workflows/vscodeclaude/session_setup.py` | 3 | New argv; delete `_coordinator_python` |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | 3 | Docstrings (`:5`, `:28`) |
| `tests/workflows/vscodeclaude/test_startup_script_mcp_coder_path.py` | 3 | Delete 2nd test; trim 1st |
| `tests/workflows/vscodeclaude/test_session_setup_env.py` | 3 | Fixture + 2 assertions |
| `tests/workflows/vscodeclaude/test_session_setup_flow.py` | 3 | Fixture + `_is_install` |
| `tests/workflows/vscodeclaude/test_session_spec.py` | 3 | Fixtures + stale-spec test |
| `tests/workflows/vscodeclaude/test_workspace_startup_script_github.py` | 3 | Six argv assertions |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | 4 | `validate_target_repo` |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | 4 | Export it |
| `pyproject.toml` | 5 | Drop `[tool.setuptools.data-files]` |
| `tools/reinstall_local.bat` / `.sh` | 5 | Rewritten driver resolution |
| `.github/workflows/ci.yml` | 5 | Bootstrap, new argv, two extra smoke checks |
| `README.md` | 6 | `:143-157` |
| `docs/getting-started/installation.md` | 6 | Rewrite |
| `docs/environments/environments.md` | 6 | `:113`, `:141` |
| `docs/repository-setup/internal.md` | 6 | `:38-39` |
| `docs/repository-setup/README.md` | 6 | `:84` + contracts table |
| `docs/cli-reference.md` | 6 | Short `install` entry |

### Deleted

| Path | Step |
|---|---|
| `tests/tools/test_install_py.py` | 2 (ported to `tests/install/`) |
| `tools/install.py` | 5 |
| `tools/install.bat` | 5 |
| `tools/install.sh` | 5 |

`tests/tools/__init__.py` stays — `tests/tools/mlflow/` still uses it.

## Verification (every step)

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
```

Steps 2 and 3 additionally: `run_tach_check`, `run_lint_imports_check`.
Step 5 additionally: `run_vulture_check`.

Note `mypy --strict` covers `src` **and** `tests` (`ci.yml:106`), so new test code needs
full annotations.
