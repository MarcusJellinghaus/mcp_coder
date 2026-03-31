# Step 3: Suffix-Aware Folder Naming

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context.
> Implement Step 3: modify `get_working_folder_path()` in `workspace.py` to handle folder name collisions using `-folder2` through `-folder9` suffixes.
> Follow TDD — write tests first, then implement.
> Run all three code quality checks (pylint, pytest, mypy) after implementation.

## WHERE

- **Modify**: `src/mcp_coder/workflows/vscodeclaude/workspace.py`
- **Modify**: `tests/workflows/vscodeclaude/test_workspace.py`

## WHAT

### `get_working_folder_path()` — suffix-aware

```python
def get_working_folder_path(
    workspace_base: str,
    repo_name: str,
    issue_number: int,
) -> Path:
    """Get full path for working folder.

    If the base name exists on disk or is in .to_be_deleted, tries
    suffixes -folder2 through -folder9. Raises ValueError if all
    slots are exhausted.
    """
```

Signature unchanged — `workspace_base` is already a parameter.

## HOW

- Import `load_to_be_deleted` from `.helpers`
- No new parameters needed (already has `workspace_base`)

## ALGORITHM

```python
base_name = f"{sanitized_repo}_{issue_number}"
to_be_deleted = load_to_be_deleted(workspace_base)
base_path = Path(workspace_base)

# Try base name first
if not (base_path / base_name).exists() and base_name not in to_be_deleted:
    return base_path / base_name

# Try suffixes -folder2 through -folder9
for i in range(2, 10):
    candidate = f"{base_name}-folder{i}"
    if not (base_path / candidate).exists() and candidate not in to_be_deleted:
        return base_path / candidate

raise ValueError(f"All folder slots exhausted for {base_name} (max: -folder9)")
```

## DATA

- **Input**: unchanged
- **Output**: `Path` — may now include suffix like `mcp-coder_123-folder2`
- **Side effect**: none (pure path computation)
- **Error**: `ValueError` if slots 1–9 all occupied

## TESTS (add to `test_workspace.py`)

```python
# Base name available
- test_get_working_folder_path_returns_base_when_available()
    → no conflict, returns workspace_base/repo_123

# Base name on disk
- test_get_working_folder_path_suffix_when_base_exists_on_disk(tmp_path)
    → create base folder on disk, returns workspace_base/repo_123-folder2

# Base name in .to_be_deleted
- test_get_working_folder_path_suffix_when_base_in_to_be_deleted(tmp_path)
    → base name in .to_be_deleted file, returns workspace_base/repo_123-folder2

# Both base and -folder2 occupied
- test_get_working_folder_path_skips_occupied_suffixes(tmp_path)
    → base + folder2 occupied, returns workspace_base/repo_123-folder3

# Mixed: some on disk, some in .to_be_deleted
- test_get_working_folder_path_checks_both_disk_and_registry(tmp_path)
    → base on disk, folder2 in .to_be_deleted, returns folder3

# All slots exhausted
- test_get_working_folder_path_raises_when_all_slots_exhausted(tmp_path)
    → base + folder2-9 all occupied, raises ValueError

# Existing behavior preserved
- test_get_working_folder_path_unchanged_when_no_conflicts()
    → clean workspace, returns same as before (no .to_be_deleted file)
```

## COMMIT MESSAGE

```
feat(vscodeclaude): suffix-aware folder naming for soft-deleted folders

When creating a session folder, check both disk and .to_be_deleted
for name collisions. Use -folder2 through -folder9 suffixes when
the base name is unavailable. Raise ValueError if all slots exhausted.
```
