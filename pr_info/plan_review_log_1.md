# Plan Review Log — Issue #1081 (Run 1)

Fix leaked coroutines in langchain provider sync-path tests.

Plan: 3 steps (1 production hardening + 2 test-only). No steps yet implemented (TASK_TRACKER unpopulated). Branch current with main.

## Round 1 — 2026-07-23

**Findings** (from `/plan_review` engineer subagent, all verified against actual source/tests):
- Production site (Step 1): `__init__.py:503` matches the plan exactly; `_run()` block at 483-501, replacement placement correct and minimal.
- Patch target `{_MOD}.agent.run_agent` (Steps 2 & 3) is the only live seam — `_ask_agent` imports `run_agent` locally at call time (`__init__.py:393`). Confirmed against existing `agent._check_agent_dependencies` patches and reference pattern in `test_langchain_agent_mode.py:42`.
- `run_agent` / `run_agent_stream` are both `async def` → `AsyncMock` is correct.
- All 4 non-stream sites covered: 3 error-path (`test_langchain_provider.py:509/530/567`) → Step 2; system-messages (`test_langchain_provider_system_messages.py:215`) → Step 3.
- Step 3 assertion chain verified: `ask_langchain` → `_build_system_messages` → `[SystemMessage("sys"), SystemMessage("proj")]` → `run_agent(system_messages=...)` keyword. `call_args.kwargs["system_messages"]` `.content == ["sys","proj"]` is correct.
- Timeout test unchanged claim correct: lazy target means `_run()` never constructed under the no-op `Thread` patch.
- NITPICK: soft line-reference drift between issue/plan text (all land on correct constructs).
- IMPROVEMENT: TASK_TRACKER has no task rows (expected — populated at implementation step 0).
- DESIGN-QUESTION: no automated regression guard (already an accepted tradeoff in issue Decisions).

**Decisions**:
- Line-reference nitpicks: **skip** — line numbers aren't load-bearing (per software_engineering_principles.md) and all point at correct code.
- Empty TASK_TRACKER: **skip** — intentional per planning_principles.md.
- No regression guard: **skip / no escalation** — explicitly decided in issue Decisions table (accepted tradeoff); not re-litigating.

**User decisions**: None required — no open design or requirements questions.

**Changes**: None. Plan verified accurate and complete; no edits needed.

**Status**: No changes needed.

## Final Status

Rounds run: 1. Plan changes: 0. The plan is accurate, complete, and correctly decomposed (3 steps, one commit each: 1 production hardening + 2 test-only). All patch targets, imports, line references, and the strengthened Step 3 assertion were verified against the actual codebase. No CRITICAL findings, no missing steps, no open questions. **Plan is ready for approval.**
