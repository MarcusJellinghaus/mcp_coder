# Step 2: Toolkit registry and runner

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **step 2** as described in
> `pr_info/steps/step_2.md`. Step 1 (`load_toolkit_config`) is done. Write the tests
> first, then the code. Nothing in the workflows calls it yet. Run pylint, mypy, pytest
> (fast unit tests), lint-imports and format, then make exactly one commit.

## Precondition

The installed mcp-tools-py must register `mcp-tools-py` under the
`mcp_coder.toolkits` entry-point group and provide `mcp_tools_py.toolkit.PythonToolkit`
with a `test` depth `unattended` (probe with a scratch test using
`importlib.metadata.entry_points(group="mcp_coder.toolkits")`). If it does not, write one
line to `pr_info/.blocked.txt` saying the installed mcp-tools-py is stale, and stop.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py` (add runner part)
- New `tests/utils/test_toolkit_runner.py`

## WHAT

```python
_STANDARD_DEPTHS = ("quick", "standard", "full")

@dataclass(frozen=True)
class LoadedToolkit:
    name: str
    toolkit: Toolkit
    info: ToolkitInfo
    config: ToolkitConfig

def _toolkit_class(name: str) -> type[Toolkit]            # raises ValueError
def load_toolkit(project_dir: Path) -> LoadedToolkit       # raises ValueError
def _request_params(loaded: LoadedToolkit, action: str, depth: str) -> dict[str, Any]
def _resolve_depth(declared: list[str], depth: str) -> str | None
def run_request(loaded: LoadedToolkit, project_dir: Path, request: str) -> ActionResult
def run_binding(loaded: LoadedToolkit, project_dir: Path, entry: str) -> list[tuple[str, ActionResult]]
def verify_toolkit(loaded: LoadedToolkit, project_dir: Path, action: str | None) -> list[VerifyItem]
def get_fragment(loaded: LoadedToolkit, name: str) -> str
```

(`project_dir` is passed explicitly; `LoadedToolkit` stays a pure description.)

## ALGORITHM

`load_toolkit`:
```
config = load_toolkit_config(project_dir)
cls = _toolkit_class(config.toolkit)    # entry_points(group="mcp_coder.toolkits"); unknown → ValueError listing registered names; ep.load() errors → ValueError
try: toolkit = cls(config.section); info = toolkit.describe()
except Exception as exc: raise ValueError(f"Toolkit '{name}' failed to load: {exc}") from exc
for action in config.params: action not in info.actions → ValueError
    for depth in info.actions[action]: validate_params(info.params_schema, _request_params(...))  # ValueError propagates
return LoadedToolkit(config.toolkit, toolkit, info, config)
```

`_request_params`: `base = {k: v for k, v in params.get(action, {}).items() if k not in info.actions[action]}`;
return `base | params[action].get(depth, {})` (depth table overrides action table).

`_resolve_depth`: declared → itself; not in `_STANDARD_DEPTHS` → `None`; else walk the
lower standard depths downward and return the first declared one; none → `None`.

`run_request`:
```
action, depth = request.split("@")
declared = loaded.info.actions.get(action); resolved = _resolve_depth(declared, depth) if declared else None
if resolved is None: return ActionResult("error", f"{request}: not declared by toolkit '{name}'")
if resolved != depth: logger.info("%s: depth %s not declared, running %s", ...)
try: return loaded.toolkit.run(ActionRequest(action, resolved, project_dir, _request_params(...)))
except Exception as exc: return ActionResult("error", f"{request} raised: {exc}")
```

`run_binding`: `[(r, run_request(loaded, project_dir, r)) for r in loaded.config.bindings[entry]]`.

`verify_toolkit`: `try: return list(loaded.toolkit.verify(project_dir, action))`
`except Exception as exc: raise ValueError(f"Toolkit '{name}' verify failed: {exc}") from exc`.

`get_fragment`: `prompt_fragments().get(name, "")`; an exception is logged as a warning
and returns `""`.

## DATA

- `run_binding` → list of `(request_string, ActionResult)` in binding order; never raises
  for toolkit failures.
- `load_toolkit` / `verify_toolkit` raise `ValueError` for every config or toolkit-load
  problem (unregistered toolkit, constructor/`describe()`/`verify()` exceptions, bad
  params, params for an undeclared action).

## HOW

- Imports: `from importlib.metadata import entry_points`; contract names from
  `.toolkit` (the shim) only.
- Tests replace the registry by monkeypatching `toolkit_runner._toolkit_class`
  (returns a fake `Toolkit` subclass), never by asserting on installed metadata.

## Tests (`tests/utils/test_toolkit_runner.py`, write first)

Fake toolkit: subclass of the shim's `Toolkit` with configurable `actions`, a
configurable closed `params_schema` (`ToolkitInfo` rejects any schema that is not
`"type": "object"` with `"additionalProperties": false`), and a `run` that records
requests and returns a canned result.

- `load_toolkit`: constructor receives `config.section`; unregistered name → `ValueError`
  naming it (patch `entry_points` to return nothing); constructor raising, `describe()`
  raising → `ValueError`; params for an undeclared action → `ValueError`; params that fail
  the schema → `ValueError`; params declared by the schema reach `ActionRequest.params`
  (fake schema `{"type": "object", "properties": {"markers": {"type": "string"},
  "verbose": {"type": "boolean"}}, "additionalProperties": False}`; config
  `params.test = {markers = "a", verbose = true}`, `params.test.quick = {markers = "b"}` →
  `test@quick` receives `{"markers": "b", "verbose": True}`, the depth table overriding
  the action table).
- `_resolve_depth` (parametrized): declared; `standard` → `quick` when only `quick`;
  `full` → `standard`; `quick` undeclared → `None`; `unattended`/`apply`/`mutation`
  undeclared → `None`.
- `run_request`: fallback logs a line; undeclared action → `error`; `run` raising → `error`
  with the message.
- `run_binding`: order and request strings preserved; empty binding → `[]`.
- `verify_toolkit`: passes `action`; `verify` raising → `ValueError`.
- `get_fragment`: present, absent → `""`, raising → `""`.
- Real toolkit: `PythonToolkit()` constructed directly (no entry-point lookup) and wrapped
  in a `LoadedToolkit`; `run_request(..., "test@unattended")` on a tmp project with one
  passing and one failing test in `tests/test_fail.py` (`PythonToolkit` collects from
  `testpaths`, default `tests`) returns `findings` whose single `Finding.key` is
  `tests/test_fail.py::test_fail`. Keep it to one small project so it runs in seconds.
