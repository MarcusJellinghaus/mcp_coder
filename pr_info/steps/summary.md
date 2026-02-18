# Summary: Pass Pre-Fetched Issues to process_eligible_issues

**Issue:** #468
**Title:** fix: pass pre-fetched issues to process_eligible_issues to avoid duplicate-protection cache miss

---

## Problem

`execute_coordinator_vscodeclaude` (`--cleanup` command) calls `get_all_cached_issues` **twice**
in the same invocation:

1. Inside `_build_cached_issues_by_repo` — may hit the 50-second duplicate-protection (DP) window
   and return stale disk cache.
2. Inside `process_eligible_issues` — **always** hits DP (because step 1 just reset `last_checked`)
   and reads the same stale data.

When step 1 itself is blocked by DP (e.g. `status` ran within the last 50 s), newly created issues
are invisible to `--cleanup` for up to ~50–60 seconds.

---

## Fix

Pass the already-fetched issue list from `_build_cached_issues_by_repo` into
`process_eligible_issues` as an optional parameter, so the second `get_all_cached_issues` call is
skipped entirely when the caller already has fresh data.

---

## Architectural / Design Changes

| Aspect | Before | After |
|---|---|---|
| `get_all_cached_issues` calls per `--cleanup` run | 2 (always) | 1 (always) |
| `process_eligible_issues` data source | always fetches independently | uses pre-fetched list when provided |
| Backward compatibility | N/A | `all_cached_issues=None` default keeps all existing callers unchanged |
| DP window vulnerability | new issue invisible for ~50–60 s | new issue visible immediately |

**No new modules, classes, or abstractions are introduced.**
The change is a single optional parameter + the caller passing a pre-derived list.

---

## Files Created / Modified

| File | Action |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | **Modified** — add `all_cached_issues` optional param to `process_eligible_issues` |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | **Modified** — derive and pass pre-fetched issues in per-repo loop |
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | **Modified** — add unit test for new parameter behaviour |

No new files are created.

---

## Steps

- [Step 1](step_1.md) — Add `all_cached_issues` optional parameter to `process_eligible_issues` + unit test
- [Step 2](step_2.md) — Pass pre-fetched issues from caller in `execute_coordinator_vscodeclaude`
