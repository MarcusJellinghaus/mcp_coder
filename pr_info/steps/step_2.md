# Step 2 — `mcp_coder.install` package + `mcp-coder install` subcommand

The package and its CLI entry point land together: a package with no caller trips
vulture, and the ported tests exercise the command as well as the phases.

`tools/install.py` is **not** deleted here (Step 5) — `session_setup` and CI still use
it. The two coexist for three commits; only the tests move.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder/install/__init__.py` | **new** — `install()`, re-export `InstallConfig` + the three constants |
| `src/mcp_coder/install/_env.py` | **new** — the three module constants, `InstallConfig` + env helpers |
| `src/mcp_coder/install/_phases.py` | **new** — the five phases |
| `src/mcp_coder/cli/commands/install.py` | **new** — `execute_install` |
| `src/mcp_coder/cli/parsers.py` | modified — `add_install_parser` after `add_icoder_parser` (`:578`) |
| `src/mcp_coder/cli/main.py` | modified — import blocks `:17-38` / `:40-57`, call `:128-145`, dispatch |
| `src/mcp_coder/cli/command_catalog.py` | modified — description + SETUP category |
| `tests/cli/commands/test_help.py` | modified — `len(all_command_names) == 22` → `23` (`:66`) |
| `tach.toml` | modified |
| `.importlinter` | modified |
| `tests/install/{__init__,test_install_env,test_install_phases}.py` | **new** |
| `tests/cli/commands/test_install.py` | **new** — parser registration + dispatch |
| `tests/tools/test_install_py.py` | **deleted** (ported) |

Test files mirror their source module, per `planning_principles.md`:
`test_install_env.py` ↔ `install/_env.py` and `test_install_phases.py` ↔ `install/_phases.py`
(the `test_<package>_<module>` shape `tests/llm/providers/langchain/` already uses for
private modules), and the CLI-dispatch tests mirror `cli/commands/install.py`, so they live
in `tests/cli/commands/` next to `test_init.py` — which imports `create_parser` from
`cli.main` for exactly this kind of assertion.

## WHAT

`_env.py`:

```python
MCP_CODER_REPO: str
REPORT_BINARIES: tuple[str, ...] = ("mcp-coder", "mcp-tools-py", "mcp-workspace", "mcp-config")
REPORT_PACKAGES: tuple[str, ...] = ("mcp-coder-utils",)

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
# re-exports; see summary's Decision 11/12 note
from ._env import MCP_CODER_REPO, REPORT_BINARIES, REPORT_PACKAGES, InstallConfig

