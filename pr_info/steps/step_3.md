# Step 3 — Remove duplicate anti-pattern call sites in three other files

> Cleanup. Four inline copies of `Path(str(resources.files(...)))` are replaced with
> `get_labels_config_path(None)`, routing all bundled-resource reads through the
> now-correct single codepath.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Three source files contain private helper functions or inline blocks that duplicate
the broken Path(str(Traversable)) anti-pattern fixed in Step 2.
Replace each one with a call to get_labels_config_path(None).

FILE 1: src/mcp_coder/workflows/vscodeclaude/config.py
  - Function: _load_labels_config()
  - Replace the entire body with:
        from ...utils.github_operations.label_config import get_labels_config_path
        return load_labels_config(get_labels_config_path(None))
  - Remove the `from importlib import resources` import if it is no longer used
    elsewhere in the file (check before removing).

FILE 2: src/mcp_coder/workflows/vscodeclaude/issues.py
  - Function: _load_labels_config()
  - Same replacement as FILE 1.
  - Remove unused `from importlib import resources` import if no longer used.

FILE 3: src/mcp_coder/cli/commands/coordinator/core.py
  - Two functions: _filter_eligible_issues() and get_eligible_issues()
  - Each contains an inline block:
        from importlib import resources
        config_resource = resources.files("mcp_coder.config") / "labels.json"
        config_path = Path(str(config_resource))
        labels_config = load_labels_config(config_path)
  - Replace each block with:
        from ....utils.github_operations.label_config import get_labels_config_path
        labels_config = load_labels_config(get_labels_config_path(None))
  - The `from importlib import resources` import inside those functions can be removed.
  - The top-level `from pathlib import Path` import in core.py is still used elsewhere
    — do NOT remove it.

After making changes, run the full test suite to confirm no regressions.
```

---

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/config.py` | Replace `_load_labels_config()` body |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | Replace `_load_labels_config()` body |
| `src/mcp_coder/cli/commands/coordinator/core.py` | Replace inline block in 2 functions |

## WHAT

### `vscodeclaude/config.py` — `_load_labels_config()`

Before:
```python
def _load_labels_config() -> dict[str, Any]:
    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    result: dict[str, Any] = load_labels_config(config_path)
    return result
```

After:
```python
def _load_labels_config() -> dict[str, Any]:
    from ...utils.github_operations.label_config import get_labels_config_path
    result: dict[str, Any] = load_labels_config(get_labels_config_path(None))
    return result
```

### `vscodeclaude/issues.py` — `_load_labels_config()`

Same pattern as `config.py`.

### `coordinator/core.py` — inline blocks in two functions

Before (repeated in both functions):
```python
    from importlib import resources
    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    labels_config = load_labels_config(config_path)
```

After:
```python
    from ....utils.github_operations.label_config import get_labels_config_path
    labels_config = load_labels_config(get_labels_config_path(None))
```

## HOW

- `get_labels_config_path` is imported inline (local import inside function) to avoid
  any circular-import risk — consistent with the existing local-import style in these files
- `load_labels_config` is already imported at the top of each file — no new top-level
  imports needed
- No logic changes: all functions behave identically to before, but now read via the
  correct `Traversable` path

## DATA

- No change to inputs, outputs, or return types of any of the three affected functions
- `_load_labels_config()` still returns `dict[str, Any]`
- Existing tests for coordinator and vscodeclaude continue to pass (behaviour unchanged)
