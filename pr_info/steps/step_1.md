# Step 1: Dependencies + Agent Utilities

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> This step adds the new dependencies and creates the agent module's utility functions.

## LLM Prompt

```
Implement Step 1 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: add dependencies to pyproject.toml and create the agent module with
utility functions for environment variable substitution and MCP config loading.
Follow TDD — write tests first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `pyproject.toml` — add two packages to `[langchain]` extras
- `tests/llm/providers/langchain/conftest.py` — add mock modules for new deps

### Files to create
- `src/mcp_coder/llm/providers/langchain/agent.py` — agent utilities (this step: constants + helpers only)
- `tests/llm/providers/langchain/test_langchain_agent.py` — tests for utilities

## WHAT

### pyproject.toml changes

Add to existing `langchain` extras group:
```toml
langchain = [
    "langchain-core>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-google-genai>=2.0.0",
    "langchain-anthropic>=0.3.0",
    "langchain-mcp-adapters>=0.1.0",   # NEW
    "langgraph>=0.2.0",                 # NEW
]
```

### pyproject.toml mypy overrides

Add mypy ignore for new packages:
```toml
[[tool.mypy.overrides]]
module = ["langchain_mcp_adapters", "langchain_mcp_adapters.*"]
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = ["langgraph", "langgraph.*"]
ignore_missing_imports = true
```

### agent.py — constants and utility functions

```python
AGENT_MAX_STEPS: int = 50

def _resolve_env_vars(value: str, env: dict[str, str]) -> str
    """Replace ${VAR} placeholders in a string with values from env dict."""

def _load_mcp_server_config(
    mcp_config_path: str,
    execution_dir: str | None,
    env_vars: dict[str, str] | None,
) -> dict[str, dict[str, object]]
    """Load .mcp.json and resolve env var placeholders.
    Returns dict suitable for MultiServerMCPClient."""
```

### conftest.py changes

Add `langchain_mcp_adapters` and `langgraph` to the mock injection block.

## HOW

### `_resolve_env_vars` — integration points
- Pure function, no imports needed
- Uses `re.sub` or simple string replacement for `${VAR}` patterns
- Env dict comes from caller (merged `os.environ` + `env_vars` parameter)

### `_load_mcp_server_config` — integration points
- Reads `.mcp.json` via `json.load()`
- Resolves path relative to `execution_dir` (or cwd if None)
- Walks all string values in the config dict and applies `_resolve_env_vars`
- Returns dict in format expected by `MultiServerMCPClient`:
  ```python
  {
      "server-name": {
          "command": "resolved/path",
          "args": ["--flag", "resolved_value"],
          "env": {"KEY": "resolved_value"},
          "transport": "stdio",
      }
  }
  ```

## ALGORITHM

### `_resolve_env_vars`
```
pattern = r'\$\{([^}]+)\}'
for each match in value:
    var_name = match.group(1)
    replacement = env.get(var_name, match.group(0))  # keep original if not found
    value = value.replace(match, replacement)
return value
```

### `_load_mcp_server_config`
```
config_path = resolve mcp_config_path relative to execution_dir
config = json.load(config_path)
env = merge os.environ + env_vars (env_vars wins)
for server_name, server_config in config["mcpServers"].items():
    recursively resolve all string values via _resolve_env_vars(value, env)
    set transport = "stdio"
return resolved config
```

## DATA

### `_resolve_env_vars` return
- `str` — the input string with `${VAR}` placeholders replaced

### `_load_mcp_server_config` return
```python
{
    "server-name": {
        "command": "/absolute/path/to/executable",
        "args": ["--project-dir", "/resolved/path"],
        "env": {"PYTHONPATH": "/resolved/path/"},
        "transport": "stdio",
    }
}
```

## TEST CASES

### `test_langchain_agent.py`

```python
class TestResolveEnvVars:
    def test_replaces_single_var(self)
    def test_replaces_multiple_vars(self)
    def test_preserves_unknown_vars(self)
    def test_empty_string_unchanged(self)
    def test_no_placeholders_unchanged(self)

class TestLoadMcpServerConfig:
    def test_loads_and_resolves_config(self, tmp_path)
    def test_resolves_relative_to_execution_dir(self, tmp_path)
    def test_env_vars_override_os_environ(self, tmp_path, monkeypatch)
    def test_raises_on_missing_file(self)
    def test_sets_stdio_transport(self, tmp_path)
```
