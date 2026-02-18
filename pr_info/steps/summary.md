# Fix: FileNotFoundError for bundled labels.json when mcp-coder is installed as a package

## Issue Summary

When `mcp-coder implement` runs in an installed-package environment (e.g. Jenkins), the label
transition step fails with:

```
FileNotFoundError: Label configuration not found:
C:\..\.venv\Lib\site-packages\mcp_coder\config\labels.json
```

The path string looks correct, but `Path.exists()` returns `False` because the file is inside
a wheel or namespace package where `importlib.resources.files()` returns a `Traversable` that
is **not** a real filesystem path.

---

## Root Cause

`get_labels_config_path()` (and four inline copies in other modules) all do:

```python
config_resource = resources.files("mcp_coder.config") / "labels.json"
return Path(str(config_resource))   # anti-pattern
```

`Path(str(Traversable))` is not guaranteed to yield a real path in all installation
configurations. `load_labels_config` then calls `.exists()` on this fake path, which fails.

The same anti-pattern is duplicated in four more locations:

| File | Function |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/config.py` | `_load_labels_config()` |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | `_load_labels_config()` |
| `src/mcp_coder/cli/commands/coordinator/core.py` | `_filter_eligible_issues()` |
| `src/mcp_coder/cli/commands/coordinator/core.py` | `get_eligible_issues()` |

---

## Architectural / Design Changes

### Before

```
get_labels_config_path()  →  always returns Path
                               ↑ fragile: Path(str(Traversable)) for bundled case
load_labels_config(Path)  →  .exists() check + open()
                               ↑ fails when path is not a real filesystem path

Duplicate anti-pattern in 3 other files (4 more call sites)
```

### After

```
get_labels_config_path()  →  returns Path   (for local project override)
                           →  returns Traversable  (for bundled fallback — safe)
load_labels_config(Path | Traversable)
    if Path    →  .exists() check + open()     (unchanged behaviour)
    if Traversable  →  .read_text(encoding="utf-8")  (no filesystem check needed)

All 4 duplicate call sites replaced with get_labels_config_path(None)
  (single fix propagates everywhere)
```

### Key Design Decisions

1. **`load_labels_config` is the only place that handles `Traversable`** — callers do not need
   to know the distinction; they just pass what `get_labels_config_path` returns.
2. **`get_labels_config_path` return type widens to `Path | Traversable`** — this is the only
   public-API change. Existing callers that pass the result straight to `load_labels_config`
   are unaffected. Callers that inspect the path (none in current codebase) would need updating.
3. **`importlib.resources.abc.Traversable`** is used for the type annotation (available in
   Python 3.11+, which is the project's minimum version).
4. **No new files** — all changes are in existing source and test files.
5. **KISS**: the fix is confined to one module (`label_config.py`) plus mechanical cleanup of
   four duplicate call sites.

---

## Files Modified

| File | Change Type | Reason |
|---|---|---|
| `src/mcp_coder/utils/github_operations/label_config.py` | **Modify** | Core fix: return type + `load_labels_config` logic |
| `src/mcp_coder/workflows/vscodeclaude/config.py` | **Modify** | Remove inline anti-pattern; use `get_labels_config_path(None)` |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | **Modify** | Same |
| `src/mcp_coder/cli/commands/coordinator/core.py` | **Modify** | Same (2 functions) |
| `tests/workflows/test_label_config.py` | **Modify** | Add regression test for bundled resource loading |

No files are created or deleted.
