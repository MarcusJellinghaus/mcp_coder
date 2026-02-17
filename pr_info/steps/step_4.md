# Step 4 — Implementation: empty-folder gate in `cleanup_stale_sessions`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for context.

The tests in Step 3 are already written and currently failing.
Your goal is to make them pass by modifying source code only — do not change tests.

In `src/mcp_coder/workflows/vscodeclaude/cleanup.py`, modify the `else` branch
(the "No Git" or "Error" handler) inside `cleanup_stale_sessions()`.

Replace the current unconditional skip with:
- Check if the folder is empty using `Path(folder).exists() and not any(Path(folder).iterdir())`
- If empty: treat identically to the "Clean" branch (dry-run print or delete + result tracking)
- If non-empty (or inaccessible): keep the existing skip-with-warning behaviour

No new imports are needed — `Path` is already imported.
Do not change any other branch (Clean, Missing, Dirty) or any other function.
```

---

## WHERE

- **File:** `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- **Function:** `cleanup_stale_sessions(dry_run: bool, cached_issues_by_repo: ...) -> dict[str, list[str]]`
- **Location:** the `else:` branch at the bottom of the `for session, git_status in stale_sessions:` loop

---

## WHAT

The `else` branch currently reads:

```python
else:  # "No Git" or "Error"
    # Skip - needs manual investigation
    logger.warning("Skipping folder (%s): %s", git_status.lower(), folder)
    print(f"[WARN] Skipping ({git_status.lower()}): {folder}")
    result["skipped"].append(folder)
```

After this change it reads:

```python
else:  # "No Git" or "Error"
    folder_path = Path(folder)
    if folder_path.exists() and not any(folder_path.iterdir()):
        # Empty folder — safe to delete regardless of git status
        if dry_run:
            print(f"Add --cleanup to delete: {folder}")
        else:
            if delete_session_folder(session):
                print(f"Deleted: {folder}")
                result["deleted"].append(folder)
            else:
                print(f"Failed to delete: {folder}")
                result["skipped"].append(folder)
    else:
        # Non-empty — needs manual investigation
        logger.warning("Skipping folder (%s): %s", git_status.lower(), folder)
        print(f"[WARN] Skipping ({git_status.lower()}): {folder}")
        result["skipped"].append(folder)
```

---

## HOW

- `Path` is already imported at the top of `cleanup.py`
- `delete_session_folder` is already defined in the same file and used in the "Clean" branch
- No new imports required
- The emptiness check `not any(folder_path.iterdir())` safely handles inaccessible folders — `iterdir()` raises `PermissionError`/`OSError` if the folder cannot be listed, which will propagate; but since "No Git"/"Error" statuses imply the folder exists and is accessible (git status was obtained), this is safe in practice

---

## ALGORITHM

```
else:  # "No Git" or "Error"
    folder_path = Path(folder)
    if folder_path.exists() AND folder is empty (not any(iterdir())):
        if dry_run:
            print "Add --cleanup to delete: {folder}"
        else:
            call delete_session_folder(session) → track in deleted/skipped
    else:
        log warning; print [WARN] Skipping; append to skipped   # unchanged
```

---

## DATA

- Return value: `dict[str, list[str]]` — `"deleted"` and `"skipped"` lists, unchanged shape
- Dry-run: nothing appended to `"deleted"` (consistent with "Clean" dry-run behaviour)
- `delete_session_folder` handles session store cleanup internally — no extra calls needed
