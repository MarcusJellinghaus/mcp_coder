# Summary: Render `auto_delete_branches` in GitHub verify section

## Issue

[#917](https://github.com/MarcusJellinghaus/mcp-coder/issues/917) — Render the `auto_delete_branches` check from `verify_github()` in the `=== GITHUB ===` verify output section, as a **top-level** sibling of `Branch protection` (not nested under it).

## Motivation

Upstream `mcp-workspace` PR #163 (merged 2026-04-27) added a check for the repo-level "Automatically delete head branches" setting via `repo.delete_branch_on_merge`. The check is already emitted by `verify_github()`, but `mcp-coder`'s verify renderer drops the human-readable label, causing the raw key `auto_delete_branches` to leak into output.

## Architectural / Design Changes

**No architectural changes.** This is a one-line label-map extension that opts into the existing default rendering path in `_format_section`.

Key design decisions (already implemented in the existing renderer — we are NOT modifying them):

- **Top-level rendering, not nested.** The check is independent of branch protection (it reads a repo-level setting and runs whenever the repo is accessible). Nesting it under `branch_protection` would cause the parent-failure suppression rule in `_format_section` to hide it.
- **Default-path rendering suffices.** `_format_section`'s default branch already produces 2-space indent, symbol selection from `entry["ok"]`, and `(error)` suffix on failure. No new logic required.
- **Insertion order.** Upstream emits `auto_delete_branches` after the entire branch-protection block; `_format_section` iterates dict insertion order, producing the expected output position. No local re-ordering.
- **Severity = warning (upstream).** A failed `auto_delete_branches` does not contribute to `overall_ok`, so `_compute_exit_code` is unaffected.
- **Render verbatim.** Upstream value strings (`"enabled"` / `"disabled"`) are rendered as-is. Even if upstream temporarily emits other strings (e.g. `"auto-delete on merge"`), no local override.

## Expected Output

```
  Branch protection    [OK] main protected
    CI checks required [OK] 8 checks configured
    Strict mode             enabled
    Force push         [OK] disabled
    Branch deletion    [OK] disabled
  Auto-delete branches [OK] enabled
```

## Files Modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify.py` | Add one entry to `_LABEL_MAP`. |
| `tests/cli/commands/test_verify_format_section.py` | Extend `_GITHUB_KEYS` tuple; add one parametrized value-cases test and one suppression-independence test. |

## Files / Folders Created

None.

## Implementation Steps

1. [step_1.md](step_1.md) — Add label mapping + tests (single commit).

## Constraints

- Do **NOT** add `auto_delete_branches` to `_BRANCH_PROTECTION_CHILDREN`.
- Do **NOT** add value-string normalization or special-casing.
- Do **NOT** modify `_compute_exit_code` (severity is warning upstream).
- Do **NOT** modify the order of items rendered (upstream insertion order is correct).
