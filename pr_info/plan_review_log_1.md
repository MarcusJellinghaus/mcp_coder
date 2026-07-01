# Plan Review Log — Issue #984 (Surface MCP tools-exposed status in verify/icoder)

## Round 1 — 2026-07-01
**Findings** (from /plan_review):
1. (Gating) Step 1 counts `mcp__*` in the init-event `tools` list; risk that connected servers' tools are deferred behind the ToolSearch wait-bridge → a healthy session reports 0 → false `verify` exit 1 / "0 exposed" banner.
2. Step 4 names the wrong function: the re-raise belongs in `process_single_task` (above the broad `except` ~line 501), not `process_task_with_retry`.
3. Step 3 adds an extra guarded "Reply with OK" LLM round-trip on every icoder startup to obtain a tool count.
4. Step 4 is the largest step (5 production files + tests in one commit).
5. Status vocabulary inconsistent across consumers (connected/pending/failed vs connected/pending/fatal vs OK/WARN/ERR).
Verified-correct (no action): `raw_response["system"]` holds the init event; required symbols already exported; `StreamMessage` type-safe; `workflow_utils -> llm` layering allowed; no new dependencies.

**Decisions**:
1. ESCALATED → empirically verified via a live real-CLI run. RESOLVED: a connected server's `mcp__*` names DO appear in `init.tools` (3 consecutive runs). Core approach is reliable; no change to Step 1's design. Added a note so Step 1 fixtures mirror the real init-event shape.
2. ACCEPT — mechanical fix to Step 4's WHERE text (`process_single_task`, above ~line 501).
3. ESCALATED → user chose to KEEP the startup round-trip (matches acceptance item 3). No change.
4. SKIP — single logical change; defensible as one commit; no split.
5. SKIP — borderline/forward-looking for #1006; defaulted to the simpler plan.

**User decisions**:
- Tool-count source / gating risk → "Verify live first" → verified; assumption holds, plan approach unchanged.
- icoder banner cost → "Keep the startup round-trip".

**Changes**:
- step_4.md: corrected the re-raise location to `process_single_task` (above ~line 501); noted `process_task_with_retry` merely propagates it.
- step_1.md: documented the verified real init-event shape (connected → `mcp__*` present in `init.tools`; pending → only `ToolSearch`); fixtures to mirror this real shape.

**Status**: committed


## Round 2 — 2026-07-01
**Findings**: Verified the Round 1 edits landed cleanly and consistently — step_4's re-raise site is correctly `process_single_task` (above the broad `except` ~line 501), with `process_task_with_retry` (~line 561) propagating the typed error transitively (no dangling reference to it as the masking site); step_1's verified-init-event note is internally consistent with its own healthy/degraded fixtures. Source cross-checks confirm the plan is buildable as written (`McpServersUnavailableError(message, unavailable_servers)` signature + `.unavailable_servers` attr; `find_fatal_mcp_servers`/`find_unavailable_mcp_servers` present and `find_exposed_mcp_tools` the only new addition; `raw_response["system"]` populated; `StreamMessage.tools` type-safe). One minor NON-BLOCKING observation: type-annotation drift — step_1 types the reader param `StreamMessage | None` while step_2/step_3 callers pass `dict[str, Any]`; runtime-safe (a TypedDict is a dict), resolved by the standard "run mypy, fix all" convention (may need a `cast(StreamMessage, ...)` or a `Mapping[str, Any]` annotation at the verify/icoder call sites).
**Decisions**: No plan changes. Round 1 edits confirmed correct and consistent; the type-annotation item is cosmetic/self-resolving, recorded here as an implementation note rather than a plan edit (default to the simpler plan).
**User decisions**: none this round.
**Changes**: none.
**Status**: no changes needed.

## Final Status
- **Rounds run:** 2.
- **Round 1:** applied 2 plan edits — corrected step_4's re-raise location (`process_single_task`, above ~line 501) and added step_1's verified-real-init-event note + tightened fixtures. Committed as `c68713c`. Two design questions escalated to and resolved by the user: (1) init-event tool-count gating risk → "verify live first" → empirically confirmed via 3 live real-CLI runs that a connected server publishes its `mcp__*` names into `init.tools`, so the approach is reliable; (2) icoder startup "Reply with OK" round-trip → user chose to KEEP it (matches acceptance item 3).
- **Round 2:** zero plan changes; plan verified clean, consistent, and buildable.
- **Non-blocking implementation note:** at the verify + icoder call sites, `cast(StreamMessage, ...)` or a `Mapping[str, Any]` param annotation may be needed so the reader's typed param accepts a plain `dict` without a mypy `arg-type` error.
- **Outcome:** Plan is READY for approval / implementation.
