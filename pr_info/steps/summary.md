# Summary: Fix stale references from github_operations migration (#888)

## Goal

Fix stale documentation and config references left over from the github_operations migration to mcp_workspace.

## Architectural / Design Changes

**None.** This is a documentation and config cleanup task. No code, APIs, or architectural boundaries change. The only structural concern is keeping the `.importlinter` contract comments accurate so future contributors understand which modules are allowed to use `requests`.

## Verification Results

During planning, each referenced file was checked for staleness:

| # | File | Claimed stale | Verified? |
|---|------|---------------|-----------|
| 1 | `docs/getting-started/label-setup.md:92` | Import path `mcp_coder.utils.github_operations.label_config` "no longer exists locally" | **Needs re-verification** — file existed at planning time. May have been migrated since. |
| 2 | `docs/architecture/architecture.md` | References `utils/github_operations/` as local dir and test path | **Needs re-verification** — directory existed at planning time. |
| 3 | `docs/tests/issues.md` | References old test path `tests/utils/github_operations/test_github_utils.py` | **Needs re-verification** — file existed at planning time. |
| 4 | `.importlinter:321` | Comment says "only in github_operations" but contract also allows `jenkins_operations.client` | **Confirmed stale.** |

**Important implementation note:** Items #1–#3 must be re-verified at implementation time. If the referenced files/paths still exist and are correct, those items should be skipped — do not "fix" references that point to real code. Only item #4 is unconditionally confirmed.

## Files Modified

| File | Change |
|------|--------|
| `.importlinter` | Update comment on Requests Library Isolation contract (line 321) |
| `docs/getting-started/label-setup.md` | Update import example on line 92 (if path is confirmed stale) |
| `docs/architecture/architecture.md` | Update directory/test path references (if confirmed stale) |
| `docs/tests/issues.md` | Update test file path reference (if confirmed stale) |

No files created. No files deleted.

## Steps

- **Step 1**: Fix `.importlinter` misleading comment (confirmed stale)
- **Step 2**: Verify and fix stale doc references in all three doc files (conditional on verification)
