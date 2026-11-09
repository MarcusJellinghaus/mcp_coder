# Step 1 — Shared placeholder resolver `mcp_coder.utils.env_placeholders`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Use TDD: write `tests/utils/test_env_placeholders.py` first, then the module.
> Do not touch any other module in this step.
> Run pylint, pytest (fast unit set, `-n auto`), mypy, lint-imports and tach. All must pass.
> Run the formatter, then make exactly one commit.

## WHERE

- New: `src/mcp_coder/utils/env_placeholders.py`
- New: `tests/utils/test_env_placeholders.py`

## WHAT

```python
def resolve_placeholders(
    value: str,
    env_vars: Mapping[str, str] | None = None,
    *,
    case_insensitive: bool | None = None,
) -> tuple[str, list[str]]:
    """Expand ``${VAR}`` / ``${VAR:-default}`` like Claude Code does in ``.mcp.json``."""
```

- Module docstring: state the semantics (below) and that verify and LangChain share this resolver.
- `case_insensitive=None` means "use the platform default", i.e. `os.name == "nt"`.

## ALGORITHM

```
ci = (os.name == "nt") if case_insensitive is None else case_insensitive
extra = {k.upper(): v for k, v in (env_vars or {}).items()} if ci else dict(env_vars or {})
unresolved = []
on each match of r"\$\{([^}]+?)(?::-([^}]*))?\}"  (single re.sub pass):
    name, default = groups; key = name.upper() if ci else name
    if key in extra -> extra[key]; elif name in os.environ -> os.environ[name]
    elif default is not None -> default; else: add name to unresolved (no duplicates) -> match text
return (result, unresolved)
```

- `os.environ` is looked up directly. It is already case-insensitive on Windows, so it is never upper-case copied.
- The lazy `[^}]+?` keeps the old behaviour of matching every `${...}`. A malformed name such as `${A:B}` is reported as unresolved.

## DATA

- Returns `(resolved_value, unresolved_names)`.
- `unresolved_names` keeps first-seen order with no duplicates, e.g. `("x/${A}", ["A"])`.

## Tests (`tests/utils/test_env_placeholders.py`)

Use `monkeypatch.setenv` / `monkeypatch.delenv(..., raising=False)` with unlikely names (e.g. `MCPC_TEST_PH_*`).

- `${VAR}` resolved from `env_vars`; resolved from `os.environ`.
- Multiple placeholders in one value; empty string and plain text are unchanged. These replace the old `TestResolveEnvVars` cases: single var, multiple vars, unknown var preserved, empty string, no placeholders.
- `env_vars` wins over `os.environ`.
- `${VAR:-default}`:
  - VAR unset → `default`;
  - VAR set → its value;
  - VAR set to `""` → `""`.
- A default containing `${X}` stays literal, e.g. `${UNSET:-${X}}`. Single pass means no expansion and `X` is not reported.
  - Pin the actual result string the regex produces in the test. If it differs from intuition, keep the regex and assert what it does.
- Unresolved `${UNSET}` stays literal and is returned in the list; duplicates appear once.
- `case_insensitive=True`: `env_vars={"MCPC_TEST_PH_CI": "1"}` resolves `${mcpc_test_ph_ci}` (runs on every OS).
- `case_insensitive=False`: `${mcpc_test_ph_ci}` with `env_vars={"MCPC_TEST_PH_CI": "1"}` is unresolved (`monkeypatch.delenv("MCPC_TEST_PH_CI", raising=False)` first, since `os.environ` stays case-insensitive on Windows).
- `@pytest.mark.skipif(os.name != "nt")`: `monkeypatch.setenv("MCPC_TEST_PH_CASE", "x")` resolves `${Mcpc_Test_Ph_Case}` with default arguments.
