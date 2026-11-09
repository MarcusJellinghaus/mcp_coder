# Step 1 — Command toolkit config model

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 3, 4 (grants), 5
("malformed" definition) and 8 (problem list).

## LLM prompt

> Implement Step 1 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_1.md`: create the pure config parser
> `mcp_coder.toolkits.command.config` and its tests (TDD — tests first). No
> toolkit class, no registration yet. Run the code-quality checks from
> CLAUDE.md and make exactly one commit.

## WHERE

- Create `src/mcp_coder/toolkits/__init__.py` (docstring only: "Toolkits shipped
  with mcp-coder; reached only through the `mcp_coder.toolkits` entry points.").
- Create `src/mcp_coder/toolkits/command/__init__.py` (docstring only for now).
- Create `src/mcp_coder/toolkits/command/config.py`.
- Create `tests/toolkits/__init__.py`, `tests/toolkits/command/__init__.py`,
  `tests/toolkits/command/test_config.py`.
- `.importlinter`: add `tests.toolkits` to `test_module_independence`.
- `tach.toml`: add `{ path = "mcp_coder.toolkits" }` to the `tests` module's
  `depends_on`, and a module entry:
  ```toml
  [[modules]]
  path = "mcp_coder.toolkits"
  layer = "tools"
  # Toolkits shipped with mcp-coder (command). Reached by core only through the
  # mcp_coder.toolkits entry points; import only the utils shims.
  depends_on = [{ path = "mcp_coder.utils" }]
  ```

`config.py` imports only stdlib (`shlex`, `os`, `dataclasses`, `typing`, `collections.abc`).

## WHAT

```python
ACTIONS = ("format", "check", "test")
PARSERS = ("exit-code", "junit")
STATUSES = ("ok", "findings", "skipped", "error")
DEFAULT_EXIT_CODES: dict[int, str] = {0: "ok", 1: "findings"}
DEFAULT_TIMEOUT = 600

@dataclass(frozen=True)
class Step:
    argv: tuple[str, ...]
    name: str | None
    parser: str                 # "exit-code" | "junit"
    exit_codes: dict[int, str]  # step table replaces the default (no merge)
    timeout: int
    report: str | None          # project-relative, junit only
    grant: str | None           # "Bash(<argv joined by spaces>)" or None

    @property
    def label(self) -> str: ...  # name, else " ".join(argv)

@dataclass(frozen=True)
class Problem:
    scope: tuple[str, str] | None   # None = global; else (action, depth)
    status: Literal["error", "warning"]
    name: str                       # e.g. "command", "check.quick[2]"
    message: str

@dataclass(frozen=True)
class ParsedConfig:
    steps: dict[str, dict[str, list[Step]]]  # action -> depth -> well-formed steps, config order
    problems: list[Problem]

    def global_errors(self) -> list[Problem]: ...
    def errors_for(self, action: str, depth: str) -> list[Problem]: ...

def parse_config(config: Mapping[str, Any]) -> ParsedConfig: ...
```

## HOW

- Pure, never raises; no filesystem access (`argv[0]` lookup is done in
  `verify` / `run`, Steps 2 and 3).
- Every declared depth appears in `steps`, even when all its steps are
  malformed (empty list), so a request for it reaches `run`.

## ALGORITHM

```
defaults: validate llm_permissions/parser/exit_codes/timeout -> global error on bad value
for key in config: unknown top-level key (not defaults, not ACTIONS) -> global error
for action in ACTIONS present: non-table -> global error; else for depth, raw in table:
    steps[action][depth] = []; non-list -> scoped error
    for i, raw_step: step, errs = _parse_step(raw_step, defaults); errs -> scoped errors (+warnings)
    if no scoped error for that step: append step
grant = f"Bash({' '.join(argv)})" if llm_permissions == "bash" and all(_safe(a)) else None
```

Rules for `_parse_step` (errors are `error` status, scoped to `(action, depth)`):
- not a table; unknown key (allowed: `argv`, `name`, `parser`, `exit_codes`, `timeout`, `report`);
- `argv` missing, not a list (a string is an error), empty, or non-string elements;
- `name` not a string; bad `parser`; bad `exit_codes` (not a table, key not
  `int(key)`-parsable, value not in `STATUSES`); `timeout` not a positive `int`
  (reject `bool`);
- effective parser `junit` without `report`; `report` with a non-`junit` parser;
- `report` absolute, or `os.path.normpath(report)` starting with `..` (outside `project_dir`).
- `_safe(a)`: `shlex.quote(a) == a and "," not in a`. Under `"bash"` an unsafe
  element is a `warning` Problem ("runs without a grant") — the step is still
  well-formed, `grant=None`.
- Under an invalid `llm_permissions` value: global error and no grants at all.

## DATA

`parse_config({...})` → `ParsedConfig(steps=..., problems=[...])`. Problem
messages name the key/value, e.g.
`"check.quick[1]: unknown key 'cmd'"`, `"timeout must be a positive integer, got 0"`.

## Tests (`tests/toolkits/command/test_config.py`)

- Defaults applied; step overrides; step `exit_codes` replaces the default table.
- `exit_codes` string keys → `int`; non-numeric key and bad value → errors.
- Unknown top-level key, unknown action key (e.g. `lint`), unknown step key → errors.
- `timeout` `0`, `-1`, `1.5`, `True` → errors; bad default → global error.
- `argv` as string, empty, missing → scoped error; that step is not in `steps`
  but its depth is declared.
- `junit` without `report`; `report` without `junit`; `report = "../x.xml"` and absolute → errors.
- Grants: `["npm", "run", "lint"]` → `"Bash(npm run lint)"`; element with a space,
  a `,` or `C:\\x` → warning, `grant is None`; `llm_permissions = "none"` → all
  `None`; `llm_permissions = "yes"` → global error, all `None`.
- Config order of depths and steps preserved.
