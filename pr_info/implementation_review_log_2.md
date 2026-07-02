# Implementation Review Log — Run 2

Issue #984 — Surface MCP tools-exposed status in verify, icoder, and failure output.

Supervised implementation review. Each round: `/implementation_review` → triage → implement accepted → commit → `/check_branch_status`. Loop until a round produces zero code changes.

Run 1 (see `implementation_review_log_1.md`) terminated after one round with zero code changes; all 5 acceptance criteria met. This run re-verifies against the current branch state.

## Round 1 — 2026-07-02

**Findings** (from `/implementation_review` engineer subagent):
1. `verify.py:594` — `pending` classified before the `not tools` check, so a pending server with 0 tools reports WARN not FAIL.
2. `env_setup._probe_exposed_mcp_tools` sends an extra `"Reply with OK"` prompt at icoder startup (a second LLM round-trip on launch).
3. `task_processing.py:507` re-raises `McpServersUnavailableError`; propagation through `implement/core.py` safety-net.
4. `# TODO: narrow exception type` visible in the diff.
5. `find_exposed_mcp_tools` defensive handling (None, str/dict entries, `mcp__` filter, dedup+sort) — noted positive.
6. `print()` in `verify.py` is the command's established output mechanism — noted positive.

**Decisions**: All **Skip**.
- 1: intentional and documented — `pending` never fails the build; mirrors the runtime guard (#999/#1005 cold-start tolerance). Not a bug.
- 2: deliberate, approved in `summary.md` icoder startup tradeoff; fully guarded (degrades to `(None, None)`, never blocks launch).
- 3: verified correct — outer `except Exception` captures into `caught_exception`, `finally` safety-net formats the message. Wiring sound.
- 4: pre-existing context, not introduced by this change — out of scope.
- 5,6: positives, no action.

**Verification**: engineer confirmed a real production diff across all 4 steps; 180 targeted tests pass; mypy strict clean; pylint clean. No Critical/bugs/regressions.

**Changes**: None — implementation accepted as-is.

**Status**: No code changes needed. Review loop terminates after one round.

## Final Status

- **Rounds run**: 1 (terminated — zero code changes accepted).
- **Findings**: 6 raised (4 review items + 2 positives), all triaged Skip. No bugs/regressions; the two "awareness" items (pending-before-0-tools ordering, icoder startup round-trip) are deliberate, documented design choices.
- **Project checks (supervisor-run)**: `run_vulture_check` → no output; `run_lint_imports_check` → 19/19 contracts kept.
- **Acceptance criteria (issue #984)**: all 5 met (unchanged since run 1) —
  1. `find_exposed_mcp_tools` reader in `claude_mcp_guard.py`, unit-tested. ✅
  2. `verify` reports tools-exposed status+count; exits 1 on fatal / connected-but-0-tools; `pending` → WARN. ✅
  3. icoder banner surfaces status+count via `RuntimeInfo`. ✅
  4. `failure_handling.py` detects `McpServersUnavailableError` and names unavailable servers. ✅
  5. `alwaysLoad` hint only in the connected-but-0-tools branch; generic hint for fatal. ✅
- **Outcome**: implementation accepted as-is. Consistent with run 1.
