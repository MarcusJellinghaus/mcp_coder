# Step 1: Shared `argv[0]` resolver; command toolkit uses it

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_1.md`) only.
Write the tests first, then the implementation. Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Create `src/mcp_coder/utils/executable.py`
- Create `tests/utils/test_executable.py`
- Modify `src/mcp_coder/toolkits/command/toolkit.py`
- Modify `tests/toolkits/command/test_toolkit_run.py` (`TestResolveExe`)
- Modify `docs/configuration/toolkits.md` (resolution rules; currently say `shutil.which`)

## WHAT

```python
# utils/executable.py
def resolve_executable(argv0: str, project_dir: Path, path: str | None = None) -> str | None:
    """Resolve a step's argv[0]; None when not found.

    path: PATH string to search for bare names; None = os.environ["PATH"].
    """
```

## Rules (from the issue)

- Platform is decided at call time with `sys.platform == "win32"` (tests monkeypatch `sys.platform` and `PATHEXT`; do **not** use `shutil.which`).
- Path-like `argv0` (contains `/`; on Windows also `\`): absolute → as-is; relative → `project_dir / argv0`.
- Bare name: each **absolute** entry of `path` (empty / relative entries skipped → never the cwd).
- Windows: if the name's suffix (lower-case) is in `PATHEXT` → use as-is; otherwise try `<name><ext>` for each `PATHEXT` entry in `PATHEXT` order, extensions lower-cased. No fallback to the extensionless file. `PATHEXT` default when unset: `.COM;.EXE;.BAT;.CMD`.
- A candidate matches when `is_file()`; on POSIX also `os.access(c, os.X_OK)`.

## ALGORITHM

```
windows = sys.platform == "win32"
exts = [e.lower() for e in PATHEXT.split(";") if e] if windows else []
if path-like: bases = [Path(argv0) if absolute else project_dir / argv0]
else:         bases = [Path(d) / argv0 for d in (path or PATH).split(os.pathsep) if d and Path(d).is_absolute()]
for base in bases: for cand in ([base] if not windows or base.suffix.lower() in exts else [base.with_name(base.name + e) for e in exts]):
    if executable(cand): return str(cand)
return None
```

## HOW

- `toolkit.py`: replace both `_resolve_exe(...)` calls with `resolve_executable(...)`; delete `_resolve_exe` and the `shutil` / `os` imports if now unused.
- Rewrite `TestResolveExe` (`test_project_relative`, `test_bare_name`) against `resolve_executable` with real files in `tmp_path` (no `shutil.which` patching), or move them into `tests/utils/test_executable.py` and delete the class.

## Tests (`tests/utils/test_executable.py`)

- POSIX: project-relative script found; non-executable file not found; bare name found in a PATH dir; bare name in cwd only → None; relative PATH entry skipped; explicit `path=` argument used instead of `os.environ`.
- Windows (monkeypatch `sys.platform="win32"`, `PATHEXT=".COM;.EXE;.BAT;.CMD"`): `./mvnw` → `mvnw.cmd`; `./gradlew` → `gradlew.bat`; only extensionless `mvnw` present → None; `PATHEXT` order respected (`x.exe` beats `x.cmd`); bare `npm` → `npm.cmd` in a PATH dir; `tool.exe` used as-is; backslash path treated as path-like.

## DATA

Returns the resolved path as `str`, or `None`.
