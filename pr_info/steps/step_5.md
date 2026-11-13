# Step 5: `setup_integration` tests and marker registration

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_5.md`) only. Step 4 must be done: if `mcp-coder setup` is not a registered CLI command, write one line to `pr_info/.blocked.txt` and stop.
This step adds integration tests only (no production code). Run format, pylint, mypy, lint-imports and tach, and the unit pytest filter (`-n auto`, now also excluding `setup_integration`); all must pass. Also run `markers=["setup_integration"]` — tests whose toolchain is missing must skip, not fail. One commit.

## WHERE

- Create `tests/install/test_setup_integration.py`
- Modify `pyproject.toml` — marker `"setup_integration: tests that run real project setup toolchains (npm, cargo, uv) via mcp-coder setup"`
- Modify `.claude/CLAUDE.md` — unit `-m` expression gets `and not setup_integration`; marker list gets `setup_integration`
- Modify `.github/workflows/ci.yml` — unit job `-m` adds `and not setup_integration`; integration job becomes `'git_integration or install_integration or setup_integration'`
- Modify `.run/pytest in tests - just unit tests.run.xml` and `tools/get_pytest_performance_stats.bat` — add `and not setup_integration`

## WHAT

```python
pytestmark = pytest.mark.setup_integration

def _run_setup(project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """sys.executable -m mcp_coder setup --project-dir <project> <extra>, capture output."""

def _npm_fixture(path: Path) -> None: ...     # package.json + package-lock.json (lockfileVersion 3, no deps), mcp-coder.toml with npm ci
def _rust_fixture(path: Path) -> None: ...    # Cargo.toml, src/main.rs, Cargo.lock (version 3, the package only), mcp-coder.toml with cargo fetch --locked
def _python_fixture(path: Path) -> None: ...  # dependency-free pyproject.toml with [tool.mcp-coder.install] extras = ""
```

## Tests

- `test_npm_setup` (skip unless `shutil.which("npm")`): `git init` the fixture (GitPython `git.Repo.init`, as `tests/conftest.py` does), `.gitignore` with `node_modules/`, commit everything; setup exits 0.
- `test_rust_setup` (skip unless `shutil.which("cargo")`): exits 0.
- `test_python_setup` (skip unless `shutil.which("uv")`): `--skip-overrides`; exits 0 and `.venv` has an interpreter.
- `test_python_setup_untracked_lockfile_fails` (skip unless `uv`): `git init`, `.gitignore` with `.venv/`, commit; setup exits non-zero and output names `uv.lock` (uv sync creates it, it is neither tracked nor ignored).

## HOW

- Every fixture is written into `tmp_path`; nothing is written into the checkout.
- Run the code under test with `sys.executable -m mcp_coder`, never the `mcp-coder` on `PATH`.
- `tests.install.**` may import `subprocess` (existing import-linter exception).
- Reuse the fixture shape of `tests/install/test_install_integration.py::_write_fixture_project` for the Python project (copy it — test packages must not import each other's modules outside their own package conftest).

## DATA

None.
