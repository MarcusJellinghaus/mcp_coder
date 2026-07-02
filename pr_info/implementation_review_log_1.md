# Implementation Review Log — Run 1

Issue #984 — Surface MCP tools-exposed status in verify, icoder, and failure output.

Supervised implementation review. Each round: `/implementation_review` → triage → implement accepted → commit → `/check_branch_status`. Loop until a round produces zero code changes.

## Round 1 — 2026-07-02

**Findings** (from `/implementation_review` engineer subagent):
1. `verify._format_tools_exposed_section` `fatal` branch + `_probe_exposed_mcp_tools` `status="fatal"` are unreachable in the live flow — the guard raises `McpServersUnavailableError` before the init event is read.
2. icoder startup makes one blocking `"Reply with OK"` LLM round-trip (per approved plan tradeoff).
3. `_probe_exposed_mcp_tools` does not forward `settings_file`; startup count may differ from a real session.
4. 3-way status classification (fatal/pending/connected) duplicated in `verify` and `env_setup`.
5. create_pr formatter landed in `create_pr/core.py` (`_handle_create_pr_failure`), not `helpers.py` as the plan documented.
6. Commit `9c7403a` trimmed unrelated `.large-files-allowlist` entries.
7. Raw dict repr in `verify.py:587` `f"{len(tools)} ({fatal})"` (only reachable via dead branch #1).

**Decisions**: All **Skip**.
- 1,7: dead/unreachable defensive branch; cosmetic output only; skip per "speculative" rule.
- 2: deliberate, approved in `summary.md` icoder tradeoff.
- 3: coarse startup indicator by design.
- 4: two call sites produce different output shapes (formatted rows+hints vs `(count,status)` tuple); extraction adds indirection for ~3 lines of precedence logic — KISS/YAGNI.
- 5: functionally correct, correct boundary; pr_info deleted later.
- 6: CI green; unrelated to the surfacing feature.

**Verification**: engineer confirmed a real production diff exists across all 4 steps; all 153 targeted tests pass; no Critical/bugs/regressions found.

**Changes**: None — implementation accepted as-is.

**Status**: No code changes needed. Review loop terminates after one round.

## Final Status

- **Rounds run**: 1 (terminated — zero code changes accepted).
- **Findings**: 7 raised, all triaged Skip (no bugs/regressions; the two "awareness" items are deliberate, approved design choices).
- **Project checks (supervisor-run)**: `run_vulture_check` → no output; `run_lint_imports_check` → 19/19 contracts kept.
- **Acceptance criteria (issue #984)**: all 5 met —
  1. `find_exposed_mcp_tools` reader in `claude_mcp_guard.py`, unit-tested (healthy + degraded fixtures). ✅
  2. `verify` reports tools-exposed status+count; exits 1 on fatal / connected-but-0-tools; `pending` → WARN. ✅
  3. icoder banner surfaces status+count via `RuntimeInfo`. ✅
  4. `failure_handling.py` detects `McpServersUnavailableError` and names unavailable servers. ✅
  5. `alwaysLoad` hint only in the connected-but-0-tools branch; generic hint for fatal (`verify.py:586-600`). ✅
- **Outcome**: implementation accepted as-is.

