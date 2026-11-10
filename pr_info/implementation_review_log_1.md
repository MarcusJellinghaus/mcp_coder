# review-implementation review log 1

## Round 1 — 2026-11-10
**Findings**:
Reading `run_request`/`get_fragment` next, then the tests.`src/mcp_coder/workflows/implement/core.py:73` — low — The `checks_exhausted` message always begins "Checks still report findings after 3 fix turns". The loop also returns `cap` before three turns: when no `fix.*` fragment is usable, when the LLM returns an empty response, and when a fix turn raises an untyped exception. The failure comment then contradicts itself, e.g. "…after 3 fix turns: fix.check: no usable fragment after 0 fix turns". Use `checks.detail` as the message, since it already carries the turn count.
**Decisions**:
Verdict(decision='tasks', tasks=['At src/mcp_coder/workflows/implement/core.py:73, stop hard-coding "Checks still report findings after 3 fix turns" in the checks_exhausted message. Use checks.detail, which already includes the actual turn count, so the message stays correct when the loop returns cap early. Early returns happen when there is no usable fix.* fragment, when the LLM response is empty, or when a fix turn raises an exception. Update or add a test that checks the message for one early-cap path, such as no usable fragment after 0 turns, so it no longer claims 3 fix turns.'], escalate_reason=None)
**Changes**:
applied
