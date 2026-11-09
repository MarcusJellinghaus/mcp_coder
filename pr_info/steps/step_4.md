# Step 4 — Verify: warn only on unresolved `env` placeholders

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`.
> Step 1 (`mcp_coder.utils.env_placeholders.resolve_placeholders`) is already done.
> Use TDD: rewrite the placeholder tests in `tests/cli/commands/test_verify_mcp_orchestration.py` first, then change `verify_sections.py` and `verify.py`.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy. All must pass.
> Run the formatter, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py` — `_validate_mcp_config`
- `src/mcp_coder/cli/commands/verify.py` — the single call site (around line 357)
- `tests/cli/commands/test_verify_mcp_orchestration.py`

## WHAT

```python
def _validate_mcp_config(
    mcp_json_path: str,
    env_vars: dict[str, str] | None = None,
) -> tuple[bool | None, str, list[tuple[str, str]]]:
```

- The `env_vars` argument stays optional: other tests mock this function without checking arguments.
- Update the docstring:
  - document `env_vars`;
  - `warnings` holds `(f"{server} / {env_var}", "${A}, ${B} not set")` for placeholders unresolved via `os.environ` and `env_vars`;
  - a `${VAR:-default}` counts as resolved.
- In `verify.py`: `_validate_mcp_config(mcp_config_resolved, env_vars=env_vars)`. `env_vars` is already computed just above.
- Remove the `re` import from `verify_sections.py` if it becomes unused.

## HOW

```python
from ...utils.env_placeholders import resolve_placeholders
```

Use the same relative style as the other `verify_sections.py` imports.

## ALGORITHM

```
warnings = []
for name, srv in servers.items():
    env = srv.get("env") if isinstance(srv, dict) else None
    if not isinstance(env, dict): continue          # wrong shape: not this check's job
    for var, val in env.items():
        if isinstance(val, str) and (missing := resolve_placeholders(val, env_vars)[1]):
            warnings.append((f"{name} / {var}", ", ".join(f"${{{m}}}" for m in missing) + " not set"))
```

## DATA

The return tuple is unchanged; only the text of the warning values changes, e.g. `("srv / PYTHONPATH", "${MCPC_TEST_A} not set")`.

## Tests

Every "unresolved" test must call `monkeypatch.delenv(name, raising=False)` or use an unlikely name. `MCP_CODER_*` variables are often set in the dev environment.

Rewrite in `TestMcpConfigWarnings`:

- `test_unresolved_placeholder_found` → value `"${MCPC_TEST_A}/src"` gives `("srv / PYTHONPATH", "${MCPC_TEST_A} not set")`.
- `test_no_placeholders_returns_no_warnings` → keep as is: plain values, no warnings.
- `test_multiple_servers_multiple_vars` → several servers and vars, all unresolved. One row per env var; a value with two placeholders yields `"${MCPC_TEST_A}, ${MCPC_TEST_B} not set"`.
- New `test_placeholder_resolved_via_env_vars` → `env_vars={"MCPC_TEST_A": "x"}` gives no warning.
- New `test_placeholder_resolved_via_os_environ` → `monkeypatch.setenv` gives no warning.
- New `test_default_syntax_counts_as_resolved` → `${MCPC_TEST_A:-d}` with A unset gives no warning.
- New `test_non_dict_env_skipped` → `"env": ["x"]` gives `ok=True` and no warnings, with no exception.

Update:

- `test_section_rendered_when_findings`:
  - it mocks `prepare_llm_environment` as `{}`, so add `monkeypatch.delenv` for its placeholder variable;
  - assert the rendered text `"${...} not set"` instead of the raw value.
- `TestMcpConfigWarningsDynamicWidth::test_long_label_widens_section_value_column`:
  - add `monkeypatch.delenv("VAR_A", raising=False)` / `("VAR_B", ...)`;
  - its `index("${VAR_A}")` lookup still works because the warning starts with the placeholder.
- `test_log_filter_suppresses_unexpanded_warning` and any other test that relies on warnings appearing: make sure its placeholder variable is unset via `monkeypatch.delenv`.
