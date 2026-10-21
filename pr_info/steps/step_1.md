# Step 1: Import walker, classification tests, import-health test

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement step 1 only, test-first: write the classification tests in
> `tests/test_module_imports.py`, then `tests/_import_walker.py`, then the
> import-health test. Run pylint, mypy, ruff and the fast unit tests (see
> CLAUDE.md); all must pass. Format, then make exactly one commit.

## WHERE

- Create `tests/_import_walker.py` (not collected by pytest — no `test_` prefix).
- Create `tests/test_module_imports.py`.

## WHAT

### `tests/_import_walker.py` (stdlib imports only — no `mcp_coder`, no `tests.*`)

```python
SKIPPED_MODULES: frozenset[str] = frozenset({"mcp_coder.__main__"})

def missing_optional_package(exc: BaseException) -> str | None:
    """Return the absent top-level package name if *exc* stems from a missing
    optional extra, else None (= real failure)."""

def walk(package_name: str) -> dict[str, Any]:
    """Import *package_name* and all its submodules; return the report dict."""

def main(argv: list[str]) -> None:
    """argv[1] = report path; write json.dumps(walk("mcp_coder"))."""

if __name__ == "__main__":
    main(sys.argv)
```

### `tests/test_module_imports.py`

```python
STRICT_ENV_VAR = "MCP_CODER_IMPORT_TEST_STRICT"

# classification unit tests (plain functions)
def test_missing_absent_package_is_skip() -> None
def test_missing_submodule_of_present_package_is_fail() -> None
def test_cannot_import_name_is_fail() -> None
def test_import_error_from_module_not_found_is_skip() -> None   # via __cause__
def test_import_error_with_context_module_not_found_is_skip() -> None  # via __context__
def test_non_import_error_is_fail() -> None

# the import-health test
def test_all_mcp_coder_modules_import(tmp_path: Path) -> None
```

## HOW

- Unit tests: `from tests._import_walker import missing_optional_package`
  (same pattern as `from tests.langchain_doubles import ...`).
- Build exceptions directly, e.g.
  `ModuleNotFoundError("No module named 'x'", name="nonexistent_pkg_xyz.sub")`;
  "present package" case uses `name="json.nonexistent_sub"`;
  cause case: `raise ImportError("install extra") from ModuleNotFoundError(...)`
  inside `try/except` to get a real `__cause__`; context case: raise inside an
  `except ModuleNotFoundError:` block.
- Import-health test runs:
  ```python
  execute_subprocess(
      [sys.executable, "-P", str(Path(_import_walker.__file__)), str(report)],
      CommandOptions(timeout_seconds=120, env={"PYTHONPATH": src_parent}),
  )
  ```
  with `from mcp_coder.utils.subprocess_runner import CommandOptions, execute_subprocess`
  and `src_parent = str(Path(mcp_coder.__file__).resolve().parent.parent)`.

## ALGORITHM

`missing_optional_package(exc)`:
```
seen = set(); cur = exc
while cur is not None and id(cur) not in seen:
    seen.add(id(cur))
    if isinstance(cur, ModuleNotFoundError):
        top = (cur.name or "").split(".")[0]
        return top if top and importlib.util.find_spec(top) is None else None
    cur = cur.__cause__ or cur.__context__
return None
```

`walk(package_name)` (root import is NOT caught — a crash is the signal):
```
pkg = importlib.import_module(package_name); report = {package_path: list(pkg.__path__), failures: [], skips: []}
def visit(path, prefix):
    for info in pkgutil.iter_modules(path, prefix):
        if info.name in SKIPPED_MODULES: continue
        try: mod = importlib.import_module(info.name)
        except Exception as exc: append {module, type, message} to skips (with "missing") if missing_optional_package(exc) else failures; continue
        if info.ispkg: visit(mod.__path__, info.name + ".")
visit(pkg.__path__, package_name + ".")
```

`test_all_mcp_coder_modules_import`:
```
result = execute_subprocess(...)
assert not result.timed_out and result.return_code == 0, stderr tail
report = json.loads(report_path.read_text(encoding="utf-8"))
assert normalised report["package_path"] == normalised list(mcp_coder.__path__)
assert not report["failures"], one line per failure "module: Type: message"
if skips: warnings.warn(listing); if os.environ.get(STRICT_ENV_VAR) == "1": pytest.fail(listing)
```

## DATA

Report JSON:
```json
{
  "package_path": ["<abs path to mcp_coder>"],
  "failures": [{"module": "mcp_coder.x", "type": "ImportError", "message": "cannot import name ..."}],
  "skips":    [{"module": "mcp_coder.y", "missing": "langchain_openai", "message": "..."}]
}
```
Path comparison: compare `os.path.normcase(str(Path(p).resolve()))` lists.

## Preconditions / checks

- The import-health test must pass on this dev env (`.[dev]`) with **zero
  skips**. If it reports a genuine failure in an existing `mcp_coder` module,
  write one line to `pr_info/.blocked.txt` naming the module and stop.
- Check once by hand that every directory under `src/mcp_coder` containing
  `.py` files has an `__init__.py` (otherwise `iter_modules` skips it). If one
  does not, write one line to `pr_info/.blocked.txt` naming it and stop.
- Commit message: `test: add import-health check for every mcp_coder module (#1246)`