def install(config: InstallConfig) -> None
```

`_phases.py` imports the constants from `._env`, never from the package root.

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
- **One code edit the move forces: pylint W1510.** `tools/install.py:214`'s
  `subprocess.run(cmd, cwd=cwd)` trips `subprocess-run-check`, which is *not* in
  `pyproject.toml`'s pylint disable list (`:199-212`), so CI's `pylint ./src ./tests`
  (`ci.yml:102`) fails the moment `run` lands under `src/`. Pass `check=False`
  explicitly: `subprocess.run(cmd, cwd=cwd, check=False)`. Do **not** forward the
  wrapper's own `check` parameter — that one means "exit the process on failure" and is
  handled two lines below by `sys.exit(r.returncode)`; forwarding it would raise
  `CalledProcessError` instead and change behaviour.
- **Docstrings are not "unchanged" — the move puts them under `ruff check src`** for the
  first time (`ci.yml:103`, `D` + `DOC`, preview, google). `ruff check --preview tools/install.py`
  reports 8 issues across 6 rules today; six of them are on code that survives the move.
  All are fixed by editing the docstring, not the code:
  - `_ensure_system_uv` (`tools/install.py:483-487`) documents `Raises: SystemExit:`
    but exits via `sys.exit` → **DOC502**. Drop the `Raises:` section and state the
    failure in prose. (The alternative — a `"src/mcp_coder/install/_env.py" = ["DOC502"]`
    entry next to the four in `pyproject.toml:336-339` — is the fallback if any other
    `sys.exit` docstring resists.)
  - `_rmtree_with_retry` (`tools/install.py:263-266`) has a four-line summary with no
    blank line → **D205**. Rewrite as a one-line summary plus a blank line plus the body.
  - `_rmtree_onexc` (`tools/install.py:254`) opens with lowercase `rmtree` → **D403**.
    Capitalize the first word.
  - `exe` (`tools/install.py:186`) returns a value its docstring never documents →
    **DOC201**. Add a `Returns:` section.
  - The module docstring (`tools/install.py:2`) trips **D301** (the `\\` line
    continuation in the example at `:50`) and **D416** (`Examples` at `:42` is an
    rST section header, not a google `Examples:`). It is rewritten wholesale — see the
    next bullet — which clears both; no `r"""` prefix is needed because the retired
    examples go with it.
  The two dropped functions carry the remaining two findings (`parse_args` `:110` and
  `_source_dir_for_overrides` `:241`, both DOC201), so they need no work.
  Run `run_ruff_check` before committing.
- **The module docstring is rewritten, not ported.** `tools/install.py:1-67` describes
  the model this issue retires. `src/mcp_coder/install/__init__.py` gets a fresh
  google-style docstring that keeps only what is still true — the *Scope* statement
  (installs Python packages only; staging `.mcp.json` / `.claude/` is the caller's job,
  the sentence `environments.md:141` will point at in Step 6), the three `--source`
  modes, and idempotency / never-blocks-on-input. Removed outright:
  - "A **standalone script**, not part of mcp-coder's importable API" (`:4`) — it is
    now ordinary package code (Decision 1).
  - the whole *Distribution* section (`:6-12`), which documents the
    `<install-prefix>/share/mcp-coder/install.py` data-files copy that Step 5 deletes.
  - "stdlib only — must run before mcp-coder is installed" (`:38`) — dropped with the
    curl bootstrap; the installer now reuses `utils.pyproject_config`.
  - the *Examples* section (`:42-52`) with its `python tools/install.py …` invocations;
    usage lives in the CLI help text and `docs/getting-started/installation.md`.
  Convert the surviving rST underline sections (`Scope`, `Install sources`) to google
  style — plain prose under a one-line summary — so D416 cannot recur.
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
  categorized exactly once. `tests/cli/commands/test_help.py:66` hard-codes the command
  count (`assert len(all_command_names) == 22`); bump it to `23`. Do **not** touch `:38`
  (`assert len(COMMAND_CATEGORIES) == 4` — the category count, unchanged) and do not touch
  `expected_commands` at `:42-65`, which is asserted as a subset, not an equality.
- **`tach.toml`**: new `[[modules]]` `path = "mcp_coder.install"`, `layer = "domain"`,
  `depends_on = [{ path = "mcp_coder.utils" }]`, placed after the `mcp_coder.prompt_sources`
  block; add `{ path = "mcp_coder.install" }` to `mcp_coder.cli`'s `depends_on` (`:56-73`)
  and to `tests`' (`:470-488`).
- **`.importlinter`**: add `mcp_coder.install` as its own row in `layered_architecture`
  between `mcp_coder.prompts` and `mcp_coder.utils`; add **exactly one** row,
  `mcp_coder.install.** -> subprocess`, to `subprocess_isolation`'s `ignore_imports`;
  add `tests.install` to `test_module_independence`.
  **Deliberate divergence from issue #1151** (Decision 8): the issue's Scope asks for a
  wildcard pair and says both rows are required. They are not — an `ignore_imports` row
  that matches no edge is an `AlertLevel.ERROR` hard failure, and `install/__init__.py`
  imports no `subprocess` (it lives in `_env.py`), so the bare row can never match. Do
  not restore it. Add **no** `tests.install` row to `subprocess_isolation` either, for
  the same reason — see the TESTS note.

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

**Constraint on the port:** keep reaching subprocess as a *module attribute* of the module
under test — `_env.subprocess.run`, `_env.subprocess.CalledProcessError`, the form
`tests/tools/test_install_py.py:367,384,398,400,417` already uses. Do **not** add a bare
`import subprocess` to any test in `tests/install/`. `subprocess_isolation` gets no
`tests.install` exemption (see the `.importlinter` bullet in HOW), so such an import breaks
the contract in this same commit.

`tests/install/test_install_env.py`
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

`tests/cli/commands/test_install.py`
- `create_parser()` registers `install` as a subcommand and parses the flags.
- `main()` dispatches `install` to `execute_install` (monkeypatched).

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
>
> Implement Step 2 only. TDD: write the three test files first — `tests/install/`
> (`test_install_env.py`, `test_install_phases.py`, porting
> `tests/tools/test_install_py.py` and rewriting `TestPhaseVersions`) plus
> `tests/cli/commands/test_install.py` for the parser/dispatch coverage — then build
> `src/mcp_coder/install/` and the CLI wiring until they pass, then delete
> `tests/tools/test_install_py.py`. Test files mirror their source module; do not put the
> CLI-dispatch test under `tests/install/`.
>
> Leave `tools/install.py`, `tools/install.bat`, `tools/install.sh`, `pyproject.toml`'s
> `data-files` entry, `ci.yml` and everything under `workflows/vscodeclaude/` untouched —
> those are Steps 3 and 5. Keep raw `subprocess.run` and the `--check` mode, but pass
> `check=False` to `subprocess.run` itself (pylint W1510) without forwarding the
> wrapper's own `check` parameter. Define
> `InstallConfig` **and** `MCP_CODER_REPO` / `REPORT_BINARIES` / `REPORT_PACKAGES` in
> `_env.py`, re-export them from `__init__.py`, and have `_phases.py` import them from
> `._env` (see the summary's Decision 11/12 note) — `__init__.py` imports `_phases`, so
> anything `_phases` needs from the package root is an import cycle.
>
> Remember `cli/command_catalog.py` and the hard-coded command count in
> `tests/cli/commands/test_help.py:66` (`all_command_names`, not the `COMMAND_CATEGORIES`
> count at `:38`), or the help tests fail.
>
> The ported docstrings are not clean under `ruff check src` — fix the five surviving
> findings listed in HOW, and rewrite the module docstring for
> `src/mcp_coder/install/__init__.py` rather than porting it (it documents the
> standalone-script / data-files / stdlib-only model this issue retires).
>
> In `.importlinter`, `subprocess_isolation` gets exactly one new row —
> `mcp_coder.install.** -> subprocess`. No bare `mcp_coder.install` row and no
> `tests.install` row: an unmatched `ignore_imports` row fails the contract. Keep the
> ported tests patching `_env.subprocess.run` as an attribute rather than importing
> `subprocess`. This deliberately diverges from issue #1151's Scope — see HOW and
> Decisions.md #8.
>
> Then run `run_format_code`, `run_pylint_check`, `run_mypy_check`, `run_ruff_check`,
> the fast pytest selection, plus `run_tach_check`, `run_lint_imports_check`,
> `run_vulture_check` and `./tools/pycycle_check.sh` — the last four are one PR-only CI
> job, and the ~570 moved lines have never been vulture-scanned. Commit once, green.
