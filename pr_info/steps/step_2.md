# Step 2 — `mcp_coder.install` package + `mcp-coder install` subcommand

The package and its CLI entry point land together: a package with no caller trips
vulture, and the ported tests exercise the command as well as the phases.

`tools/install.py` is **not** deleted here (Step 5) — `session_setup` and CI still use
it. The two coexist for three commits; only the tests move.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder/install/__init__.py` | **new** — `install()`, re-export `InstallConfig` |
| `src/mcp_coder/install/_env.py` | **new** — `InstallConfig` + env helpers |
| `src/mcp_coder/install/_phases.py` | **new** — the five phases |
| `src/mcp_coder/cli/commands/install.py` | **new** — `execute_install` |
| `src/mcp_coder/cli/parsers.py` | modified — `add_install_parser` after `add_icoder_parser` (`:578`) |
| `src/mcp_coder/cli/main.py` | modified — import blocks `:17-38` / `:40-57`, call `:128-145`, dispatch |
| `src/mcp_coder/cli/command_catalog.py` | modified — description + SETUP category |
| `tach.toml` | modified |
| `.importlinter` | modified |
| `tests/install/{__init__,test_install_config,test_install_phases,test_install_cli}.py` | **new** |
| `tests/tools/test_install_py.py` | **deleted** (ported) |

## WHAT

`_env.py`:

```python
@dataclass(frozen=True)
class InstallConfig:
    target: Path
    source: str            # "git" | "pypi" | "local"
    ref: str
    local_path: Path       # always resolved; defaults to target
    extras: str            # always resolved; "" means no extras
    extra_packages: str
    use_sync: bool
    skip_overrides: bool
    refresh: bool
    clean: bool
    python: str
    check: bool

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "InstallConfig": ...

def venv_bin(venv: Path) -> Path
def exe(name: str) -> str
def run(cmd: list[str], *, check: bool = True, dry: bool = False, cwd: Path | None = None) -> int
def ensure_system_uv() -> str
def rmtree_with_retry(path: Path, attempts: int = 3, delay: float = 1.0) -> None
```

`_phases.py` — same bodies as `tools/install.py`, taking `InstallConfig` instead of
`argparse.Namespace`:

```python
def phase_venv(config: InstallConfig, venv: Path) -> None
def phase_bootstrap_pip_uv(config: InstallConfig, py_v: Path) -> None
def phase_install_main(config: InstallConfig, uv_bin: str, py_v: Path) -> bool   # True == editable
def phase_overrides(config: InstallConfig, uv_bin: str, py_v: Path, is_editable: bool) -> None
def phase_report_versions(config: InstallConfig, bin_dir: Path, uv_bin: str, py_v: Path) -> None
```

`__init__.py`:

```python
MCP_CODER_REPO: str
REPORT_BINARIES: tuple[str, ...] = ("mcp-coder", "mcp-tools-py", "mcp-workspace", "mcp-config")
REPORT_PACKAGES: tuple[str, ...] = ("mcp-coder-utils",)

from ._env import InstallConfig          # re-export; see summary's Decision 11/12 note

def install(config: InstallConfig) -> None
```

`cli/commands/install.py`:

```python
def execute_install(args: argparse.Namespace) -> int
```

`cli/parsers.py`:

```python
def add_install_parser(subparsers: Any) -> None
```

## HOW

- **Ported from `tools/install.py`, unchanged in behaviour:** `venv_bin`, `exe`, `run`,
  `ensure_system_uv`, `rmtree_with_retry`/`_rmtree_onexc`, and the phase bodies.
  Keep raw `subprocess.run` with inherited stdio and the `--check` dry-run mode.
- **Dropped:** `CLI_BINARIES`, `OPTIONAL_CLI_BINARIES`, `EXTRA_VERSION_QUERIES`,
  `_detect_repo_root`, `REPO_ROOT`, `_source_dir_for_overrides`, `parse_args`, `main`,
  and the local `github_overrides` (use `pyproject_config.get_github_install_config`).
- **`phase_report_versions`** iterates `REPORT_BINARIES`, running `--version` for each
  present binary and printing `(not installed: <name>)` for each absent one. It never
  exits non-zero. Then `uv pip show` for `REPORT_PACKAGES`.
- **`phase_overrides`** reads overrides via
  `get_github_install_config(config.local_path)` — no `src_dir is None` branch left,
  since `local_path` is always set (Decision 17).
- **Parser flags** mirror `tools/install.py:parse_args` with two changes:
  `--extras default=None` and `--local-path default=None` (sentinels). `--python`
  keeps `default=sys.executable`.
- **`main.py`**: add `add_install_parser` to the `.parsers` import block, `execute_install`
  to the `.commands.*` block, call `add_install_parser(subparsers)` alongside
  `add_init_parser`/`add_verify_parser`, and add
  `elif args.command == "install": return execute_install(args)`.
- **`command_catalog.py`**: `"install": "Install mcp-coder into a target environment"`
  and add `"install"` to the `SETUP` category. Required — `tests/cli/test_help_anti_drift.py`
  asserts the description set equals the parser leaf set and that every description is
  categorized exactly once.
- **`tach.toml`**: new `[[modules]]` `path = "mcp_coder.install"`, `layer = "domain"`,
  `depends_on = [{ path = "mcp_coder.utils" }]`, placed after the `mcp_coder.prompt_sources`
  block; add `{ path = "mcp_coder.install" }` to `mcp_coder.cli`'s `depends_on` (`:56-73`)
  and to `tests`' (`:472-488`).
- **`.importlinter`**: add `mcp_coder.install` as its own row in `layered_architecture`
  between `mcp_coder.prompts` and `mcp_coder.utils`; add **both**
  `mcp_coder.install -> subprocess` and `mcp_coder.install.** -> subprocess` to
  `subprocess_isolation`'s `ignore_imports` (`pkg.**` does not match `pkg` itself);
  add `tests.install` to `test_module_independence`.

## ALGORITHM

```
InstallConfig.from_args(args):
    if args.source == "local" and args.local_path is None:
        raise ValueError("--source local requires --local-path")   # raw value, pre-resolution
    target     = args.target.resolve()
    local_path = (args.local_path or args.target).resolve()
    if args.use_sync and local_path != target:
        raise ValueError("--use-sync requires target == --local-path; uv sync writes to <local-path>/.venv")
    declared = get_install_extras(local_path, strict=True)   # unconditional: validates the file
    extras   = args.extras if args.extras is not None else declared
    return cls(target=target, local_path=local_path, extras=extras, ...)

