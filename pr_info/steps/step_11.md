# Step 11 — No toolkit configured is an error (Scope 1, Scope 7)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_11.md`).
> Implement Step 11 only: remove `DEFAULT_TOOLKIT` and both fallbacks in
> `load_toolkit_config`, raise the no-toolkit `ValueError`, narrow
> `ToolkitConfig.source` to `str`, and teach the autouse test fixture to supply
> `toolkit = "mcp-tools-py"` with an opt-out marker. Tests first, then code.
> Run format, pylint, mypy and the full fast pytest set. One commit.

## Precondition

`search_files(pattern="DEFAULT_TOOLKIT", glob="src/**/*.py")` must match only
`src/mcp_coder/utils/toolkit_runner.py`. If anything else matches, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py`
- `tests/conftest.py::_resolvable_formatter`
- `pyproject.toml` — register the marker
- Tests:
  - **new** `tests/utils/test_no_toolkit_error.py`
  - `tests/utils/test_toolkit_config.py` — fallback tests become error tests
    with the opt-out marker; drop any `DEFAULT_TOOLKIT` import
  - tests asserting `ToolkitConfig.source is None`
    (`tests/utils/test_toolkit_config.py` ~lines 30, 38). `tests/utils/test_setup_config.py:75`
    asserts `SetupConfig.source is None` and stays unchanged

## WHAT

```python
_CONFIGURE_URL = (
    "https://github.com/MarcusJellinghaus/mcp_coder/blob/main/"
    "docs/configuration/toolkits.md#configure-a-toolkit"
)
_NO_TOOLKIT_HELP = (
    'For Python, add to pyproject.toml: [tool.mcp-coder.toolkit] toolkit = "mcp-tools-py". '
    'For any other stack, add to a root mcp-coder.toml: [tool.mcp-coder.toolkit] toolkit = "command" '
    "— the command toolkit also needs its [tool.mcp-coder.toolkit.command] step tables for the "
    "actions and depths the bindings request (with the default bindings more than format, "
    f"e.g. test@quick and test@unattended). See {_CONFIGURE_URL}"
)

@dataclass(frozen=True)
class ToolkitConfig:
    ...
    source: str  # file name the table came from
```

Messages (one line each, readable in a `verify` row, a failure comment and a log):
- no table: `f"No {_TABLE} table in pyproject.toml or mcp-coder.toml. {_NO_TOOLKIT_HELP}"`
- no key: `f"{_TABLE} in {source} has no toolkit key. {_NO_TOOLKIT_HELP}"`

## ALGORITHM (`load_toolkit_config`)

```
found = find_mcp_coder_table(project_dir, "toolkit")
if found is None: raise ValueError(no-table message)
source, table = found ; table-type check (unchanged)
if "toolkit" not in table: raise ValueError(no-key message)     # before key loop and bindings
name = table["toolkit"] ; string / reserved checks, key loop, section, bindings, params (unchanged)
```

Remove the `DEFAULT_TOOLKIT` constant. Workflows, `verify`, grants and prompt
slots already handle a `ValueError` from `load_toolkit_config`; add no new handling.

## HOW — test fixture (`tests/conftest.py`)

```python
@pytest.fixture(autouse=True)
def _resolvable_formatter(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    from mcp_tools_py.toolkit import PythonToolkit
    from mcp_coder.utils import toolkit_runner

    real_find = toolkit_runner.find_mcp_coder_table

    def _with_toolkit(project_dir: Path, table: str) -> tuple[str, Any] | None:
        found = real_find(project_dir, table)
        if table != "toolkit": return found
        if found is None: return ("pyproject.toml", {"toolkit": "mcp-tools-py"})
        source, raw = found
        if isinstance(raw, dict) and "toolkit" not in raw: return (source, {**raw, "toolkit": "mcp-tools-py"})
        return found

    real = request.node.get_closest_marker("real_toolkit_config") is not None
    with ExitStack() as stack:
        stack.enter_context(patch("mcp_coder.workflow_steps.commit.verify_toolkit", lambda _l, _p, _a: []))
        stack.enter_context(patch("mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit", lambda _l, _p, _a: []))
        if not real:
            stack.enter_context(patch("mcp_coder.utils.toolkit_runner.find_mcp_coder_table", _with_toolkit))
            stack.enter_context(patch("mcp_coder.utils.toolkit_runner._toolkit_class", lambda _name: PythonToolkit))
        yield
```

Keep the docstring's note on why `patch()` is used instead of `monkeypatch`, and
update it for the new patches and the marker. Imports needed: `ExitStack`
(from `contextlib`, already imported as a module) and `Any`.

Marker in `pyproject.toml`:
`"real_toolkit_config: opt out of the autouse toolkit-name and toolkit-registry patches (_resolvable_formatter)"`.

## DATA

`ToolkitConfig.source: str` — always the file name.

## Tests (write first; all marked `@pytest.mark.real_toolkit_config`)

- no table → `ValueError` containing both snippets, the `command` pointer and `_CONFIGURE_URL`
- bindings-only table → same error (not "Unknown key")
- bindings-only table with a `command` subtable → the no-key error, not "Unknown key 'command'"
- `verify` PROJECT section for a `tmp_path` without config → `[ERR]` Toolkit row
  with the message, `_print_project_section` returns False (and `execute_verify`
  exits 1 with `_print_project_section` unpatched or via its existing exit test pattern)
- `check_formatter_config(tmp_path)` (format pre-flight) reports the error
  (match the existing tests for its return shape)
- `llm_permissions(tmp_path, "claude")` → `[]` with a warning; `required_mcp_servers(tmp_path)`
  → `["mcp-workspace"]`
- `toolkit = "mcp-tools-py"` with `entry_points` patched to only `command` →
  `load_toolkit` error carries the `mcp-coder[python]` hint
