# Step 1: Soft-Delete File I/O Helpers

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context.
> Implement Step 1: add three soft-delete helper functions to `helpers.py` with tests.
> Follow TDD — write tests first in a new `test_soft_delete.py`, then implement.
> Run all three code quality checks (pylint, pytest, mypy) after implementation.

## WHERE

- **Modify**: `src/mcp_coder/workflows/vscodeclaude/helpers.py`
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (re-export new functions)
- **Create**: `tests/workflows/vscodeclaude/test_soft_delete.py`

## WHAT

Three functions added to `helpers.py`:

```python
TO_BE_DELETED_FILENAME = ".to_be_deleted"

def load_to_be_deleted(workspace_base: str) -> set[str]:
    """Load soft-delete registry. Returns set of folder names."""

def add_to_be_deleted(workspace_base: str, folder_name: str) -> None:
    """Add folder name to soft-delete registry. No-op if already present."""

def remove_from_to_be_deleted(workspace_base: str, folder_name: str) -> None:
    """Remove folder name from registry. Deletes file if empty."""
```

## HOW

- Import `Path` from `pathlib` (already imported in helpers.py context)
- Add to `__all__` in `helpers.py`
- Re-export from `__init__.py`
- No new dependencies

## ALGORITHM

```
# load_to_be_deleted
path = Path(workspace_base) / TO_BE_DELETED_FILENAME
if not path.exists(): return set()
return {line.strip() for line in path.read_text().splitlines() if line.strip()}

# add_to_be_deleted
existing = load_to_be_deleted(workspace_base)
if folder_name in existing: return
path = Path(workspace_base) / TO_BE_DELETED_FILENAME
with path.open("a") as f: f.write(folder_name + "\n")

# remove_from_to_be_deleted
existing = load_to_be_deleted(workspace_base)
existing.discard(folder_name)
if not existing: path.unlink(missing_ok=True); return
path.write_text("\n".join(sorted(existing)) + "\n")
```

## DATA

- **Input**: `workspace_base: str` — path to workspace directory
- **Input**: `folder_name: str` — folder name relative to workspace_base (e.g., `"mcp-coder_123"`)
- **File format**: plain text, one folder name per line, no headers
- **Returns**: `load` returns `set[str]`, others return `None`

## TESTS (`test_soft_delete.py`)

```python
# Test load_to_be_deleted
- test_load_empty_when_file_missing() → returns empty set
- test_load_returns_folder_names() → reads file with 2 entries, returns set of 2
- test_load_ignores_blank_lines() → file with blank lines, returns only non-blank

# Test add_to_be_deleted
- test_add_creates_file_if_missing() → file created with entry
- test_add_appends_to_existing() → second entry added
- test_add_idempotent() → adding same name twice, file has it once

# Test remove_from_to_be_deleted
- test_remove_entry() → removes one of two entries, other remains
- test_remove_last_entry_deletes_file() → file deleted when empty
- test_remove_nonexistent_entry_no_error() → no-op when entry not in file
- test_remove_when_file_missing_no_error() → no-op when file doesn't exist
```

## COMMIT MESSAGE

```
feat(vscodeclaude): add soft-delete file helpers

Add load_to_be_deleted(), add_to_be_deleted(), and
remove_from_to_be_deleted() to helpers.py for managing the
.to_be_deleted registry file in workspace_base.
```
