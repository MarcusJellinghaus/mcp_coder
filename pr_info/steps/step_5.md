# Step 5: Schema-driven verify_config rewrite

**Commit message:** `config: rewrite verify_config to walk schema`

> Read `pr_info/steps/summary.md` for full context. This is Step 5: rewrite `verify_config()` to use `_CONFIG_SCHEMA` instead of hand-coded per-section logic.

## Goal

Replace ~100 lines of repetitive per-section checks in `verify_config()` with a schema-driven loop.
Delete `_SECTION_ENV_VARS` and `_get_source_annotation()` — the schema provides all needed info.
Preserve the return format: `{"entries": [...], "has_error": bool}`.

## WHERE

`src/mcp_coder/utils/user_config.py` — rewrite `verify_config()`, delete `_SECTION_ENV_VARS`, delete `_get_source_annotation()`

## WHAT

### Delete
- `_SECTION_ENV_VARS` dict (lines ~340-348)
- `_get_source_annotation()` function (lines ~351-377)

### Rewrite `verify_config()`

Same signature, same return format. New implementation walks schema.

## ALGORITHM

```
def verify_config():
    entries = []
    # Step 1-3: File existence + TOML parse (unchanged)
    ...same as before...
    
    # Step 4: Walk schema sections
    for section_name, fields in _CONFIG_SCHEMA.items():
        if section_name == "coordinator.repos.*":
            # Handle wildcard: iterate actual repos in config_data
            _verify_wildcard_repos(config_data, fields, entries)
            continue
        
        section_data = _get_section_data(config_data, section_name)
        if section_data is None:
            entries.append({"label": f"[{section_name}]", "status": "info",
                           "value": "not configured"})
            continue
        
        _verify_section(section_name, section_data, fields, entries)
    
    return {"entries": entries, "has_error": False}
```

### Severity rules (from issue)

| Condition | Severity |
|---|---|
| Type mismatch (e.g. `"true"` instead of `true`) | **Error** |
| Missing mandatory field (in a present section) | **Error** |
| Unknown key in a section | **Warning** |
| Missing optional field (in a present section) | **Info** |
| Section entirely absent | **Info** (hint to configure) |
| Env var set (overrides config) | **OK** (shown alongside TOML status) |

### Helper: `_verify_section()`

```python
def _verify_section(
    section_name: str,
    section_data: dict[str, Any],
    fields: dict[str, FieldDef],
    entries: list[dict[str, str]],
) -> None:
```

```
for key, field_def in fields.items():
    env_value = os.environ.get(field_def.env_var) if field_def.env_var else None
    config_value = section_data.get(key)
    
    if env_value:
        source = "(env var, also in config.toml)" if config_value is not None else "(env var)"
        entries.append({"label": f"[{section_name}]", "status": "ok",
                       "value": f"{key} configured {source}"})
    elif config_value is not None:
        # Type check
        if not isinstance(config_value, field_def.field_type):
            entries.append({"label": f"[{section_name}]", "status": "error",
                           "value": f"{key}: expected {field_def.field_type.__name__}, "
                                    f"got {type(config_value).__name__} ('{config_value}')"})
        else:
            entries.append({"label": f"[{section_name}]", "status": "ok",
                           "value": f"{key} configured (config.toml)"})
    elif field_def.required:
        entries.append({"label": f"[{section_name}]", "status": "error",
                       "value": f"{key} is required but missing"})
    else:
        entries.append({"label": f"[{section_name}]", "status": "info",
                       "value": f"{key} not configured"})

# Check for unknown keys
for key in section_data:
    if key not in fields:
        entries.append({"label": f"[{section_name}]", "status": "warning",
                       "value": f"unknown key: {key}"})
```

### Helper: `_verify_wildcard_repos()`

```python
def _verify_wildcard_repos(
    config_data: dict[str, Any],
    fields: dict[str, FieldDef],
    entries: list[dict[str, str]],
) -> None:
```

