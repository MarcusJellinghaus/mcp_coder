# Plan Review Log — Issue #1043 (I2.3 Langchain enforcement gateway)

Supervised plan review. Base branch: main. Branch up to date (no rebase needed).

## Round 1 — 2026-07-30
**Findings**:
- (c1) Adapter capability-check fires too late on the iCoder path — raw TypeError beats the clear error.
- (c2) Missing interceptor-level test for skill-elevated `never` remaining callable.
- (c3) Bypass guard didn't cover site 2 (non-stream `run_agent`).
- (a1) Step 1 test collides with the langchain conftest MagicMock.
- (a2) Step 2 stamping-source micro-change needs a canonical-name regression test.
- (a3) Step 4 `stream()` docstring still describes old `permission_warning` behavior.
- (b1) `permission_warning` path deleted → malformed skill tokens silently dropped (visible behavior removal).
- (b2/FYI) With `enforce_skill_tools=False`, any skill declaration elevates a config `never` to ALWAYS — intended frame-first model (D5 + AC), noted for awareness.
**Decisions**: Accept c1, c2, c3, a1, a2, a3 as straightforward improvements. Skip a4 (split build_legacy_frame/bridge — small/cohesive). b2 treated as decided (frame-first by design).
**User decisions**: Q on malformed-token warning → user chose **B (preserve a warning)**: `build_legacy_frame` collects parse failures, gateway surfaces them (slimmed `permission_warning` / WARNING log), with a test.
**Changes**:
- `pr_info/steps/step_1.md` (c1, a1): extracted the capability assertion into a reusable
  `_assert_tool_interceptors_supported()` helper (so Step 5 can call it early); guarded the
  `inspect.signature` call with try/except so the conftest `MagicMock` stand-in is skipped, not
  misread; moved the real-install pass-test onto the `langchain_integration` marker and added a
  unit test for the mock-skip path.
- `pr_info/steps/step_2.md` (a2): added `test_connect_and_discover_stamps_canonical_name` regression
  test asserting `metadata["mcp_canonical_name"]` is unchanged (`mcp__{server}__{lc_tool.name}`) after
  the stamping-source micro-change in the unified helper.
- `pr_info/steps/step_3.md` (b1, c2): `build_legacy_frame` now returns `(frame, warnings)` and
  **collects** per-token parse failures (fail-closed, not silently dropped); added a frame-builder
  test for the malformed-token case and a call-level interceptor test proving a skill-elevated `never`
  stays CALLABLE (interceptor awaits the real handler); updated ALGORITHM/DATA/LLM-prompt accordingly.
- `pr_info/steps/step_4.md` (b1, a3): **repurposed** (not deleted) the `permission_warning` emission
  to surface the malformed-token warnings from `build_legacy_frame` — kept the `ui/app.py` render
  branch and the two render tests (`test_app_core.py`, `test_app_pilot.py`); added a
  `stream()`-emits-warning test; added a docstring Boy-Scout note to rewrite `stream()`'s docstring to
  the new warning behavior; updated WHERE/ALGORITHM/Checks/LLM-prompt.
- `pr_info/steps/step_5.md` (c1, c3): added an early `_assert_tool_interceptors_supported()` call at
  the top of the langchain branch (before `MCPManager`) with an ordering test; added a site-2
  stream-only bypass-guard test (`run_agent` never reached from iCoder) alongside the existing site-3
  guard; updated WHAT/HOW/ALGORITHM/intro/LLM-prompt.
- `pr_info/steps/summary.md`: updated D3 + KISS #4 (reusable early-called guarded helper); added a
  "USER DECISION — malformed skill tokens keep a warning" note; retargeted the llm_service.py /
  icoder.py / agent.py entries in Files-modified; marked the two `permission_warning` render tests as
  kept; updated the Step-5 step-plan line and the requirements-traceability list.
**Status**: committed