install(config):
    uv = ensure_system_uv(); venv = config.target/".venv"
    bin_dir = venv_bin(venv); py = bin_dir/exe("python")
    print header
    phase_venv(config, venv); phase_bootstrap_pip_uv(config, py)
    editable = phase_install_main(config, uv, py)
    phase_overrides(config, uv, py, editable)
    if config.extra_packages: run([uv,"pip","install","--python",py,*split])
    phase_report_versions(config, bin_dir, uv, py)

execute_install(args):
    try: config = InstallConfig.from_args(args)
    except ValueError as e: logger.error(str(e)); return 1
    install(config); return 0
```

## DATA

- `InstallConfig` — frozen; attribute assignment raises `FrozenInstanceError`.
  `local_path` and `extras` are **always** resolved, so no consumer sees a sentinel.
- `phase_install_main` → `bool` (editable install, so `phase_overrides` knows whether
  to re-link).
- `execute_install` → `0` on success, `1` on a config-level error. A failing subprocess
  still exits the process through `run`'s `sys.exit(rc)`, as today.
- `--check` prints every command as `> <cmd>` and executes nothing.

## TESTS (write first)

Port `tests/tools/test_install_py.py` into `tests/install/`, replacing its
`importlib.util.spec_from_file_location` loader with normal imports, then delete it.

`tests/install/test_install_config.py`
- extras: declared in target pyproject; section absent → `"dev"`; explicit `extras = ""`
  → `""`; explicit `--extras` flag overrides the file.
- strict TOML: malformed target pyproject → error naming the file, **also when
  `--extras` is passed explicitly** (the strict read is unconditional, so
  `phase_overrides`' lax `get_github_install_config` can never silently swallow it);
  missing pyproject → `{}` semantics, installs with the `"dev"` fallback (Decision 21).
- `--local-path` defaults to `<target>`; an explicit `--local-path` still wins.
- `--source local` without `--local-path` still errors (Decision 19).
- `InstallConfig` rejects attribute assignment (Decision 12).
- `--use-sync` with mismatched target/local-path errors.

`tests/install/test_install_phases.py`
- The ported `TestGithubOverridesParser` / `TestPhaseOverridesDryRun` /
  `TestEnsureSystemUv` coverage (dry-run stdout assertions on the `> …` lines).
- **Rewritten** `TestPhaseVersions`: a missing binary is reported and the install still
  succeeds (§2 / Decision 3) — the old "missing required CLI exits" test is deleted.

`tests/install/test_install_cli.py`
- `create_parser()` registers `install` as a subcommand and parses the flags.
- `main()` dispatches `install` to `execute_install` (monkeypatched).

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
>
> Implement Step 2 only. TDD: create `tests/install/` with the three test files first
> (porting `tests/tools/test_install_py.py`, rewriting `TestPhaseVersions`), then build
> `src/mcp_coder/install/` and the CLI wiring until they pass, then delete
> `tests/tools/test_install_py.py`.
>
> Leave `tools/install.py`, `tools/install.bat`, `tools/install.sh`, `pyproject.toml`'s
> `data-files` entry, `ci.yml` and everything under `workflows/vscodeclaude/` untouched —
> those are Steps 3 and 5. Keep raw `subprocess.run` and the `--check` mode. Define
> `InstallConfig` in `_env.py` and re-export it from `__init__.py` (see the summary's
> Decision 11/12 note) — do not create an import cycle.
>
> Remember `cli/command_catalog.py`, or `tests/cli/test_help_anti_drift.py` fails.
>
> Then run `run_format_code`, `run_pylint_check`, `run_mypy_check`, the fast pytest
> selection, plus `run_tach_check` and `run_lint_imports_check`. Commit once, green.
