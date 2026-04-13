# Step 3: Update bool-field callers (cli/utils, coordinator/core, mlflow)

**Commit message:** `config: update bool-field callers to use native types`

> Read `pr_info/steps/summary.md` for full context. This is Step 3: update callers that compare boolean config values as strings.

## Goal

Replace `== "True"` string comparisons and flexible string parsing with native `bool` checks.

## WHERE + WHAT

### 1. `src/mcp_coder/cli/utils.py` (lines 92-93)

**Before:**
```python
cfg_labels = config[(section, "update_issue_labels")] == "True"
cfg_comments = config[(section, "post_issue_comments")] == "True"
```

**After:**
```python
cfg_labels = config[(section, "update_issue_labels")] is True
cfg_comments = config[(section, "post_issue_comments")] is True
```

### 2. `src/mcp_coder/cli/commands/coordinator/core.py` (lines 78-79)

**Before:**
```python
"update_issue_labels": config[(section, "update_issue_labels")] == "True",
"post_issue_comments": config[(section, "post_issue_comments")] == "True",
```

**After:**
```python
"update_issue_labels": config[(section, "update_issue_labels")] is True,
"post_issue_comments": config[(section, "post_issue_comments")] is True,
```

### 3. `src/mcp_coder/utils/mlflow_config_loader.py` (lines 51-55)

**Before:**
```python
enabled_str = config_values[("mlflow", "enabled")]
enabled = False
if enabled_str is not None:
    enabled = enabled_str.lower() in ("true", "1", "yes", "on", "enabled")
```

**After:**
```python
enabled_value = config_values[("mlflow", "enabled")]
enabled = enabled_value is True
```

## Tests to update

### `tests/cli/test_utils.py` — `TestResolveIssueInteractionFlags`

Update mock return values from string `"True"`/`"False"` to native `True`/`False`:

- `test_cli_flags_override_config`: `"True"` → `True`
- `test_config_values_used_when_cli_none`: `"True"` → `True`
- `test_cli_true_overrides_config_false`: `"False"` → `False`
- `test_partial_cli_override`: `"False"` → `False`, `"True"` → `True`

### `tests/cli/commands/coordinator/test_core.py` — `TestLoadRepoConfig`

- `test_load_repo_config_includes_issue_interaction_flags`: `"True"` → `True`
- `test_load_repo_config_defaults_flags_when_missing`: no change (already `None`)

### `tests/integration/test_mlflow_integration.py`

- `test_enabled_but_mlflow_unavailable`: `"true"` → `True`
- Any other tests mocking mlflow enabled with string values → `True`/`False`

### Other mlflow test files

Search for mocks of `get_config_values` returning `("mlflow", "enabled"): "true"` or similar strings and update to native `True`/`False`.

## Checklist
- [ ] `cli/utils.py`: `== "True"` → `is True`
- [ ] `coordinator/core.py`: `== "True"` → `is True`
- [ ] `mlflow_config_loader.py`: delete flexible parsing, use `is True`
- [ ] All test mocks updated: string booleans → native booleans
- [ ] All checks pass (pylint, pytest, mypy)
