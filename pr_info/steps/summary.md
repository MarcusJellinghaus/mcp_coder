# Issue #946 — Render per-permission probe results in `verify` GITHUB section

## Goal

Surface the 6 `perm_*` `CheckResult` entries that upstream `mcp-workspace#195` added to `verify_github()` as a labeled `[Permissions]` subsection at the end of the GITHUB output. The current downstream renderer drops them into the unmapped fallback path, which gives the user no signal about *which* permission is missing on a fine-grained PAT.

## Scope

Pure rendering change. No backend logic changes, no exit-code changes, no upstream version bump (the 6 `perm_*` keys arrive automatically through the existing `src/mcp_coder/mcp_workspace_github.py` shim).

## Architectural / design changes

None at the architecture level. This is an additive cosmetic change inside one function (`_format_section`) and one constant (`_LABEL_MAP`):

- **Reuses the existing TOML-style subsection convention** already used by CONFIG (`verify.py:626-636`) and PROJECT (`verify.py:182-198`): blank line → `"  [Group]"` header at indent 2 → rows at indent 4.
- **Reuses the existing `ok`-based symbol selection** in `_format_section`. Probe rows with `ok=False` render `[ERR]` like every other row in the section, even though upstream marks them `severity="warning"`. `_compute_exit_code` is untouched, so probe failures do not affect the CLI exit code (that gating is purely on `severity="error"` via `overall_ok`).
- **Header detection via key prefix** (`key.startswith("perm_")`) inside a one-shot local boolean — not a new constant, not a new helper. Detection lives in the generic-row handler, *after* the `branch_protection` children block, so the existing `continue` paths bypass it.
- **No new module, no new function, no new abstraction.** The change is ~10 lines of additions across one `_LABEL_MAP` and one loop.

## Files modified

| Path | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify.py` | Add 6 entries to `_LABEL_MAP`. Add `permissions_header_emitted` boolean + header emit + indent=4 row in `_format_section`. |
| `tests/cli/commands/test_verify_format_section_basic.py` | Grow `TestGitHubLabelMappings._GITHUB_KEYS` from 11 → 17. Add new `TestPermissionProbes` class (~2 tests). |
| `tests/cli/commands/test_verify_orchestration.py` | Add one orchestration test asserting probe rows reach end-to-end output. Inline the GitHub result dict (matches existing pattern at line 520). |

No new files. No deleted files. No moved files.

## Constraints (from issue)

- **6 keys, not 7** — no `perm_metadata_read`. Upstream does not emit it.
- **Label for `perm_workflows_read` = `"Actions: Read"`** — matches upstream probe wording and GitHub PAT UI.
- **Symbol from `ok` only** — `[ERR]` for `ok=False` even when `severity="warning"`. No special case for "not checked".
- **Exit code unaffected** — do not promote probe `severity` downstream.
- **`[Permissions]` header emitted at most once per section** via one-shot local boolean.
- **Layout matches existing convention** — blank line, header at indent 2, rows at indent 4.
- **Default `_LABEL_WIDTH=22`** already fits the longest new label (`Commit statuses: Read`, 21 chars).

## Out of scope

Write-permission rows, restructuring the GITHUB section, `--verify-permissions` flag.

## Implementation steps

One self-contained step (`step_1.md`). The change is a single cohesive feature: the `_LABEL_MAP` additions, the rendering logic, the test-invariant tuple update, and the new tests are all interdependent and ship as one atomic commit. Splitting them would either break tests at intermediate commits or create empty churn.
