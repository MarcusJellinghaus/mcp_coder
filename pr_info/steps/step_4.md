# Step 4 — Reconcile `.to_be_deleted` against live VSCode (Item #8)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`) in
> full. Step 1 (PID-bound title matching) is a prerequisite — `is_vscode_open_for_folder`
> must already use the tightened cmdline check from Step 1's path. Follow TDD.
> One commit at the end.

## Goal

Close the loop on prior false-negative soft-deletes. If a folder name in
`.to_be_deleted` matches a currently-open VSCode cmdline, the entry is
removed without a deletion attempt and a reconciliation warning is logged —
instead of being retried (and failing) forever.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
  (extend the `.to_be_deleted` retry loop in `cleanup_stale_sessions`)
- `tests/workflows/vscodeclaude/test_cleanup.py`

## WHAT — function signatures

No new public API. The reconciliation lives inside the existing
`.to_be_deleted` retry loop in `cleanup_stale_sessions`. Import
`is_vscode_open_for_folder` from `.sessions`.

```python
# cleanup.py — augment existing retry loop, no signature changes
```

## HOW — integration points

- Insert the reconciliation step between the `folder_path.exists()` early-exit
  and the existing `safe_delete_folder` call.
- The VSCode cache is already populated by `build_active_session_set` at the
  start of the command, so no extra `psutil.process_iter` calls.
- After Step 3 lands, the `not folder_path.exists()` early-exit composes
  cleanly with the orphan-workspace flow.

## ALGORITHM

```
for folder_name in list(to_delete):
    folder_path = Path(workspace_base) / folder_name
    if not folder_path.exists():
        remove_from_to_be_deleted(workspace_base, folder_name)
        continue
    is_open, _ = is_vscode_open_for_folder(str(folder_path))
    if is_open:
        remove_from_to_be_deleted(workspace_base, folder_name)
        logger.warning(
            "Reconciled .to_be_deleted entry — VSCode is open on %s; "
            "removing entry without deletion (prior soft-delete was a false negative).",
            folder_name,
        )
        continue
    deletion = safe_delete_folder(folder_path)
    ...
```

## DATA

- Inputs unchanged.
- Side effects: registry entry removed; warning emitted via `logger.warning`.
- `safe_delete_folder` is NOT called when reconciliation fires.

## Tests (write first)

1. **Reconciliation fires**: tmp workspace; `.to_be_deleted` contains
   `mcp_coder_937`; folder exists. Mock `is_vscode_open_for_folder` to return
   `(True, 12345)`. Call `cleanup_stale_sessions(..., dry_run=False)`. Assert:
   - registry entry removed,
   - warning log captured (`"Reconciled .to_be_deleted entry"`),
   - `safe_delete_folder` not called (patch + `assert_not_called()`).
2. **No reconciliation → existing path runs**: same setup but
   `is_vscode_open_for_folder` returns `(False, None)` → existing
   `safe_delete_folder` retry path executes.
3. **Idempotence**: replay the reconciliation scenario — same outcome, no
   spurious warning the second time (because the entry was removed).

## Done when

- All tests pass.
- mypy, pylint clean.
- One commit: tests + implementation.
