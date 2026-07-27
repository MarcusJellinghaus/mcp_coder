# Step 1 — Create the pure `_depcheck` module (TDD)

**One commit.** Read `pr_info/steps/summary.md` first for full context.

This step creates the standalone dependency-check module and its tests. It does
**not** touch `__init__.py` — that is Step 2. Written test-first.

## WHERE

- Create `tests/test_depcheck.py`
- Create `src/mcp_coder/_depcheck.py`

`_depcheck.py` is a **root-level** module (`mcp_coder._depcheck`). It imports
**only** the stdlib and `packaging` — nothing from `mcp_coder.*`, no heavy
imports. This keeps it outside the layered architecture and safe to import from
inside `__init__` while `__init__` is still executing.

## WHAT — function signatures

```python
# src/mcp_coder/_depcheck.py
from importlib.metadata import PackageNotFoundError, requires, version
from packaging.requirements import Requirement

def find_missing_dependencies() -> list[str]:
    """Return declared mandatory distributions that are not installed.

    Pure: no side effects, no heavy imports. Returns [] when mcp-coder's own
    distribution metadata is absent (source-only / pythonpath runs) or when
    requires() yields nothing — the guard cannot enumerate deps, so it must
    not block.
    """

def ensure_dependencies() -> None:
    """Print a friendly message to stderr and exit 1 if deps are missing."""

def _installed_version() -> str:
    """mcp-coder version via importlib.metadata, or the dev fallback."""
```

## HOW — integration points

- Import names into the module namespace as
  `from importlib.metadata import PackageNotFoundError, requires, version`
  so tests can monkeypatch `mcp_coder._depcheck.requires`.
- Marker evaluation: `req.marker.evaluate()` with the **default** environment
  (no `extra` set) — this makes `extra == "..."` markers evaluate `False`
  (drops optional-extra deps) and platform markers like
  `sys_platform == 'win32'` (pywin32) evaluate against the real platform.
- `_installed_version()` reuses the `PackageNotFoundError → "0.0.0.dev0+unknown"`
  fallback pattern that `__init__` already uses.

## ALGORITHM

`find_missing_dependencies()`:
```
try:
    reqs = requires("mcp-coder") or []      # None or missing metadata -> no-op
except PackageNotFoundError:
    return []
missing = []
for spec in reqs:
    req = Requirement(spec)
    if req.marker and not req.marker.evaluate():   # drop extras + off-platform
        continue
    try:
        version(req.name)                          # distribution present?
    except PackageNotFoundError:
        missing.append(req.name)
return missing
```

`ensure_dependencies()`:
```
missing = find_missing_dependencies()
if not missing:
    return
print(f"mcp-coder {_installed_version()}", file=sys.stderr)
print(f"Installation incomplete — missing required dependencies: {', '.join(missing)}", file=sys.stderr)
print("This looks like a --no-deps install. Reinstall with:  pip install mcp-coder", file=sys.stderr)
raise SystemExit(1)
```

## DATA

- `find_missing_dependencies()` → `list[str]` of missing **distribution** names
  (declared order preserved), or `[]`.
- `ensure_dependencies()` → `None` on a healthy env; otherwise writes 3 lines to
  stderr and raises `SystemExit(1)`.
- `_installed_version()` → `str`.

## TESTS — `tests/test_depcheck.py`

Pure-function tests, single patch seam (`mcp_coder._depcheck.requires`):

1. `requires` raising `PackageNotFoundError` → `find_missing_dependencies() == []`.
2. `requires` returning `None` → `find_missing_dependencies() == []`.
3. `requires` returning `["definitely-absent-xyz>=1"]` → returns
   `["definitely-absent-xyz"]` (real `version()` lookup reports it absent).
4. `requires` returning `["some-pkg; extra == 'dev'"]` → `[]` (extra marker
   dropped).
5. `ensure_dependencies()` with `find_missing_dependencies` monkeypatched to
   return `[]` → returns `None`, no exit.
6. `ensure_dependencies()` with `find_missing_dependencies` monkeypatched to
   return `["python-jenkins", "textual"]` → `pytest.raises(SystemExit)` with
   code `1`; `capsys` stderr contains `"mcp-coder "`, `"Installation incomplete"`,
   both dep names, and `"pip install mcp-coder"`.

## Checks (per CLAUDE.md — all must pass)

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
```

## LLM prompt

> Implement Step 1 from `pr_info/steps/step_1.md` (context in
> `pr_info/steps/summary.md`). Work test-first: create `tests/test_depcheck.py`
> with the six cases listed, then create `src/mcp_coder/_depcheck.py` with
> `find_missing_dependencies()`, `ensure_dependencies()`, and `_installed_version()`
> exactly as specified. `_depcheck.py` must import only the stdlib and
> `packaging` — nothing from `mcp_coder.*`. Do **not** modify `__init__.py` in
> this step. Use MCP workspace tools for all file operations. Then run pylint,
> mypy, and pytest (fast-unit marker exclusions per CLAUDE.md) and fix anything
> until all three pass. This step is one commit.
