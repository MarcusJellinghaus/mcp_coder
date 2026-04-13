# Config Schema & Native Type Validation — Summary

**Issue:** #785 — config: harden type parsing with centralized schema and config validation

## Problem

`_get_nested_value()` in `user_config.py` converts all TOML values to `str` via `str(value)`.
This forces callers to do fragile string comparisons:

- `cli/utils.py:92-93` and `coordinator/core.py:78-79`: `== "True"` (breaks for TOML string `"true"`)
- `mlflow_config_loader.py:53-55`: `.lower() in ("true", "1", "yes", ...)` — dead code once schema enforces `bool`
- `vscodeclaude/config.py:88`: `int(max_sessions_str)` — unnecessary if native `int` flows through
- `vscodeclaude/config.py:117-128`: `json.loads()` on setup_commands — unnecessary if native `list` flows through
- `langchain/__init__.py:132-141`: manual env var override loop — duplicates what `get_config_values` should do

## Solution

Four steps, each one commit:

1. **Schema definition** — `FieldDef` dataclass + `_CONFIG_SCHEMA` dict in `user_config.py`
2. **Native types + bool callers** — Remove `str()` coercion, add type checking, update bool-field callers + tests
3. **Callers: int/list/langchain** — Update `vscodeclaude/config.py`, `langchain/__init__.py`, type annotations + tests
4. **Schema-driven `verify_config()`** — Walk schema instead of hand-coding each section, delete `_get_standard_env_var`, `_SECTION_ENV_VARS`, `_get_source_annotation`

## Architectural / Design Changes

### Before
- `_get_nested_value()` returns `str | None` — all TOML types flattened to strings
- `_get_standard_env_var()` — standalone function mapping `(section, key)` → env var name
- `_SECTION_ENV_VARS` — separate dict for verify_config's env var lookups
- Each caller manually parses types: `== "True"`, `int()`, `json.loads()`, `.lower()`
- `verify_config()` — hand-coded per-section logic (~100 lines of repetitive checks)
- `langchain/__init__.py` — manual env var override loop duplicating get_config_values logic

### After
- `_get_nested_value()` returns `Any` (native TOML types pass through)
- `_CONFIG_SCHEMA` — single `dict[str, dict[str, FieldDef]]` is the source of truth for:
  - Field types (`str`, `bool`, `int`, `list`)
  - Required/optional status
  - Environment variable mappings
- `_get_standard_env_var()` and `_SECTION_ENV_VARS` deleted — schema replaces both
- Callers use native types directly: `is True`, direct `int`, direct `list`
- `verify_config()` — schema-driven loop, automatically covers all sections
- `langchain/__init__.py` — env var mappings in schema, manual loop removed
- Type mismatches (e.g. `"true"` in a bool field) raise `ValueError` at load time

### Design Decisions
- **No `SectionDef` wrapper** — plain nested `dict[str, dict[str, FieldDef]]` is sufficient
- **Wildcard sections** — `coordinator.repos.*` matched by prefix in a helper function
- **Env vars bypass validation** — env vars are always strings, callers parse them
- **Strict over permissive** — string in boolean field raises `ValueError`, not silent coercion

## Files Modified

### Source files
| File | Change |
|------|--------|
| `src/mcp_coder/utils/user_config.py` | Add `FieldDef`, `_CONFIG_SCHEMA`; modify `_get_nested_value`, `get_config_values`, `verify_config`; delete `_get_standard_env_var`, `_SECTION_ENV_VARS`, `_get_source_annotation`; update `get_cache_refresh_minutes` |
| `src/mcp_coder/cli/utils.py` | `== "True"` → `is True` (lines 92-93) |
| `src/mcp_coder/cli/commands/coordinator/core.py` | `== "True"` → `is True` (lines 78-79) |
| `src/mcp_coder/utils/mlflow_config_loader.py` | Delete flexible string parsing, use `is True` |
| `src/mcp_coder/workflows/vscodeclaude/config.py` | Handle native `int` and `list` types |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Remove manual env var override loop |
| `src/mcp_coder/utils/jenkins_operations/client.py` | Update type annotation (line 91) |
| `src/mcp_coder/utils/github_operations/base_manager.py` | Update type annotation (line 169) |

### Test files (~11 test files)
| File | Change |
|------|--------|
| `tests/utils/test_user_config.py` | Update `test_converts_non_string_to_string` → test native types; add schema validation tests; update `get_cache_refresh_minutes` tests |
| `tests/utils/test_verify_config.py` | Update for schema-driven verify output; add type mismatch / unknown key / missing field tests |
| `tests/cli/test_utils.py` | Mock returns: `"True"` → `True`, `"False"` → `False` |
| `tests/cli/commands/coordinator/test_core.py` | Mock returns: `"True"` → `True` |
| `tests/integration/test_mlflow_integration.py` | Mock returns: `"true"` → `True` |
| `tests/config/test_mlflow_config.py` | Replace string-variant bool tests with native bool tests |
| `tests/workflows/vscodeclaude/test_config.py` | Mock returns: `"5"` → `5`, JSON strings → native lists |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Remove/update env var override tests |
| Other test files mocking `get_config_values` | Update string → native type mock returns |

### No new files created
All changes are modifications to existing files.

## Implementation Steps

| Step | Commit | Description |
|------|--------|-------------|
| 1 | Schema definition | Add `FieldDef` + `_CONFIG_SCHEMA` + `_get_field_def()` helper. Purely additive. |
| 2 | Native types + bool callers | Remove `str()` in `_get_nested_value`, add validation, update bool-field callers + tests |
| 3 | Callers: int/list/langchain | Update `vscodeclaude/config.py`, `langchain/__init__.py`, type annotations + tests |
| 4 | Schema-driven verify | Rewrite `verify_config()` to walk schema + delete `_get_standard_env_var`, `_SECTION_ENV_VARS`, `_get_source_annotation` + update verify tests |
