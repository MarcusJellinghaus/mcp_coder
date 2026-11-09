# Step 2 — LangChain config loader uses the shared resolver

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Step 1 (`mcp_coder.utils.env_placeholders.resolve_placeholders`) is already done.
> Use TDD: adjust the tests in `tests/llm/providers/langchain/test_langchain_agent.py` first, then `_mcp_tools.py`.
> Run pylint, pytest (fast unit set, `-n auto`), mypy, lint-imports and tach. All must pass.
> Run the formatter, then make exactly one commit.

## Precondition

`_resolve_env_vars` must be referenced only from `_mcp_tools.py` and `tests/llm/providers/langchain/test_langchain_agent.py`. Check with `mcp__mcp-tools-py__find_references`.

If anything else references it, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/llm/providers/langchain/_mcp_tools.py`
- `tests/llm/providers/langchain/test_langchain_agent.py`

## WHAT

- Delete `_resolve_env_vars(value, env)`.
- In `_load_mcp_server_config(mcp_config_path, env_vars=None)` (signature unchanged):
  - delete `merged_env = {**os.environ, **(env_vars or {})}`;
  - resolve `command`, the string items of `args`, and the string values of `env` via `resolve_placeholders(value, env_vars)[0]`.
- Remove the `os` / `re` imports if they become unused (ruff and pylint will tell).
- Update the module docstring and the `env_vars` docstring line if they mention the old merge.

## HOW

```python
from ....utils.env_placeholders import resolve_placeholders
```

Match the relative-import depth used elsewhere in the module, or use the absolute `mcp_coder.utils.env_placeholders` import.

Optional local helper inside the function, to keep lines short:

```python
def _resolve(text: str) -> str:
    return resolve_placeholders(text, env_vars)[0]
```

## ALGORITHM

```
for key, value in server_cfg.items():
    command (str)  -> _resolve(value)
    args (list)    -> [_resolve(i) if isinstance(i, str) else i for i in value]
    env (dict)     -> {k: _resolve(v) if isinstance(v, str) else v for k, v in value.items()}
    (other branches unchanged)
```

## DATA

The return shape is unchanged: `dict[str, dict[str, object]]`.

## Tests

- Remove the `TestResolveEnvVars` class and the `_resolve_env_vars` import. Step 1 covers those cases in `tests/utils/test_env_placeholders.py`.
- Keep `test_loads_and_resolves_config` and `test_env_vars_override_os_environ` passing unchanged.
- Add to `TestLoadMcpServerConfig`:
  - `test_default_syntax_resolves`: with `monkeypatch.delenv("MCPC_TEST_UNSET", raising=False)`, `"env": {"X": "${MCPC_TEST_UNSET:-fallback}"}` → `"fallback"`.
