# Summary: Add GITHUB section to `mcp-coder verify`

**Issue:** #895 — verify - add GITHUB section using upstream `verify_github()`

## Goal

Add a GITHUB verification section to `mcp-coder verify` that calls the upstream
`verify_github(project_dir)` from `mcp-workspace` and displays the results.

## Architectural / Design Changes

- **No new modules or classes.** This extends the existing verify command with one
  more section, following the exact same pattern used by BASIC VERIFICATION, MLFLOW,
  and LLM PROVIDER sections.
- **`_compute_exit_code()` gains one parameter** (`github_result`) — placed before the
  active-provider check because GitHub access is provider-independent (relevant for
  both claude and langchain).
- **`_LABEL_MAP` grows by 9 entries** — the 9 check keys returned by `verify_github()`.
- **Import path:** `verify_github` is imported through the existing shim
  (`mcp_coder.mcp_workspace_github`) — hard import, no try/except guard.
- **Section placement in output:** after PROJECT, before LLM PROVIDER. This is a
  natural fit since GitHub repo access is a project-level concern, not an LLM concern.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/verify.py` | Import `verify_github`, add 9 label mappings, add `github_result` param to `_compute_exit_code()`, call `verify_github()` in `execute_verify()`, collect GitHub install hints |
| `tests/cli/commands/test_verify_exit_codes.py` | Tests for `_compute_exit_code()` with `github_result` |
| `tests/cli/commands/test_verify_format_section.py` | Tests for GitHub label mappings in `_format_section()` |
| `tests/cli/commands/test_verify_orchestration.py` | Tests for GITHUB section placement, `verify_github` call, install hints |

No new files or modules are created.

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `github_result` to `_compute_exit_code()` + exit code tests | `verify: add github_result to _compute_exit_code` |
| 2 | Add 9 GitHub label mappings to `_LABEL_MAP` + formatting tests | `verify: add GitHub label mappings` |
| 3 | Wire `verify_github()` into `execute_verify()` orchestration + tests | `verify: add GITHUB section to execute_verify` |

## Key Decisions (from issue)

- Always exit 1 when `overall_ok` is False (provider-independent)
- No `gh` CLI check needed — PyGithub verification is sufficient
- Always show GITHUB section, even when no token is configured
- Hard import — broken install should be fixed, not silently skipped
