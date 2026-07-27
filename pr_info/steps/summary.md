# Summary — Fail cleanly on incomplete installs (missing mandatory deps)

Issue #1076.

## Problem

`import mcp_coder` eagerly pulls heavy imports during package load
(`mcp_coder/__init__.py` → `.utils.subprocess_runner` → `utils/__init__.py` →
`from .jenkins_operations ...` → `from jenkins import Jenkins`). When a
**mandatory** external dependency is missing — which happens on a
`pip install --no-deps` install of `mcp-coder` — package load crashes with a
raw `ModuleNotFoundError` traceback before `main()` ever runs. `python-jenkins`
crashes first; `textual`, `psutil`, `tabulate`, and `python-frontmatter` would
follow, since all are mcp-coder-unique and eagerly imported on the boot path.

## Decision (from the issue — not up for change here)

- `--no-deps` installs are **unsupported**. The goal is **not** to make them
  work — it is to **fail with a clear, diagnosable message** instead of a
  traceback.
- `python-jenkins` **stays a mandatory** runtime dependency. No lazy imports,
  no optional extras, no moving modules. The original (superseded) lazy-import
  proposal must NOT be implemented.

## Approach — startup dependency guard

A tiny stdlib + `packaging` module `src/mcp_coder/_depcheck.py` with two
functions, called as the **first statement** of `mcp_coder/__init__.py`.

1. `find_missing_dependencies() -> list[str]` — **pure**. Enumerates declared
   **mandatory** deps via `importlib.metadata.requires("mcp-coder")` +
   `packaging.requirements.Requirement` (marker evaluation drops extras and
   non-applicable platform markers), then checks each **distribution** is
   installed via `importlib.metadata` — presence, **not** importability, so no
   import-name↔dist-name map is ever needed. Returns the missing distribution
   names.
2. `ensure_dependencies() -> None` — thin wrapper. If anything is missing,
   prints version + friendly message to **stderr**, then `raise SystemExit(1)`.

### Guaranteed behaviours

- **No-metadata / source-only runs no-op.** Under `pythonpath=["src"]` (how
  pytest runs here) there is no installed dist, so `requires("mcp-coder")`
  raises `PackageNotFoundError`; `requires()` may also return `None`. Both →
  `find_missing_dependencies()` returns `[]` and loading proceeds.
- **Fail-open on unexpected internal error.** The `__init__` guard is wrapped
  in `try/except Exception`, so any unforeseen error is swallowed and normal
  loading proceeds (worst case: today's traceback). `SystemExit` subclasses
  `BaseException`, not `Exception`, so the intended clean exit-1 still
  propagates. The guard can only ever convert a broken install into a clean
  message — never introduce a new failure on a healthy one.
- **Healthy install:** `ensure_dependencies()` finds nothing missing and
  returns in microseconds.

### Error output (stderr, no traceback)

```
mcp-coder 1.4.2
Installation incomplete — missing required dependencies: python-jenkins, textual, psutil, tabulate, python-frontmatter
This looks like a --no-deps install. Reinstall with:  pip install mcp-coder
```

Version is read standalone via `importlib.metadata.version("mcp-coder")` with
the same `PackageNotFoundError → "0.0.0.dev0+unknown"` fallback `__init__`
already uses (NOT via `from mcp_coder import __version__`, which would re-trigger
the crashing `__init__`).

## Architectural / design changes

- **New root-level module `mcp_coder._depcheck`** — stdlib + `packaging` only,
  no internal imports, no heavy imports. It sits *outside* the layered
  architecture (imports nothing from `mcp_coder.*`), so it does not affect any
  import-linter contract.
- **Package-load-time guard**, not a CLI-only guard. Every `import mcp_coder`
  (CLI *and* library use) is governed. This is intentional: the crash happens
  during package load, before `main()`, so a guard inside `main()` would be too
  late. In a broken install a library import would crash anyway, so converting
  it to a clean message is strictly an improvement.
- **Entry point and package layout unchanged** — `mcp_coder.cli.main:main`,
  normal package, nothing moves. No `pyproject.toml` change.
- **`packaging` stays undeclared** as a direct dependency (it is effectively
  universal, shipping with pip/setuptools). Its absence is covered by
  fail-open. Adding it as a dependency would itself be skipped under
  `--no-deps`, so declaring it buys nothing for the scenario this guards.

## KISS notes

- Distribution presence is a plain per-name loop: `version(name)` in a
  `try/except PackageNotFoundError` — no set-building, no name normalization,
  no `distribution()` objects.
- `find_missing_dependencies()` stays seam-free (no injection parameters).
  Tests inject a bogus missing dep by patching **only**
  `mcp_coder._depcheck.requires`, relying on the real `version()` lookup to
  report it absent — one patch point.
- Fail-open is four lines in `__init__`; `SystemExit` propagation is automatic.
- `__init__`'s existing version block is left untouched; `_depcheck` reads its
  own version (≈4 duplicated lines) rather than coupling the two modules.

## Files created / modified

| File | Change |
|------|--------|
| `src/mcp_coder/_depcheck.py` | **created** — pure `find_missing_dependencies()` + thin `ensure_dependencies()` |
| `tests/test_depcheck.py` | **created** — unit tests for the pure function + wrapper |
| `src/mcp_coder/__init__.py` | **modified** — 4-line fail-open guard as the first statement |

No folders, entry points, `pyproject.toml`, or import-linter contracts change.

## Steps

- **Step 1** — `pr_info/steps/step_1.md`: create `_depcheck.py` + `test_depcheck.py` (TDD).
- **Step 2** — `pr_info/steps/step_2.md`: wire the guard into `__init__.py` + smoke test.

Each step is exactly one commit (tests + implementation + all checks passing).
