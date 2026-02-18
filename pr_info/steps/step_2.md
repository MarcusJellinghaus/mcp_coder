# Step 2: Update `cleanup_stale_sessions` to use the reason in warnings

## LLM Prompt

```
See pr_info/steps/summary.md for full context.
Step 1 (get_stale_sessions returning 3-tuple) is already complete.

Implement Step 2: update `cleanup_stale_sessions` in
`src/mcp_coder/workflows/vscodeclaude/cleanup.py` to:
1. Unpack the 3-tuple from get_stale_sessions
2. Include the reason in the "No Git" / "Error" non-empty folder warning messages

Do NOT modify dirty-folder warnings (they stay unchanged per the spec).
Do NOT yet modify tests (that is Step 3).
```

---

## WHERE

**File:** `src/mcp_coder/workflows/vscodeclaude/cleanup.py`  
**Function:** `cleanup_stale_sessions`

---

## WHAT

Two small changes inside `cleanup_stale_sessions`:

### 1. Unpack 3-tuple

```python
# Before
for session, git_status in stale_sessions:

# After
for session, git_status, reason in stale_sessions:
```

### 2. Update the non-empty No Git / Error warning (inside the `else:` branch)

```python
# Before
logger.warning("Skipping folder (%s): %s", git_status.lower(), folder)
print(f"[WARN] Skipping ({git_status.lower()}): {folder}")

# After
logger.warning("Skipping folder (%s, %s): %s", git_status.lower(), reason, folder)
print(f"[WARN] Skipping ({git_status.lower()}, {reason}): {folder}")
```

---

## HOW

- `reason` is now available from the unpacked tuple — no computation needed here.
- The dirty-folder branch (`elif git_status == "Dirty":`) is **not touched**.
- The empty-folder branch inside `else:` (delete path) is **not touched**.
- No new imports.

---

## ALGORITHM

```
for session, git_status, reason in stale_sessions:
    ...
    else:  # "No Git" or "Error"
        if is_directory_empty(folder_path):
            # unchanged — delete empty folder
        else:
            # Non-empty — include reason in warning
            logger.warning("Skipping folder (%s, %s): %s", git_status.lower(), reason, folder)
            print(f"[WARN] Skipping ({git_status.lower()}, {reason}): {folder}")
```

---

## DATA

No change to return type. `cleanup_stale_sessions` still returns
`dict[str, list[str]]` with keys `"deleted"` and `"skipped"`.

### Example output after this change

```
[WARN] Skipping (no git, closed): /path/to/folder
[WARN] Skipping (no git, blocked): /path/to/folder
[WARN] Skipping (no git, bot status): /path/to/folder
[WARN] Skipping (no git, stale → status-05:bot-pickup): /path/to/folder
[WARN] Skipping (no git, closed, blocked): /path/to/folder
[WARN] Skipping (error, stale → status-10:pr-created): /path/to/folder
```
