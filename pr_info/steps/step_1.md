# Step 1: Define config schema with FieldDef dataclass

**Commit message:** `config: add FieldDef dataclass and _CONFIG_SCHEMA`

> Read `pr_info/steps/summary.md` for full context. This is Step 1: purely additive schema definition.

## Goal

Add the schema data structure that will drive validation and env var lookup in later steps.
Nothing references it yet — no behavior changes, no callers break.

## WHERE

`src/mcp_coder/utils/user_config.py` — add near top (after imports, before existing functions)

## WHAT

```python
@dataclass(frozen=True, slots=True)
class FieldDef:
    """Schema definition for a single config field."""
    field_type: type  # str, bool, int, list
    required: bool = False
    env_var: str | None = None
```

```python
_CONFIG_SCHEMA: dict[str, dict[str, FieldDef]] = { ... }
```

```python
def _get_field_def(section: str, key: str) -> FieldDef | None:
    """Look up field definition from schema, supporting wildcard sections."""
```

## HOW

- Import `dataclass` from `dataclasses`
- `_CONFIG_SCHEMA` is a module-level constant dict
- `_get_field_def()` first tries exact section match, then checks `coordinator.repos.*` wildcard by matching any section starting with `coordinator.repos.`

## ALGORITHM — `_get_field_def`

```
def _get_field_def(section, key):
    if section in _CONFIG_SCHEMA and key in _CONFIG_SCHEMA[section]:
        return _CONFIG_SCHEMA[section][key]
    if section.startswith("coordinator.repos.") and section.count(".") == 2:
        wildcard = _CONFIG_SCHEMA.get("coordinator.repos.*", {})
        return wildcard.get(key)
    return None
```

## DATA — `_CONFIG_SCHEMA`

```python
_CONFIG_SCHEMA: dict[str, dict[str, FieldDef]] = {
    "github": {
        "token": FieldDef(str, required=True, env_var="GITHUB_TOKEN"),
        "test_repo_url": FieldDef(str, env_var="GITHUB_TEST_REPO_URL"),
    },
    "jenkins": {
        "server_url": FieldDef(str, required=True, env_var="JENKINS_URL"),
        "username": FieldDef(str, required=True, env_var="JENKINS_USER"),
        "api_token": FieldDef(str, required=True, env_var="JENKINS_TOKEN"),
        "test_job": FieldDef(str),
        "test_job_coordination": FieldDef(str),
    },
    "mcp": {
        "default_config_path": FieldDef(str, env_var="MCP_CODER_MCP_CONFIG"),
    },
    "llm": {
        "default_provider": FieldDef(str),
    },
    "llm.langchain": {
        "backend": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_BACKEND"),
        "model": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_MODEL"),
        "api_key": FieldDef(str),
        "endpoint": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_ENDPOINT"),
        "api_version": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_API_VERSION"),
    },
    "coordinator": {
        "cache_refresh_minutes": FieldDef(int),
    },
    "coordinator.repos.*": {
        "repo_url": FieldDef(str, required=True),
        "executor_job_path": FieldDef(str, required=True),
        "github_credentials_id": FieldDef(str, required=True),
        "executor_os": FieldDef(str),
        "update_issue_labels": FieldDef(bool),
        "post_issue_comments": FieldDef(bool),
        "setup_commands_windows": FieldDef(list),
        "setup_commands_linux": FieldDef(list),
    },
    "vscodeclaude": {
        "workspace_base": FieldDef(str, required=True),
        "max_sessions": FieldDef(int),
    },
    "mlflow": {
        "enabled": FieldDef(bool),
        "tracking_uri": FieldDef(str, env_var="MLFLOW_TRACKING_URI"),
        "experiment_name": FieldDef(str, env_var="MLFLOW_EXPERIMENT_NAME"),
        "artifact_location": FieldDef(str, env_var="MLFLOW_DEFAULT_ARTIFACT_ROOT"),
    },
}
```

## Tests

`tests/utils/test_user_config.py` — add new test class:

```python
class TestConfigSchema:
    """Tests for FieldDef and _CONFIG_SCHEMA."""

    def test_field_def_creation(self) -> None:
        """FieldDef stores type, required, and env_var."""
        f = FieldDef(str, required=True, env_var="MY_VAR")
        assert f.field_type is str
        assert f.required is True
        assert f.env_var == "MY_VAR"

    def test_field_def_defaults(self) -> None:
        """FieldDef defaults: required=False, env_var=None."""
        f = FieldDef(bool)
        assert f.required is False
        assert f.env_var is None

    def test_schema_has_all_known_sections(self) -> None:
        """Schema contains all expected top-level sections."""
        expected = {"github", "jenkins", "mcp", "llm", "llm.langchain",
                    "coordinator", "coordinator.repos.*", "vscodeclaude", "mlflow"}
        assert set(_CONFIG_SCHEMA.keys()) == expected

    def test_schema_github_token_env_var(self) -> None:
        """github.token maps to GITHUB_TOKEN."""
        assert _CONFIG_SCHEMA["github"]["token"].env_var == "GITHUB_TOKEN"

    def test_schema_langchain_env_vars(self) -> None:
        """llm.langchain fields have correct env var mappings."""
        lc = _CONFIG_SCHEMA["llm.langchain"]
        assert lc["backend"].env_var == "MCP_CODER_LLM_LANGCHAIN_BACKEND"
        assert lc["model"].env_var == "MCP_CODER_LLM_LANGCHAIN_MODEL"
        assert lc["endpoint"].env_var == "MCP_CODER_LLM_LANGCHAIN_ENDPOINT"
        assert lc["api_version"].env_var == "MCP_CODER_LLM_LANGCHAIN_API_VERSION"

    def test_get_field_def_exact_match(self) -> None:
        """_get_field_def returns FieldDef for exact section match."""
        result = _get_field_def("github", "token")
        assert result is not None
        assert result.env_var == "GITHUB_TOKEN"

    def test_get_field_def_wildcard_match(self) -> None:
        """_get_field_def matches coordinator.repos.* sections."""
        result = _get_field_def("coordinator.repos.mcp_coder", "repo_url")
        assert result is not None
        assert result.required is True

    def test_get_field_def_unknown_returns_none(self) -> None:
        """_get_field_def returns None for unknown section/key."""
        assert _get_field_def("unknown", "key") is None
        assert _get_field_def("github", "unknown_key") is None

    def test_field_def_is_frozen(self) -> None:
        """FieldDef instances are immutable."""
        f = FieldDef(str)
        with pytest.raises(AttributeError):
            f.required = True  # type: ignore[misc]
```

## Checklist
- [ ] `FieldDef` dataclass added with `frozen=True, slots=True`
- [ ] `_CONFIG_SCHEMA` covers all sections from the issue
- [ ] `_get_field_def()` handles exact and wildcard matches
- [ ] All tests pass (pylint, pytest, mypy)
- [ ] No existing behavior changed
