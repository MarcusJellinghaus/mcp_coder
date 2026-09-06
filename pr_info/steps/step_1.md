# Step 1 — Shared TOML plumbing in `mcp_coder.utils`

Prerequisite for Step 2: the installer needs a strict pyproject load and an extras
reader. Independent of everything else; ships as one commit.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder/utils/toml_utils.py` | **new** |
| `src/mcp_coder/utils/user_config.py` | modified (`:34`, `:107-176`, `:208`) |
| `src/mcp_coder/utils/pyproject_config.py` | modified (all three readers) |
| `src/mcp_coder/config/label_config.py` | modified (comment at `:114` only) |
| `tests/utils/test_user_config.py` | modified (`:9` import + 10 call sites) |
| `tests/utils/test_pyproject_config.py` | modified (new cases) |

## WHAT

`src/mcp_coder/utils/toml_utils.py`:

```python
def format_toml_error(file_path: Path, error: tomllib.TOMLDecodeError) -> str:
```

Moved verbatim from `user_config._format_toml_error` (`:107-176`), renamed public.
Two edits to the body: hoist its function-local `import re` (`:117`) to module level,
and bring the module-level `_SMART_QUOTES` constant (`user_config.py:34`) along — it is
used only by this function (`:171`), so it moves with it rather than being left behind
as dead code in `user_config`.

`src/mcp_coder/utils/pyproject_config.py`:

```python
def _load_pyproject(project_dir: Path, *, strict: bool = False) -> dict[str, Any]:
def get_install_extras(project_dir: Path, *, strict: bool = False) -> str | None:
```

`get_install_extras` returns `None` when the key is not declared — **not** `"dev"`. It is
the single public reader of `[tool.mcp-coder.install] extras`, serving both the installer
(Step 2, which applies the `"dev"` fallback in `InstallConfig.from_args`) and Step 4's
warn-only contract row (which needs declared-vs-absent). A second predicate would read the
same key twice.

## HOW

- `user_config.py`: `from .toml_utils import format_toml_error`, delete the private
  function **and** the now-unused `_SMART_QUOTES` constant (`:34`), update the single
  call at `:208`.
- `pyproject_config.py`: `from .toml_utils import format_toml_error`; rewrite
  `get_prompts_config`, `get_github_install_config`, `get_implement_config` to call
  `_load_pyproject(project_dir)` (lax) instead of each doing its own
  `path.exists()` / `open` / `tomllib.load` / `except` block. Their public behaviour
  and return types are unchanged.
- `get_install_extras` returns a plain `str | None`, not a frozen dataclass — the section
  has one field, and a wrapper class would add an import and a `.extras` hop for nothing.
- `label_config.py:114`: one comment line stating that `mcp_coder.config` sits below
  `mcp_coder.utils` in the layer stack and therefore cannot import `pyproject_config`.

## ALGORITHM

```
_load_pyproject(project_dir, strict):
    path = project_dir / "pyproject.toml"
    if not path.exists(): return {}                      # missing file is never an error
    try: return tomllib.load(open(path, "rb"))
    except TOMLDecodeError as e:
        if strict: raise ValueError(format_toml_error(path, e)) from e
        return {}
    except OSError as e:
        if strict: raise ValueError(f"Error reading {path}\n{e}") from e
        return {}

get_install_extras(project_dir, strict):
    section = _load_pyproject(project_dir, strict=strict).get("tool", {}).get("mcp-coder", {}).get("install", {})
    return section.get("extras")                         # None == not declared; "" is honoured
```

## DATA

- `_load_pyproject` → parsed TOML `dict[str, Any]`; `{}` for missing file, and for a
  malformed one when `strict=False`.
- `get_install_extras` → `str | None`. `None` when the file, section or key is absent;
  `""` when the repo declares no extras. Comma-separated values (`"dev,mlflow"`) pass
  through unparsed — splitting is the installer's job. The `"dev"` fallback is *not*
  applied here; Step 2's `InstallConfig.from_args` owns it.
- Malformed TOML with `strict=True` → `ValueError` whose message names the file
  (via `format_toml_error`).

## TESTS (write first)

`tests/utils/test_pyproject_config.py` — new cases:

- `get_install_extras`: declared value returned; key absent → `None`; section absent →
  `None`; file absent → `None`; malformed file (lax) → `None`; explicit `extras = ""` →
  `""` (distinct from `None` — this is the pair Step 4's warn row turns on).
- `_load_pyproject`: missing file → `{}` under both `strict` values; malformed TOML →
  `{}` when lax, `ValueError` naming the file when strict.
- One regression case per existing reader confirming behaviour is unchanged for a
  malformed file (still returns the neutral default, does not raise).

`tests/utils/test_user_config.py` — change the import at `:9` to
`from mcp_coder.utils.toml_utils import format_toml_error` and rename the 10 call
sites (`:18` docstring, `:36`, `:60`, `:83`, `:104`, `:125`, `:144`, `:162`, `:187`).
All assertions stay as they are: this pins that `user_config`'s error path is unchanged.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement Step 1 only. TDD: write the new `tests/utils/test_pyproject_config.py`
> cases first, watch them fail, then implement `toml_utils.format_toml_error`,
> `pyproject_config._load_pyproject` and `pyproject_config.get_install_extras`, and
> update `user_config` plus `tests/utils/test_user_config.py`.
>
> Do not touch `tools/install.py`, the CLI, or anything under `workflows/` — those are
> later steps. Do not add a `strict` parameter to `get_github_install_config`
> (see the summary's note on Decision 13).
>
> `get_install_extras` returns `str | None` and does **not** apply the `"dev"` fallback —
> that belongs to Step 2's `InstallConfig.from_args`. Do not add a second reader or
> predicate for the same key.
>
> Then run `run_format_code`, `run_pylint_check`, `run_mypy_check`, `run_ruff_check` and
> the fast pytest selection from the summary, and commit once with everything green.
