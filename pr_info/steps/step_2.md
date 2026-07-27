# Step 2 — Wire the guard into `__init__.py` (fail-open)

**One commit.** Read `pr_info/steps/summary.md` first. Depends on Step 1
(`mcp_coder._depcheck` must already exist).

This step calls the guard as the **first statement** of package load, so every
`import mcp_coder` (CLI and library) is protected before the heavy imports run.

## WHERE

- Modify `src/mcp_coder/__init__.py`
- Add a smoke test to `tests/test_depcheck.py` (or a small
  `tests/test_init_guard.py` — either is fine; keep it with the other guard
  tests).

## WHAT

No new functions. Insert the guard block at the very top of `__init__.py`,
**after the module docstring** and **before** the first
`from .checks.branch_status import ...` import.

## HOW — the guard block

```python
# Fail cleanly (not with a cryptic traceback) when a mandatory dependency is
# missing — e.g. a `pip install --no-deps` install. Must run before the heavy
# imports below. Fail-open: any unexpected internal error is swallowed so a
# healthy install is never broken (SystemExit subclasses BaseException, so the
# intended clean exit-1 still propagates). See mcp_coder/_depcheck.py.
try:
    from . import _depcheck

    _depcheck.ensure_dependencies()
except Exception:  # noqa: BLE001 — fail-open: never break a healthy install
    pass
```

- Importing `._depcheck` from inside `__init__` while it executes is safe: the
  package is already in `sys.modules`, so it does not re-trigger `__init__`.
- Leave the existing `__version__` block and all other imports **unchanged**.

## ALGORITHM

None beyond the guard block above.

## DATA

No new data structures. `ensure_dependencies()` returns `None` on healthy
installs; the surrounding `try/except` makes the guard a no-op there.

## TEST — smoke / regression

Confirms the guard does not break normal import in the dev/test env:

- `import mcp_coder` succeeds and `mcp_coder.__version__` is a non-empty `str`.
- `mcp_coder._depcheck.ensure_dependencies()` is callable and returns `None`
  in this env, so the guard passes through.

Keep the assertion **strictly behavioral** (`assert ensure_dependencies() is
None`). Do **not** encode the environment's metadata state into the test — in
particular do **not** assert that `requires("mcp-coder")` raises
`PackageNotFoundError`. mcp-coder may be editable-installed here (metadata
present, guard enumerates all mandatory deps and finds none missing) **or**
run source-only (no dist, short-circuits to `[]`); the behavioral assertion
holds in both, whereas a metadata-state assertion would break under an
editable install.

### Fail-open regression test (swallow-and-continue)

The guard's headline guarantee — an unexpected internal `_depcheck` error must
**never** break a healthy install — needs its own test; the smoke test above
only exercises the happy pass-through.

- Monkeypatch `mcp_coder._depcheck.find_missing_dependencies` to raise a
  **non-`SystemExit`** exception (e.g. `RuntimeError("boom")`), then
  `importlib.reload(mcp_coder)` and assert the reload **succeeds** —
  `mcp_coder.__version__` is a non-empty `str`. This proves the `__init__`
  guard's `except Exception` swallowed the internal error and loading proceeded
  (import does not propagate the exception).
- Contrast (already covered, do not re-test here): the intended clean
  `SystemExit(1)` on a real broken install is **not** swallowed, because
  `SystemExit` subclasses `BaseException`, not `Exception`; that exit path is
  covered by Step 1's `ensure_dependencies()` test.
- Restore the patch (fixture teardown / `monkeypatch` auto-undo) and
  `importlib.reload(mcp_coder)` once more so later tests see the real module.

(The broken-install path itself is fully covered by Step 1's pure-function
tests — no subprocess or hand-broken venv is needed.)

## Checks (per CLAUDE.md — all must pass)

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
```

Also confirm import contracts still pass (the new root module imports nothing
from `mcp_coder.*`, so no contract should change):

```
mcp__tools-py__run_lint_imports_check
```

## LLM prompt

> Implement Step 2 from `pr_info/steps/step_2.md` (context in
> `pr_info/steps/summary.md`). Add the 4-line fail-open guard block to the top
> of `src/mcp_coder/__init__.py` — after the module docstring, before the first
> real import — calling `_depcheck.ensure_dependencies()` exactly as specified.
> Do not change the existing `__version__` block or any other imports. Add the
> smoke test verifying `import mcp_coder` still works and the guard passes
> through here (keep the assertion behavioral — `ensure_dependencies()` returns
> `None` — without asserting the environment's metadata state, per the TEST
> section). Use MCP workspace tools for all file
> operations. Run pylint, mypy, pytest (fast-unit marker exclusions per
> CLAUDE.md), and lint-imports, and fix anything until all pass. This step is
> one commit.
