# review-implementation review log 1

## Round 1 — 2026-09-29
**Findings**:
Now the source diffs.Tests look thorough so far; checking skill-frame and wiring tests for the remaining ACs.`src/mcp_coder/icoder/permissions/skill_frame.py:132` — medium — Skill `@ref` lookups (and `use:` scenario members at `skill_frame.py:253`) return the group's matchers without the #1053 arg-predicate warning. That warning is emitted at `skill_frame.py:142-149` for a direct token. An arg-scoped group member on the `allow` side therefore grants the whole tool with no warning. Fix: run resolved members through the same arg check before returning.
`src/mcp_coder/icoder/permissions/skill_frame.py:136` — low — A group that is defined but stored as `()` (empty, cyclic, or with a broken nested ref, per `loader.py:522`) is reported to the skill author as an "unknown group reference", which misstates the cause.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/icoder/permissions/skill_frame.py, send the matchers resolved from skill `@ref` lookups (~line 132) and from `use:` scenario members (~line 253) through the same #1053 arg-predicate check used for direct tokens at lines 142-149, so an arg-scoped group member on the allow side emits the warning. Add tests covering both the `@ref` path and the `use:` path.', 'In src/mcp_coder/icoder/permissions/skill_frame.py (~line 136), report a group that is defined but resolved to an empty tuple (empty, cyclic, or with a broken nested ref, per loader.py:522) as a group that resolved to no rules, not as an unknown group reference. Add a test asserting the distinct message.'], escalate_reason=None)
**Changes**:
applied
