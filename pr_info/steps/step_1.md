# Step 1: Contract shim and strict `[tool.mcp-coder.toolkit]` config loading

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **step 1** as described in
> `pr_info/steps/step_1.md`. Write the tests first, then the code. Nothing calls the new
> code yet. Run pylint, mypy, pytest (fast unit tests), lint-imports and format, then
> make exactly one commit.

## Precondition

`from mcp_coder_utils.toolkit import validate_params` must work in the project venv
(probe with a scratch test). If it fails, write one line to `pr_info/.blocked.txt`
saying the installed mcp-coder-utils has no toolkit module, and stop.

## WHERE

- New `src/mcp_coder/utils/toolkit.py` (shim)
- New `src/mcp_coder/utils/toolkit_runner.py` (config part only in this step)
- `src/mcp_coder/utils/toml_utils.py`, `src/mcp_coder/utils/pyproject_config.py`
- `.importlinter`, `pyproject.toml`
- `docs/configuration/config.md`, `docs/repository-setup/python.md` (one row each)
- New `tests/utils/test_toolkit_config.py`

## WHAT

`utils/toolkit.py` — same style as `utils/subprocess_streaming.py`:

```python
"""Toolkit contract — thin shim over mcp-coder-utils."""
from mcp_coder_utils.toolkit import (ActionRequest, ActionResult, Finding, Toolkit,
                                     ToolkitInfo, VerifyItem, validate_params)
__all__ = [...]
```

`utils/toml_utils.py`:

```python
def load_toml(path: Path, *, strict: bool = False) -> dict[str, Any]
```
Move the body of `_load_pyproject` here (missing file → `{}`; parse/read error →
`ValueError` with `format_toml_error` when strict, else `{}`).
`_load_pyproject(project_dir, strict=...)` becomes `return load_toml(project_dir / "pyproject.toml", strict=strict)`.

`utils/toolkit_runner.py` (config part):

```python
DEFAULT_TOOLKIT = "mcp-tools-py"
DEFAULT_BINDINGS: dict[str, tuple[str, ...]] = {
    "implement_task": (),
    "implement_final": ("check@quick",),
    "commit": ("format@apply",),
    "rebase": ("check@standard", "test@standard"),
    "rebase_automated": ("check@standard", "test@unattended"),
}
_ALLOWED_ACTIONS: dict[str, frozenset[str]] = {
    "implement_task": frozenset(),
    "implement_final": frozenset({"check"}),
    "commit": frozenset({"format"}),
    "rebase": frozenset({"check", "test"}),
    "rebase_automated": frozenset({"check", "test"}),
}
_REQUEST_RE = re.compile(r"^[a-z][a-z0-9_-]*@[a-z][a-z0-9_-]*$")
_CONFIG_FILES = ("pyproject.toml", "mcp-coder.toml")

@dataclass(frozen=True)
class ToolkitConfig:
    toolkit: str                              # entry-point key
    bindings: dict[str, tuple[str, ...]]      # every entry, defaults merged
    params: dict[str, dict[str, Any]]         # raw [..toolkit.params] tables
    section: dict[str, Any]                   # [tool.mcp-coder.toolkit.<toolkit>] or {}
    source: str | None                        # file name the table came from, None = default

def load_toolkit_config(project_dir: Path) -> ToolkitConfig   # raises ValueError
def get_binding(project_dir: Path, entry: str) -> tuple[str, ...]
```

## ALGORITHM

```
tables = {name: t for name in _CONFIG_FILES
          if (t := load_toml(project_dir / name, strict=True)
                    .get("tool", {}).get("mcp-coder", {}).get("toolkit")) is not None}
if len(tables) == 2: raise ValueError("both define [tool.mcp-coder.toolkit]; keep one")
if not tables: return ToolkitConfig(DEFAULT_TOOLKIT, dict(DEFAULT_BINDINGS), {}, {}, None)
source, table = the single item; require dict; name = table.get("toolkit", DEFAULT_TOOLKIT) (str)
reject name in {"bindings","params"}; reject keys {"format","check","test"} (per-action not supported yet);
reject any key not in {"toolkit","bindings","params",name}; section = table.get(name, {}) must be dict
bindings = DEFAULT_BINDINGS | validated(table.get("bindings", {})); params = validated(table.get("params", {}))
```

Binding validation (per entry): entry must be in `DEFAULT_BINDINGS`; value a list of
strings; each matches `_REQUEST_RE`; action in `_ALLOWED_ACTIONS[entry]`
(`implement_task` therefore must be empty); `commit` rejects `format@check`.
Params validation here is shape only: a dict of action → dict. Values are checked
against the toolkit's schema in step 2.

Every error message names the file (`source`) and the offending key/value.

## DATA

- `load_toolkit_config` → `ToolkitConfig`; `ValueError` for every config error.
- `get_binding(project_dir, entry)` → `load_toolkit_config(project_dir).bindings[entry]`.

## HOW

- `.importlinter` → `mcp_coder_utils_isolation.ignore_imports` add
  `mcp_coder.utils.toolkit -> mcp_coder_utils`.
- `pyproject.toml` (this repo, acceptance criterion):
  ```toml
  [tool.mcp-coder.toolkit]
  toolkit = "mcp-tools-py"
  ```
- Docs: add `[tool.mcp-coder.toolkit]` (toolkit, bindings, params; `pyproject.toml`
  else `mcp-coder.toml`; reader `utils/toolkit_runner.py`) to the `pyproject.toml` row of
  `docs/configuration/config.md` and one row to the table in
  `docs/repository-setup/python.md`. Keep it to one line each; #1200 writes the
  reference docs.

## Tests (`tests/utils/test_toolkit_config.py`, write first)

- No file / no table → `toolkit == "mcp-tools-py"`, `bindings == DEFAULT_BINDINGS`, `source is None`.
- Table in `pyproject.toml` only, and in `mcp-coder.toml` only (no `pyproject.toml`) → resolved, `source` set.
- Both files with the table → `ValueError`. Both files, only one with the table → ok.
- Malformed TOML in either file → `ValueError` (strict), even when the other file is fine.
- Binding override replaces only that entry; others keep defaults.
- Parametrized `ValueError` cases: unknown top-level key; unknown binding entry;
  non-list binding; `"check"` (no `@`); `"check@"`; `implement_task = ["check@quick"]`;
  `implement_final = ["test@quick"]`; `rebase = ["format@apply"]`;
  `commit = ["format@check"]`; `commit = ["check@quick"]`; `toolkit = "bindings"`;
  `toolkit = "params"`; per-action `check = "x"`; params not a table; section not a table.
- Section `[tool.mcp-coder.toolkit.mcp-tools-py]` returned in `section`; absent → `{}`.
- `tests/utils/test_pyproject_config.py` keeps passing (behaviour of `_load_pyproject` unchanged).
