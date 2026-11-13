# Step 2: Shared two-file table lookup and setup config loader

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_2.md`) only.
Write the tests first, then the implementation. Existing toolkit config tests must pass unchanged. Run format, pylint, pytest (unit filter, `-n auto`), mypy, lint-imports and tach; all must pass. One commit.

## WHERE

- Modify `src/mcp_coder/utils/toml_utils.py` — add `find_mcp_coder_table`
- Modify `src/mcp_coder/utils/toolkit_runner.py` — `load_toolkit_config` uses it
- Create `src/mcp_coder/utils/setup_config.py`
- Create `tests/utils/test_setup_config.py` (also cover `find_mcp_coder_table` here or in the existing toml_utils tests)

## WHAT

```python
# toml_utils.py
MCP_CODER_CONFIG_FILES = ("pyproject.toml", "mcp-coder.toml")

def find_mcp_coder_table(project_dir: Path, table: str) -> tuple[str, Any] | None:
    """Return (file name, raw value) of [tool.mcp-coder.<table>], or None.

    Raises ValueError if a file is malformed, 'tool'/'mcp-coder' is not a
    table, or both files define the table.
    """

# setup_config.py
BUILTINS = frozenset({"python"})
DEFAULT_STEP_TIMEOUT = 1800

@dataclass(frozen=True)
class SetupStep:
    argv: tuple[str, ...] | None   # exactly one of argv / builtin is set
    builtin: str | None
    name: str | None
    timeout: int                   # DEFAULT_STEP_TIMEOUT for builtin steps

    @property
    def label(self) -> str: ...    # name, else builtin, else " ".join(argv)

@dataclass(frozen=True)
class SetupConfig:
    steps: tuple[SetupStep, ...]
    source: str | None             # file name; None = default (no table)

    def uses_python(self) -> bool: ...  # any step.builtin == "python"

def load_setup_config(project_dir: Path) -> SetupConfig: ...
```

## HOW

- Move the loop from `load_toolkit_config` (the `for file_name in _CONFIG_FILES` block and the "Both … define … keep one" check) into `find_mcp_coder_table`. Keep the exact error texts, built with `f"[tool.mcp-coder.{table}]"`, so the existing toolkit tests still match.
- `load_toolkit_config`: `found = find_mcp_coder_table(project_dir, "toolkit")`; `None` → defaults; else `source, table = found`.

## ALGORITHM (`load_setup_config`)

```
found = find_mcp_coder_table(project_dir, "setup")
if found is None: return SetupConfig((SetupStep(None, "python", None, 1800),) if (project_dir/"pyproject.toml").is_file() else (), None)
source, table = found; table must be a dict whose only key is "steps" (required) -> else ValueError
steps must be a list; each item a dict, keys ⊆ {argv, builtin, name, timeout}, exactly one of argv/builtin
argv: non-empty list of str; builtin: str in BUILTINS; name: str; timeout: positive int (not bool), only with argv
return SetupConfig(tuple(parsed), source)
```

Every error is `ValueError` naming the file, `[tool.mcp-coder.setup]`, the step index (`steps[2]`) and the offending key/value — same style as `toolkit_runner`.

## Tests

- No table + `pyproject.toml` → one `python` built-in step, `source is None`; no table, no `pyproject.toml` → `steps == ()`.
- `steps = []` → empty; table in `mcp-coder.toml` only → `source == "mcp-coder.toml"`; both files define it → error.
- Toolkit in `mcp-coder.toml`, setup in `pyproject.toml` → both load (per-table rule).
- Errors: missing `steps`; unknown top-level key; step not a table; unknown step key; both/neither `argv`/`builtin`; empty `argv`; non-str element; unknown builtin; `timeout` on builtin; `timeout` 0 / negative / bool / str; `name` not a str; malformed TOML.
- `label` and `uses_python()`; default timeout 1800.
- `find_mcp_coder_table`: returns `None` when absent; non-table `tool` → error.

## DATA

`SetupConfig(steps=(SetupStep(...), ...), source="pyproject.toml" | "mcp-coder.toml" | None)`.
