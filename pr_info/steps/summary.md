# Wire `verify_git` into `mcp-coder verify` — Implementation Summary

**Issue:** [#937](https://github.com/MarcusJellinghaus/mcp-coder/issues/937) — Wire `verify_git` into `mcp-coder verify`

## Goal

Surface git signing misconfigurations through `mcp-coder verify` before they cause silent unsigned commits. The function already exists upstream (`mcp_workspace.git_operations.verification.verify_git`); this issue is purely shim re-export + CLI wiring.

## Architectural / Design Changes

| Aspect | Change | Rationale |
|---|---|---|
| Shim surface | Add `verify_git` re-export to `mcp_workspace_git.py` | Mirrors `verify_github` exposure in `mcp_workspace_github.py`. All upstream symbols flow through shims; this is the only allowed import path inside `mcp_coder`. |
| Verify section ordering | New `=== GIT ===` section between PROJECT (`0c`) and GITHUB (renumbered `0e`) | Local-first grouping: git is a prerequisite for GitHub. Matches Decision #2 of the issue. |
| Tier 3 deep probe | Always-on (`actually_sign=True`, no `--sign-test` flag) | Upstream gates Tier 3 on `signing_intent_detected` → zero cost when signing isn't configured; max diagnostic value when it is. Matches Decision #3. |
| Exit code | `_compute_exit_code` gains `git_result` parameter; rejects on `not git_result.get("overall_ok")` (provider-independent) | Mirrors the existing `github_result` handling exactly. Severity-driven `overall_ok` upstream means "not configured" → ok=True → no false-positive failures. |
| Formatter | **No changes** | `_format_section` already handles the `CheckResult` TypedDict shape generically. `_BRANCH_PROTECTION_CHILDREN` special-casing only triggers on those four GitHub keys. |
| Logging | **No new logging in the wiring layer** | Decision #11: `verify_git` upstream deliberately avoids `@log_function_call` to prevent leaking key IDs / fingerprints / signed payloads. The shim and CLI must not reintroduce this. |

## Files Created / Modified

### Modified

- `src/mcp_coder/mcp_workspace_git.py` — add `verify_git` import + `__all__` entry
- `src/mcp_coder/cli/commands/verify.py` — import shim, extend `_LABEL_MAP` (13 keys), extend `_compute_exit_code` signature, insert `0d` GIT section
- `tests/test_mcp_workspace_git_smoke.py` — bump `__all__` length assertion 28 → 29
- `tests/cli/commands/test_verify_orchestration.py` — add `_mock_git` autouse fixture so existing tests don't hit real git
- `tests/cli/commands/test_verify_format_section_basic.py` — add `TestGitLabelMappings` class (unit smoke test for the new section)
- `tests/cli/commands/test_verify_integration.py` — add `git_integration`-marked test for the gpgsign-without-key scenario

### Created

None — the change is purely additive within existing files.

## Step Overview

Two steps. Each step is one commit with tests + implementation + all checks passing.

| # | Title | Scope |
|---|---|---|
| 1 | Re-export `verify_git` from the shim | `mcp_workspace_git.py` import + `__all__`; bump smoke-test length assertion |
| 2 | Wire GIT section into `mcp-coder verify` | Section wiring, label map, exit code, orchestration fixture, unit smoke test, integration test |

## Out of Scope (per issue)

- Any signing-fix logic (lives upstream in mcp-workspace).
- Auto-fix / interactive setup.
- A separate `--sign-test` flag.

## Reference Decisions (from issue #937)

- **#1** Section title is `GIT` (short, all-caps, matches existing headers).
- **#2** Placement: between PROJECT and GITHUB.
- **#3** `actually_sign=True` always, no flag.
- **#4** Human-friendly labels (13 entries — see step 2).
- **#5** "Not configured" stays as `[OK] not configured` — no formatter change.
- **#11** No signing-key logging in the wiring layer.
