# Summary — Issue #1023: Remove parsers.py from large-files-allowlist

## Goal

Complete the acceptance criterion for issue #1023: `src/mcp_coder/cli/parsers.py`
must be **under 750 lines AND off `.large-files-allowlist`**.

The code-level work was already done by #90 (merged as PR #1024), which shrank
`parsers.py` from 762 to **560 lines** by extracting per-flag helpers into
`cli/shared_args.py` and command descriptions into `cli/command_catalog.py`.
Only the allowlist cleanup remains.

## Scope

This is a **maintenance / bookkeeping change**, not a code refactor. It removes a
single stale entry from a plain-text allowlist file. No Python source is modified.

## Architectural / Design Changes

**None.** There are no architectural or design changes.

- No modules are split, moved, renamed, or created.
- No public/private API changes.
- No import-graph, layering, or dependency changes.
- The only file touched is the plain-text `.large-files-allowlist` config.

The relevant design context (already in place, unchanged by this work):

- `src/mcp_coder/checks/file_sizes.py` computes `passed = len(violations) == 0`.
  A stale allowlist entry is reported as advisory information but does **not**
  fail the check. Removing the entry is therefore required by the issue's
  acceptance criterion, but nothing is currently broken.
- `parsers.py` now composes helpers from `cli/shared_args.py` and descriptions
  from `cli/command_catalog.py` (result of #90) — this is the reason it is
  compliant. Per the refactoring guide's **"no-recycle" rule**, the compliant
  file is left untouched (no proactive further split).

## Files / Folders Created or Modified

| Path | Action | Notes |
|------|--------|-------|
| `.large-files-allowlist` | **Modified** | Remove the single line `src/mcp_coder/cli/parsers.py` |
| `pr_info/steps/summary.md` | Created | This document |
| `pr_info/steps/step_1.md` | Created | Implementation step |

**No Python source files, modules, or folders are created or modified.**

## Out of Scope (do NOT touch)

- Any further split or edit of `parsers.py` — it is already compliant (560 < 750);
  honor the refactoring guide's "no-recycle" rule.
- The two other stale allowlist entries
  (`src/mcp_coder/workflows/vscodeclaude/workspace.py`,
  `tests/workflows/vscodeclaude/test_workspace_startup_script.py`) — tracked
  separately in #1029.

## Verification

`mcp-coder check file-size --max-lines 750` must report `parsers.py` as
**neither a violation nor a stale entry**.

## Steps

1. [step_1.md](./step_1.md) — Remove `parsers.py` from `.large-files-allowlist` and verify.
