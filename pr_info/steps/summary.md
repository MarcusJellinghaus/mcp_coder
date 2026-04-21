# Summary: Fix stale references from github_operations migration (#888)

## Goal

Fix stale documentation and config references left over from the github_operations migration to mcp_workspace.

## Architectural / Design Changes

**None.** This is a documentation and config cleanup task. No code, APIs, or architectural boundaries change. The only structural concern is keeping the `.importlinter` contract comments accurate so future contributors understand which modules are allowed to use `requests`.

## Verification Results

During planning, each referenced file was checked for staleness. The `github_operations` package still exists with all referenced files and paths intact.

| # | File | Claimed stale | Verified? |
|---|------|---------------|-----------|
| 1 | `docs/getting-started/label-setup.md:92` | Import path `mcp_coder.utils.github_operations.label_config` "no longer exists locally" | **Verified — still valid, no change needed.** The `github_operations` package and `label_config.py` still exist at the referenced path. |
| 2 | `docs/architecture/architecture.md` | References `utils/github_operations/` as local dir and test path | **Verified — still valid, no change needed.** The directory and all sub-modules still exist. |
| 3 | `docs/tests/issues.md` | References old test path `tests/utils/github_operations/test_github_utils.py` | **Verified — still valid, no change needed.** The test file and class still exist at the referenced path. |
| 4 | `.importlinter:321` | Comment says "only in github_operations" but contract also allows `jenkins_operations.client` | **Confirmed stale.** |

## Files Modified

| File | Change |
|------|--------|
| `.importlinter` | Update comment on Requests Library Isolation contract (line 321) |

No other files need changes — the three doc references (label-setup.md, architecture.md, issues.md) all point to paths that still exist.

## Steps

- **Step 1**: Fix `.importlinter` misleading comment (confirmed stale — single-step, single-commit task)
