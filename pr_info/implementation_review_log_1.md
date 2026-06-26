# Implementation Review Log — Issue #995

Branch: `995-mcp-venv-path-tool-env`
Scope: Fix MCP server path resolution (env.py tool-env vs VIRTUAL_ENV) + fail-fast on unavailable MCP servers (claude_code_cli.py).

## Round 1 — 2026-06-26
**Findings** (from `/implementation_review`):
- Fix 1 (env.py tool-env resolution) and Fix 2 (fail-fast MCP guard) correctly implement #995; all 4 acceptance criteria met; 48 unit tests pass. No merge blockers.
- [Accept] Fail-fast guard exists only on the non-streaming path (`ask_claude_code_cli`); the parallel streaming path (`ask_claude_code_cli_stream`) parses the same init event but has no guard — a headless streaming caller could run blind.
- [Skip] Workflow-level `mcp_unavailable` classification not wired — AC3 only requires aborting with a clear typed error (`McpServersUnavailableError`), which is satisfied; issue framed this as optional.
- [Skip] Guard keys off server `status != connected` rather than `tools == []` — the status-based check is the more precise cause-based signal and correctly leaves legitimate no-MCP sessions alone.
- [Skip] Preset `MCP_CODER_VENV_PATH` not existence-validated — speculative hardening (YAGNI); a bad path is caught downstream by Fix 2.

**Decisions**:
- Accept the streaming-path guard (consistency / safety net; same Fix 2, parallel path; bounded effort).
- Skip the other three (out of bounded scope / working as intended / speculative).

**Changes**:
- `claude_code_cli_streaming.py`: imported existing `McpServersUnavailableError` + `find_unavailable_mcp_servers` (DRY), added the guard on the init/system event in `ask_claude_code_cli_stream` — raises before yielding any assistant content; zero-server streams unaffected.
- `test_claude_cli_stream_parsing.py`: added `TestMcpServerGuardInStream` (raises on non-connected configured server; does not raise for zero-server stream).
- pylint / pytest (3991 passed, 2 skipped) / mypy: all pass.

**Status**: committed (see commit below).

## Round 2 — 2026-06-26
**Findings**: Reviewed the streaming-guard commit (`edfd07e`). Guard raises before any assistant content is yielded; detection identical to the non-streaming path (same `find_unavailable_mcp_servers` + byte-identical error message); no-MCP (zero-server) streams unaffected; tests behavior-focused with realistic NDJSON, covering both raise and no-raise. Branch diff (`main...HEAD`, 6 files) coherent with #995. No Critical or Accept-level findings.
**Decisions**: Accept as-is. No changes needed.
**Changes**: None.
**Status**: no changes needed — review loop converged.

## Final Status
- **Rounds run**: 2 (round 1 accepted 1 change; round 2 clean → loop converged).
- **Code changes**: 1 commit — `edfd07e` fix(llm/claude): fail fast in streaming path when MCP servers aren't connected (#995). Mirrored the non-streaming MCP-unavailable guard into `ask_claude_code_cli_stream`, reusing the existing error type + helper, with tests.
- **Acceptance criteria**: all 4 met (tool-env resolution ignores VIRTUAL_ENV + unit test; fail-fast abort on non-connected MCP server, now on both streaming and non-streaming paths; docs updated).
- **Skipped findings**: workflow `mcp_unavailable` classification (optional, AC met by typed error); `tools == []` direct check (status-based check is more precise); preset `MCP_CODER_VENV_PATH` existence validation (speculative/YAGNI).
- **Quality gates**: pylint, pytest (3991 passed / 2 skipped), mypy — all pass. vulture: no output. lint-imports: 19 contracts kept, 0 broken.
