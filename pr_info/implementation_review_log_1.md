# Implementation Review Log — Issue #999

Restore the ToolSearch wait-bridge to fix the headless MCP cold-start race.
Branch: `999-restore-toolsearch-wait-bridge`.

Supervisor: technical lead delegating to engineer subagents.
Review cycles below; each round runs `/implementation_review`, triages findings,
implements accepted changes, and commits.

---

## Round 1 — 2026-06-30

**Findings** (from `/implementation_review`; implementation diff confirmed present — real source changes in `claude_mcp_guard.py`, `claude_code_cli.py`, `claude_code_cli_streaming.py` plus tests):
- Critical / Should-fix: **none**.
- Minor 1 — Stale inline comment at `claude_code_cli.py:~227` ("Disable all built-in tools…") now false since `CLAUDE_BUILTIN_TOOLS = "ToolSearch"`.
- Minor 2 — Guard double-scans `mcp_servers` (`find_fatal_mcp_servers` then `find_unavailable_mcp_servers`); correct but relies on the ordering subtlety that fatal already aborted.
- Nitpick 3 — New `test_build_cli_command_tools_is_toolsearch` duplicates coverage in `test_build_cli_command_always_includes_tools_flag`.
- Nitpick 4 — Tautological final assertion in `test_v2_never_connects_fails_clean_no_hallucination` (`assert raised_clean or sentinel not in final_text` can never fail).
- Reviewer noted strong positives: blocking/streaming parity achieved, retry machinery fully removed with no dangling refs, #998 init-capture regression preserved, unguessable-sentinel integration test is a solid acceptance proof.

**Decisions**:
- Minor 1 — **ACCEPT** (actively misleading; Boy Scout fix in an owned file).
- Minor 2 — **ACCEPT comment only**, not the shared-scanner refactor (KISS/YAGNI; cost is negligible, a one-line ordering note is the right-sized fix).
- Nitpick 3 — **SKIP** (named test documents the headline #999 acceptance criterion; duplication is cheap, don't delete intent-documenting tests).
- Nitpick 4 — **ACCEPT** (an assertion that can never fail is false confidence — a real test-quality defect).

**Changes**:
- `claude_code_cli.py` — corrected the `--tools` comment to "Keep only ToolSearch (the MCP wait-bridge); all other built-ins (Bash/Edit/Read/Write) stay disabled."; added ordering note at the `find_unavailable_mcp_servers` call site.
- `claude_code_cli_streaming.py` — same ordering note at its `find_unavailable_mcp_servers` call site.
- `test_claude_mcp_coldstart_integration.py` — removed the tautological assertion; the unconditional `sentinel not in final_text` check above is the real guarantee. Cleaned up the now write-only `raised_clean` flag (init dropped; `except` branch documents the clean-abort path) — no weakening of the test's guarantees.
- Verification: format clean; fast unit suite 4083 passed / 2 skipped, no collection errors; pylint clean; mypy clean.

**Status**: changes made — pending commit.

## Round 2 — 2026-06-30

**Findings** (fresh `/implementation_review` after round-1 fixes; implementation diff still present; unit suite 66/66 on the touched modules):
- Critical / Should-fix: **none**.
- Minor 1 — Guard still double-scans `mcp_servers` (`find_fatal_*` then `find_unavailable_*`); reviewer suggests a single `_scan_mcp_servers(tolerate_pending=False)` partition. Rated optional.
- Minor 2 — Streaming guard re-runs the scan on every `type=="system"` event, not only `init`; blocking path reads the single captured init snapshot. Reviewer: "harmless today" (later system events carry no `mcp_servers`), suggests gating on `subtype == "init"`. Low risk.
- Nitpick 1 — `test_build_cli_command_tools_is_toolsearch` duplicates `test_build_cli_command_always_includes_tools_flag`.
- Nitpick 2 — v1 integration `assert stub_status == "pending"` is a timing assumption (8s delay vs ~5s cap).
- Positives reaffirmed: real blocking/streaming parity, accurate docstrings, consistent `dict[str, str]` migration, #998 init-capture preserved, rigorous unguessable-sentinel integration design, no dead refs / debug prints.

**Decisions**:
- Minor 1 — **SKIP refactor** (already documented with the round-1 ordering comment; rewrite is optional churn on a tiny list — KISS).
- Minor 2 — **SKIP** (behavior already correct and matches blocking path; the only trigger — a later `system` event carrying `mcp_servers` — is exactly what #999 proves never happens, so it's speculative per the KB; not worth touching the core fix's streaming hot path).
- Nitpick 1 — **SKIP** (named test documents the headline acceptance criterion; cheap duplication).
- Nitpick 2 — **SKIP** (the assertion is load-bearing — v1 must fail loudly if the stub isn't `pending`, else the self-heal path goes untested; 8s-vs-5s margin is deliberate).

**Changes**: none — all findings triaged to skip with rationale.

**Status**: no changes needed. Review loop terminates (a round produced zero code changes).

---

## Final Status

- **Rounds run:** 2. Round 1 accepted 3 small fixes (stale comment, pending-scan ordering comments ×2, dead test assertion) → committed `7e001ba`. Round 2 produced zero code changes (all findings triaged to skip with rationale) → loop terminated.
- **Critical / Should-fix findings:** none across both rounds.
- **`run_vulture_check`:** clean — sole hit is `reveal_sentinel` in `tests/.../_mcp_stub_server.py`, a false positive (MCP-protocol-invoked tool, not dead code).
- **`run_lint_imports_check`:** PASSED — 19 contracts kept, 0 broken. No architecture/import-contract violations.
- **Acceptance criteria (issue #999):** all five met per the task tracker and round-1/2 reviews — `CLAUDE_BUILTIN_TOOLS = "ToolSearch"`; v1 self-heal + v2 clean-failure integration proofs; guard tolerates `pending` / aborts on `failed`; blocking == streaming; settings confirmed.

Implementation is sound and ready. CI / rebase status reported separately via `/check_branch_status`.
