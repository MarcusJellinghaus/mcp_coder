# review-implementation review log 1

## Round 1 — 2026-09-29
**Findings**:
Now the source diffs.Tests look thorough so far; checking skill-frame and wiring tests for the remaining ACs.`src/mcp_coder/icoder/permissions/skill_frame.py:132` — medium — Skill `@ref` lookups (and `use:` scenario members at `skill_frame.py:253`) return the group's matchers without the #1053 arg-predicate warning. That warning is emitted at `skill_frame.py:142-149` for a direct token. An arg-scoped group member on the `allow` side therefore grants the whole tool with no warning. Fix: run resolved members through the same arg check before returning.
`src/mcp_coder/icoder/permissions/skill_frame.py:136` — low — A group that is defined but stored as `()` (empty, cyclic, or with a broken nested ref, per `loader.py:522`) is reported to the skill author as an "unknown group reference", which misstates the cause.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/icoder/permissions/skill_frame.py, send the matchers resolved from skill `@ref` lookups (~line 132) and from `use:` scenario members (~line 253) through the same #1053 arg-predicate check used for direct tokens at lines 142-149, so an arg-scoped group member on the allow side emits the warning. Add tests covering both the `@ref` path and the `use:` path.', 'In src/mcp_coder/icoder/permissions/skill_frame.py (~line 136), report a group that is defined but resolved to an empty tuple (empty, cyclic, or with a broken nested ref, per loader.py:522) as a group that resolved to no rules, not as an unknown group reference. Add a test asserting the distinct message.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-09-29
**Findings**:
Reviewing the source diff; now checking side effects of the D9 hoist and other `matched_rule.matcher` readers.`src/mcp_coder/cli/commands/icoder.py:110` — medium — Moving the config load out of the langchain-only branch (D9) also moves `emit_schema` (`loader.py:493`) there. That call is not guarded: if `.icoder/` exists but is not writable, the `write_text` at `loader.py:216` raises an `OSError` that now aborts iCoder startup under the Claude provider too. Before this change, only langchain+MCP sessions could hit it. This goes against the loader's own rule that a bad layer must degrade, not abort startup (`loader.py:364-365`). Fix: catch and log the `OSError` inside `emit_schema`, and add a test for it.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/icoder/permissions/loader.py, make `emit_schema` (~line 493) catch `OSError` from the `write_text` at ~line 216 and log it instead of raising, so a non-writable `.icoder/` no longer aborts iCoder startup under any provider now that the config load is hoisted in src/mcp_coder/cli/commands/icoder.py:110. Add a test that forces `write_text` to raise `OSError` and asserts that loading still succeeds and the error is logged.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-09-29
**Findings**:
Now the source diff.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
rebase-needed
**Escalate reason**: rebase
