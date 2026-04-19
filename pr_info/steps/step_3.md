# Step 3: New config discovery

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 3: Change `get_labels_config_path()` to drop `workflows/config/labels.json` convention, add `pyproject.toml` lookup and `config_override` parameter. Write tests first (TDD), then implement. Run all code quality checks after changes.

## WHERE

- `src/mcp_coder/utils/github_operations/label_config.py` — modify `get_labels_config_path()`
- `tests/workflows/test_label_config.py` — add discovery tests

## WHAT

### Modified function signature

```python
def get_labels_config_path(
    project_dir: Optional[Path] = None,
    config_override: Optional[Path] = None,
) -> Path | Traversable:
    """Get path to labels.json configuration file.
    
    Resolution order:
    1. config_override (explicit --config flag, highest priority)
    2. [tool.mcp-coder] labels-config in pyproject.toml (relative to project root)
    3. Bundled package defaults (mcp_coder/config/labels.json)
    """
```

### New private helper

```python
def _get_labels_config_from_pyproject(project_dir: Path) -> Optional[Path]:
    """Read labels-config from [tool.mcp-coder] in pyproject.toml.
    
    Returns absolute Path if configured and file exists, None otherwise.
    """
```

## HOW

- Modify `get_labels_config_path` in-place — add `config_override` parameter with default `None`
- Remove the `workflows/config/labels.json` check block
- Add `config_override` check first, then pyproject.toml check, then bundled fallback
- Existing callers (`issue_stats.py`, `set_status.py`) pass no `config_override`, so they keep working
- The pyproject.toml helper reads `[tool.mcp-coder].labels-config` as a string path relative to `project_dir`

## ALGORITHM

```
if config_override is not None:
    if not config_override.exists(): raise FileNotFoundError
    return config_override

if project_dir is not None:
    pyproject_path = _get_labels_config_from_pyproject(project_dir)
    if pyproject_path is not None:
        return pyproject_path

return resources.files("mcp_coder.config") / "labels.json"
```

### `_get_labels_config_from_pyproject`:

```
path = project_dir / "pyproject.toml"
if not path.exists(): return None
data = tomllib.load(path)
config_value = data["tool"]["mcp-coder"]["labels-config"]  # may KeyError → None
resolved = project_dir / config_value
return resolved if resolved.exists() else None
```

## DATA

- Input: `project_dir: Optional[Path]`, `config_override: Optional[Path]`
- Output: `Path | Traversable` pointing to labels.json
- Raises: `FileNotFoundError` if `config_override` is given but doesn't exist

## Tests (TDD — write first)

Add to `tests/workflows/test_label_config.py`:

```python
class TestConfigDiscovery:
    def test_config_override_takes_priority(self, tmp_path):
        """Explicit config_override is returned even when pyproject.toml exists."""
        
    def test_config_override_missing_raises(self, tmp_path):
        """Non-existent config_override raises FileNotFoundError."""
        
    def test_pyproject_toml_labels_config(self, tmp_path):
        """labels-config in pyproject.toml is used when no override given."""
        
    def test_pyproject_toml_missing_key_falls_to_bundled(self, tmp_path):
        """pyproject.toml without labels-config key falls back to bundled."""
        
    def test_no_project_dir_returns_bundled(self):
        """project_dir=None returns bundled config."""
        
    def test_pyproject_toml_nonexistent_path_falls_to_bundled(self, tmp_path):
        """labels-config pointing to non-existent file falls back to bundled."""
        
    def test_old_workflows_config_not_used(self, tmp_path):
        """workflows/config/labels.json is NOT used even if it exists (breaking change)."""
```

## Verification

- All existing tests pass (backward-compatible signature)
- New discovery tests pass
- Pylint, mypy, pytest all green
