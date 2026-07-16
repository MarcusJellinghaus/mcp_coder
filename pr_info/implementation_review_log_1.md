# Implementation Review Log — Issue #1039 (Run 1)

**Issue:** I1.1 — Enforce a skill's declared tool set in the langchain provider
**Branch:** 1039-i1-1-enforce-a-skill-s-declared-tool-set-in-the-langchain-provider
**Supervisor:** technical lead (delegating to engineer subagents)

Enforcement mechanism only (opt-in, `enforce_skill_tools=False` default). No skill-file edits
(deferred to #1062). All tests use purpose-built fixtures, not repo skills.

---

## Round 1 — 2026-07-16
**Findings** (from `/implementation_review`):
- Quality checks all PASS: pylint (clean), mypy (clean), pytest unit (4251 passed, 2 skipped, 0 failed).
- All acceptance criteria met and tested against purpose-built fixtures (no repo skills): subset narrowing, absent/empty→full set, all-non-MCP→zero MCP tools, host-side pre-`create_react_agent`, canonical bare-vs-`mcp__server__tool` resolution, same-bare-name disambiguation, wildcard/`@group`/arg-scoped→restricted+warning, cache-not-mutated, pure-filter unit tests, seam-level proof via `FakeLLMService`/captured `tools=`. Warning surfaces to both event log and TUI.
- Nitpick 1: malformed exact token (e.g. `mcp__srv`, no third segment) enters allow-set but matches nothing.
- Nitpick 2: generic warning text (token interpolated) identical for wildcard/`@group`/arg-scoped.
- Minor 3: `_connect_and_discover` assigns `lc_tool.metadata`; relies on Pydantic mutable field (unit-tested; live integration out of scope per issue decision).

**Decisions**:
- Nitpick 1 — **Skip**. Fail-closed by construction (can never widen the set), matches documented exact-token contract. Speculative (KISS/YAGNI).
- Nitpick 2 — **Skip**. Token is interpolated so message stays actionable; richer per-category messaging is explicitly I2.1/I4.1 scope (out of scope for I1.1).
- Minor 3 — **Skip**. Merge-preserve semantics unit-tested; live `langchain_integration` fixture explicitly avoided by the issue's stated decision. No action.

**Changes**: None — zero substantive findings; no code changed this round.
**Status**: No changes needed.

---

## Final Status
- **Rounds run**: 1 (zero code changes — loop terminated immediately).
- **pylint / mypy / pytest (unit)**: PASS (4251 passed, 2 skipped).
- **vulture**: clean (no output).
- **lint-imports**: PASS (19 contracts kept, 0 broken).
- **Findings**: 3 nitpick/minor observations, all Skipped (fail-closed-by-construction, out-of-scope for I1.1, or already unit-tested). No code changes recommended before merge.
- **Verdict**: Implementation faithfully closes the #755 langchain enforcement gap; ships opt-in (`enforce_skill_tools=False`), never mutates the shared MCP cache, enforces host-side before `create_react_agent`. Ready for PR review.
