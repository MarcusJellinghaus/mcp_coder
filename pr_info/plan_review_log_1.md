# Plan Review Log — Issue #598

Reviewer: Automated plan review supervisor
Date: 2026-03-27

## Round 1 — 2026-03-27

**Findings**:
- Step 6 too large — combines mechanical WorkflowFailure updates, try/finally safety net, and SIGTERM handler in one step
- Wrong step ordering — safety net (core requirement) placed last after heartbeat (nice-to-have)
- Steps 3 and 4 should be merged — Step 4 (CLI heartbeat passthrough) is trivially small
- SIGTERM handler does I/O directly inside signal handler — re-entrancy/deadlock risk
- `test_no_heartbeat_by_default` tests implementation (mocks threading) instead of behavior
- `test_run_heartbeat_logs_periodically` uses real timing — flaky on Windows CI
- `test_passes_heartbeat_params` uses fragile `or` fallback assertion style

**Decisions**:
- Accept: Split Step 6 into Step 3 (mechanical WorkflowFailure updates) + Step 4 (safety net + SIGTERM)
- Accept: Reorder steps — safety net (Steps 3-4) before heartbeat (Steps 5-6)
- Accept: Merge old Steps 3+4 into new Step 5
- Accept: Fix SIGTERM handler to set flag + sys.exit(1), let finally block do I/O
- Accept: Fix heartbeat tests to test behavior via caplog, use mock Event.wait for determinism, simplify assertions
- Skip: Windows SIGTERM behavior (handled by existing try/except)
- Skip: Missing FrozenInstanceError import in test snippet (will resolve naturally)
- Skip: CI polling test data structure (verified correct)

**User decisions**: None — all findings were straightforward improvements, no design/requirements escalation needed.

**Changes**:
- `pr_info/steps/step_3.md` — New content: mechanical update of existing WorkflowFailure constructions (was part of old Step 6)
- `pr_info/steps/step_4.md` — New content: try/finally safety net + SIGTERM handler with flag approach (was part of old Step 6)
- `pr_info/steps/step_5.md` — Merged old Steps 3+4: heartbeat in execute_subprocess + CLI passthrough, with fixed tests
- `pr_info/steps/step_6.md` — Renumbered from old Step 5: CI polling heartbeat (content unchanged)
- `pr_info/steps/summary.md` — Updated steps table, files table, and design decisions
- `pr_info/steps/Decisions.md` — Created with rationale for all three changes

**Status**: Ready to commit

## Final Status

- **Rounds run**: 1
- **Commits**: 1 (pending)
- **Plan status**: Ready for approval — all findings resolved, no open questions