```
repos = config_data.get("coordinator", {}).get("repos", {})
if not repos:
    entries.append({"label": "[coordinator.repos]", "status": "info",
                   "value": "no repositories configured"})
    return

entries.append({"label": "[coordinator]", "status": "ok",
               "value": f"{len(repos)} repos configured"})

for repo_name, repo_data in repos.items():
    section_name = f"coordinator.repos.{repo_name}"
    if isinstance(repo_data, dict):
        _verify_section(section_name, repo_data, fields, entries)
```

## DATA — return format (preserved)

```python
{
    "entries": [
        {"label": "[github]", "status": "ok", "value": "token configured (env var)"},
        {"label": "[jenkins]", "status": "ok", "value": "server_url configured (config.toml)"},
        {"label": "[mlflow]", "status": "info", "value": "not configured"},
        ...
    ],
    "has_error": False  # True only for TOML parse errors or type mismatches
}
```

**Note on `has_error`**: The issue says type mismatches are **Error** severity. If any type mismatch is found by verify, set `has_error = True`. Currently `has_error` is only True for invalid TOML. After this change, it's also True for type mismatches and missing required fields.

## Tests

`tests/utils/test_verify_config.py` — update existing + add new:

### Tests that need output format updates

The existing tests check for specific label/value patterns. The schema-driven output will be more granular (per-field instead of per-section summary). Update assertions to match new output format.

Key tests to update:
- `test_verify_config_valid_with_all_sections`: Update expected labels/values for schema-driven output
- `test_verify_config_env_var_only`: Check per-field env var reporting
- `test_verify_config_dual_source`: Check "(env var, also in config.toml)" format
- `test_verify_config_coordinator_repo_count`: Now walks individual repo fields
- `test_verify_config_mcp_*`: Now part of schema-driven loop

### New tests to add

```python
def test_verify_config_type_mismatch_reports_error(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """String in bool field -> error status with type context."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[mlflow]\nenabled = "true"\n', encoding="utf-8"
    )
    monkeypatch.setattr(...)
    self._clear_env_vars(monkeypatch)

    result = verify_config()

    assert result["has_error"] is True
    errors = [e for e in result["entries"] if e["status"] == "error"]
    assert any("expected bool" in e["value"] and "enabled" in e["value"] for e in errors)

def test_verify_config_missing_required_field(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Present section with missing required field -> error."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('[github]\n', encoding="utf-8")  # token missing
    monkeypatch.setattr(...)
    self._clear_env_vars(monkeypatch)

    result = verify_config()

    errors = [e for e in result["entries"] if e["status"] == "error"]
    assert any("token" in e["value"] and "required" in e["value"] for e in errors)

def test_verify_config_unknown_key_warns(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown key in known section -> warning."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[github]\ntoken = "ghp_test"\nunknown_key = "value"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(...)
    self._clear_env_vars(monkeypatch)

    result = verify_config()

    warnings = [e for e in result["entries"] if e["status"] == "warning"]
    assert any("unknown_key" in e["value"] for e in warnings)

def test_verify_config_absent_section_info(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Absent section -> info hint."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(...)
    self._clear_env_vars(monkeypatch)

    result = verify_config()

    info_entries = [e for e in result["entries"] if e["status"] == "info"]
    labels = [e["label"] for e in info_entries]
    assert "[github]" in labels or any("github" in e["value"] for e in info_entries)
```

## Checklist
- [ ] `_SECTION_ENV_VARS` deleted
- [ ] `_get_source_annotation()` deleted
- [ ] `verify_config()` walks `_CONFIG_SCHEMA`
- [ ] Severity levels match issue table
- [ ] `has_error` True for type mismatches and missing required fields
- [ ] Return format preserved (`entries` list + `has_error`)
- [ ] Wildcard repos handled
- [ ] All existing verify tests updated
- [ ] New tests for type mismatch, unknown key, missing required, absent section
- [ ] All checks pass (pylint, pytest, mypy)
