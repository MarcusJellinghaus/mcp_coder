# Plan Review Log — Issue #1081 (Run 2)

Fix leaked coroutines in langchain provider sync-path tests.

Plan: 3 steps (1 production hardening + 2 test-only). No steps implemented yet (TASK_TRACKER unpopulated). Branch up to date with `origin/main` (no rebase needed). Run 1 concluded the plan was ready for approval with zero changes; this run re-verifies independently.

## Round 1 — 2026-07-23

**Findings** (from `/plan_review` engineer subagent, all verified against the actual current source/tests, not just plan text):
- Step 1 production site: `__init__.py:503` is exactly `threading.Thread(target=asyncio.run, args=(_run(),), daemon=True)`; `_run()` block at 483–501, `thread.start()` at 504. Lazy named-target placement is correct and minimal.
- Patch target `{_MOD}.agent.run_agent` (Steps 2 & 3) is the only live seam — `_ask_agent` imports `run_agent` locally at call time (`__init__.py:393`); `{_MOD}.run_agent` would not exist. Mirrors existing `{_MOD}.agent._check_agent_dependencies` patches and reference idiom `test_langchain_agent_mode.py:42`. `_MOD` confirmed in both test files.
- `run_agent` (`agent.py:236`) and `run_agent_stream` (`agent.py:391`) are both `async def` → `AsyncMock` correct.
- All 4 non-stream sites covered: `test_langchain_provider.py:509/530/567` → Step 2; `test_langchain_provider_system_messages.py:215` → Step 3. Stream site → Step 1 production change.
- Step 3 strengthened assertion verified: `_build_system_messages` (`__init__.py:64-68`) yields `[SystemMessage("sys"), SystemMessage("proj")]`; passed as `system_messages=` kwarg (`__init__.py:412`); `call_args.kwargs["system_messages"]` `.content == ["sys","proj"]` is correct. Replaces weak `assert mock_run.called` (line 233).
- Step 1 "no test change" claim correct: with lazy target, `_run()` never constructed under the no-op `Thread` patch (`test_langchain_agent_timeout.py:39`); test still times out and passes unchanged.
- Imports accurate: both target test files import `MagicMock, patch` (no `AsyncMock`), matching the "add `AsyncMock`" instruction.
- Scoping correct: 3 steps, one commit each (Step 2 keeps 3 sibling error-path tests together — not over-split). No "verify everything" / "fix all issues" steps.
- NITPICK: soft line-reference drift between issue/plan prose and actual patch lines (all land on the correct constructs).
- DESIGN-QUESTION: no CI-enforced regression guard for "0 warnings" (already an accepted tradeoff in issue Decisions).

**Decisions**:
- Line-reference drift: **skip** — non-load-bearing per software_engineering_principles.md; all point at correct code.
- No regression guard: **skip / no escalation** — explicitly decided in issue Decisions table (accepted tradeoff); not re-litigating.

**User decisions**: None required — no open design or requirements questions.

**Changes**: None. Plan independently re-verified accurate and complete; no edits needed.

**Status**: No changes needed.

## Final Status

Rounds run: 1. Plan changes: 0. Run 2 independently re-verified the plan against the current codebase and confirms Run 1's conclusion. All patch targets, imports, line references, scoping, and the strengthened Step 3 assertion check out. No CRITICAL findings, no missing steps, no open questions. **Plan is ready for approval.**
