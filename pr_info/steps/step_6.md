# Step 6 — Cleanup migration (ordering fix, lock veto, retry loop consumes assessment)

**Read first:** [summary.md](./summary.md) (sections "Key behavioural fixes":
cleanup ordering, lock-failure veto, `.to_be_deleted` retry loop). This closes the
**destructive** bugs and the second #38 door.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- Tests: `tests/workflows/vscodeclaude/test_cleanup.py`, `tests/workflows/vscodeclaude/test_soft_delete.py`

## WHAT
- `get_stale_sessions(...)` and `cleanup_stale_sessions(...)` take
  `assessments: dict[str, SessionAssessment]` instead of `active_set: dict[str, bool]`.
- `delete_session_folder(...)` reorders deletion and removes the unconditional
  workspace-file unlink.

## HOW
- This is one consumer migration: flip `get_stale_sessions`/`cleanup_stale_sessions`
  to take `assessments` **and** their `commands.py` call site in the **same** commit
  (green-state ordering from Step 5).
- **Skip active:** `if assessments[folder].verdict.active: continue` (covers KEEP_ACTIVE
  and zombie INVESTIGATE_ZOMBIE — both stay tracked).
- **Drive action from the assessment**, not re-derived stale/closed logic: branch on
  `a.decision.action` (`DELETE` → delete-if-clean; `REMOVE_MISSING` → remove session +
  orphan workspace file; `SKIP` → report `a.decision.reason`; `INVESTIGATE_ZOMBIE` →
  warn, keep). This is the R1 fix — `get_stale_sessions`'s big eligibility block is
  replaced by reading `a.decision`. The destruction-safety matrix already lives in
  `decide` (Step 3), so cleanup never re-checks git status to gate a DELETE.
- **Ordering fix (`delete_session_folder`):** attempt `safe_delete_folder(folder)`
  **first**; only on success delete the `.code-workspace` file. Remove the
  "always delete workspace file before folder deletion" block (`cleanup.py:225-232`).
- **Lock veto:** on `safe_delete_folder` failure, **do not** `remove_session` and
  **do not** unlink the workspace file. Add the folder to `.to_be_deleted` (retry
  queue) and return `False`. The session stays tracked. (Removes the `was_clean`
  soft-delete-then-`remove_session` asymmetry.)
- **`.to_be_deleted` retry loop (`cleanup.py:308-330`):** `.to_be_deleted` is keyed by
  folder **name**; `assessments` is keyed by folder **path**. Map each queue entry to
  its assessment by resolving the entry name under `workspace_base` to a path
  (`assessments.get(str(workspace_base / name))`). Then:
  - **assessment exists + `a.verdict.active`** → leave in queue (a live folder is spared;
    closes the second #38 door, replacing the cmdline-only `is_vscode_open_for_folder`).
  - **assessment exists + inactive** → retry `safe_delete_folder`.
  - **no assessment + folder still exists** (locked, no tracked session) → retry delete
    (today's behaviour).
  - **no assessment + folder gone** → drop the entry.

## ALGORITHM (`delete_session_folder`)
```
if folder_path.exists():
    deletion = safe_delete_folder(folder_path)
    if not deletion.success:
        add_to_be_deleted(workspace_base, folder_name)   # retry; never remove_session
        return False
    workspace_file.unlink(missing_ok=True)               # only AFTER folder gone
remove_session(folder)
return True
```

## DATA
`cleanup_stale_sessions` still returns `{"deleted": [...], "skipped": [...]}`.

## Tests (write first)
- Locked clean folder, dead session: workspace file **retained**, session **still
  tracked**, entry in `.to_be_deleted`, returns `False`.
- Retry loop: `.to_be_deleted` entry whose session assessment is `verdict.active`
  (title hit, cmdline miss) is **spared** — `safe_delete_folder` not called for it.
- Retry loop fallback: entry with **no** assessment but folder still exists → retry
  delete; entry with no assessment and folder gone → dropped from queue.
- `DELETE` action on a clean folder removes folder then workspace file then session.
- `REMOVE_MISSING` removes session + orphan workspace file.
- Zombie (`INVESTIGATE_ZOMBIE`) is skipped, never deleted.

## Done when
All three checks pass. One commit.
