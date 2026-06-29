# Implementation Review Log — Issue #998

MCP guard reads init event (not last system event) + bounded retry on transient MCP startup.

Branch: `998-mcp-guard-init-event-retry`

Note: review covers committed work (commits fa65d17, 0ddd32a, 80b3433) **and** uncommitted/untracked working-tree changes:
- M `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- M `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py`
- M `tests/llm/providers/claude/test_claude_cli_stream_parsing.py`
- ?? `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py`
- ?? `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`

---

## Round 1 — 2026-06-29
**Findings**:
- (Accept) Streaming path fails fast on `pending` and does not retry like the blocking path — undocumented intentional asymmetry (`claude_code_cli_streaming.py` guard site).
- (Skip) "Missing init" treated as available (empty list) rather than unavailable — deliberate, docstring-documented tradeoff protecting the "no false positive when no MCP servers configured" criterion.
- (Skip) DRY: unavailable-server message assembly duplicated across blocking + streaming paths — low payoff, each site adds path-specific wording.
- (Skip) `tools: []` trigger not used directly — keying off `mcp_servers` statuses is more direct/correct.
- No Critical findings. pylint/mypy clean; pytest 46 target + 1012 llm tests pass. All 5 acceptance criteria met.

**Decisions**: Accept the one streaming comment (Boy Scout clarity). Skip the rest per rationale above.

**Changes**: Added a 4-line comment at the streaming MCP-guard raise site (`claude_code_cli_streaming.py`) documenting the intentional fail-fast (no bounded retry) asymmetry vs `ask_claude_code_cli`. No logic changed. format/pylint/mypy clean; pytest 4001 passed / 2 skipped.

**Status**: committing implementation (5 files) this round.

## Round 2 — 2026-06-29 (convergence)
**Findings**: No new findings (no Critical / Accept / Skip). The round-1 streaming comment accurately documents the intentional fail-fast-on-`pending` asymmetry and is locked in by `TestStreamMcpGuard.test_stream_aborts_on_pending_init`. Full extraction (`claude_mcp_guard.py` + re-exports from `claude_code_cli.py`) preserves all public names and test patch targets; guard logic is defensive and regression-tested.
**Decisions**: Nothing to change.
**Changes**: None.
**Status**: no changes needed — loop converged.

## Final Status
- Rounds run: 2 (round 1 = 1 Accept comment + committed the working-tree implementation; round 2 = zero changes, converged).
- Implementation commit: `1ebaeda` — `feat(llm/claude): extract MCP guard module and wire blocking + streaming guards (#998)`.
- Quality gates: pylint clean, mypy (strict) clean, pytest fast subset 4001 passed / 2 skipped. vulture clean. lint-imports 19/19 contracts kept.
- All 5 issue #998 acceptance criteria met (init-capture, guard pending/failed distinction, bounded retry, streaming parity, regression test).
- No Critical findings across either round. No architectural/import-contract violations.
