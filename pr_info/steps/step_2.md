# Step 2 — Fix `label_config.py`: return Traversable + accept it in load_labels_config

> Core fix. After this step the regression test from Step 1 passes.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Modify `src/mcp_coder/utils/github_operations/label_config.py` as follows:

1. Add import at top of file:
       from importlib.resources.abc import Traversable

2. Change `get_labels_config_path` return type from `Path` to `Path | Traversable`.
   In the bundled-fallback branch, remove the Path(str(...)) conversion and return
   the Traversable directly:
       config_resource = resources.files("mcp_coder.config") / "labels.json"
       return config_resource

3. Change `load_labels_config` signature to accept `Path | Traversable`.
   Replace the existing body with the simplified logic:
   - Raise FileNotFoundError only if the argument is a Path and does not exist
   - Call .read_text(encoding="utf-8") on the argument (works for both Path and Traversable)
   - Parse with json.loads() and validate "workflow_labels" key as before
   (No if/else split needed — both types share .read_text())

4. Update the docstring of `load_labels_config` to reflect the new accepted types.

Do not change any other functions, the module docstring, or any other files.
Run the tests in tests/workflows/test_label_config.py to verify all pass.
```

---

## WHERE

- **File**: `src/mcp_coder/utils/github_operations/label_config.py`

## WHAT

### Imports to add

```python
from importlib.resources.abc import Traversable
```

### `get_labels_config_path` — changed return type and bundled branch

```python
def get_labels_config_path(project_dir: Optional[Path] = None) -> Path | Traversable:
```

Bundled fallback (replaces the existing 3-line conversion block):
```python
    return resources.files("mcp_coder.config") / "labels.json"
```

### `load_labels_config` — changed signature and body

```python
def load_labels_config(config_path: Path | Traversable) -> Dict[str, Any]:
```

## HOW

- `Traversable` is available as `importlib.resources.abc.Traversable` in Python 3.11+
  (the project's minimum version per `pyproject.toml`)
- All existing callers of `load_labels_config` that pass a `Path` continue to work unchanged
- The `isinstance(config_path, Path)` branch preserves the existing `FileNotFoundError`
  message exactly — no behaviour change for the local-file path

## ALGORITHM

```python
# load_labels_config body
if isinstance(config_path, Path) and not config_path.exists():
    raise FileNotFoundError(f"Label configuration not found: {config_path}")
text = config_path.read_text(encoding="utf-8")
config = json.loads(text)
if "workflow_labels" not in config:
    raise ValueError("Configuration missing required key: 'workflow_labels'")
return config
```

> Both `Path` and `Traversable` expose `.read_text()`, so the branch only needs to
> guard the `FileNotFoundError`. No duplication.

## DATA

- `get_labels_config_path` return: `Path` (local override) or `Traversable` (bundled)
- `load_labels_config` parameter: `Path | Traversable`
- `load_labels_config` return: `Dict[str, Any]` — unchanged
- Error behaviour for `Path` inputs: unchanged (`FileNotFoundError`, `json.JSONDecodeError`, `ValueError`)
- Error behaviour for `Traversable`: only `json.JSONDecodeError` and `ValueError` (no `FileNotFoundError`)
