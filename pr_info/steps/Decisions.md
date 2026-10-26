# Decisions

## Step 4 — order of `MODULE` in `test_commit_push.py` (2026-10-26)

Context: the first implementation run blocked because two separate `move_symbol` calls left
`MODULE = ...` below `TestPushAfterCommit` and `TestCommitAutoPush`, and step 4 forbade
reordering by hand.

- Marcus: reorder by hand only if there is no other option.
- Other option found: one `move_symbol` call with `["MODULE", "TestPushAfterCommit",
  "TestCommitAutoPush"]` keeps source order (verified with a scratch probe). It leaves a stale
  `import MODULE` from the source module (ruff F811, not auto-fixable), which is deleted as an
  import edit.
- Fallback: if `MODULE` still ends up below the classes, moving that single assignment by hand
  to directly below the imports is allowed.
