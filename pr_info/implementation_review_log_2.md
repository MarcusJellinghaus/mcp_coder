# review-implementation review log 2

Issue: #1116 — LangChain backend: icoder multiple-system-message bug + path convergence
Branch: `1116-langchain-backend-icoder-multiple-system-message-bug-path-convergence`
Started: 2026-08-19 (continues `implementation_review_log_1.md`, which ended after round 3 with a rebase escalation)

## Round 1 — 2026-08-19

**Findings**:
- Diff confirmed real: 30 files (+3982/−423). `_messages.py` added; `agent.py` rewritten (`_summarize_messages` extracted, `run_agent` collapsed to a drainer, graph-final-messages via root `run_id`, single storage site, flatten NOTE deleted); `__init__.py` converged (merged `SystemMessage`, both text paths on the shared helpers, `_strip_internal_done_keys` boundary strip, `_ask_agent` no longer stores); 11 test files + 2 doc files.
- Rounds 1–3 of log 1 verified as applied (missing-terminal-event warning `agent.py:678`; `_summarize_messages` docstring + dead usage loop removed; stats omitted rather than zeroed on the no-terminal path; `DOC502` per-file ignore reverted for the targeted `# noqa` at `agent.py:443`).
- **No critical or medium findings.** Two low:
  - `src/mcp_coder/llm/providers/langchain/_messages.py:45` — low — contract asymmetry: `serialize_messages` preserves *non-leading* `SystemMessage`s (pinned by `test_serialize_keeps_non_leading_system_message`) while `assemble_messages` drops **every** system entry from loaded history, so a stored mid-conversation system could never be replayed. Inert today — nothing produces mid-conversation systems.
  - `src/mcp_coder/llm/providers/langchain/agent.py:333` — low, pre-existing — `_summarize_messages` derives `agent_steps`/`total_tool_calls`/`tool_trace` from the graph's *whole* final message list, which on turn N includes reloaded prior turns, so `raw_response` stats accumulate across a session. Not a regression: the old `run_agent` computed identically from `ainvoke`'s full state.
- Explicitly checked and correct: merge safety (only two `_build_system_messages` call sites, no production consumer expects two messages); no double-store; boundary strip covers every `done` event reaching consumers while `result` is correctly retained for `ResponseAssembler`'s no-delta fallback; downstream consumers use `.get()`; no unused imports or dead accumulators in `agent.py`; cancel/error cannot reach `_store_history` (`CancelledError`/`GeneratorExit` are `BaseException`).

**Decisions**:
- `_messages.py:45` asymmetry — **Skip**. It is an explicit documented design decision (`pr_info/steps/summary.md` §1: "Note the asymmetry, and keep it") and inert in the current codebase. Acting on it would only matter if a future change starts storing mid-conversation systems — speculative (KB: *Code Review Scope*).
- `agent.py:333` stats span — **Skip**. Explicitly pre-existing and not a regression; out of review scope (KB: *Pre-existing issues are out of scope*). Worth a separate issue if the accumulating `tool_trace` matters for MLflow reporting.

**Changes**: none — both findings skipped.

**Status**: no changes needed.

## Final Status

Review loop closed after one round with zero code changes.

Verification actually executed this round (the environment breakage that blocked rounds 1–3 of log 1 is gone):

| Check | Result |
|---|---|
| pytest (`-n auto`, integration markers deselected) | 4931 passed, 2 skipped (4933 collected) |
| mypy | clean |
| ruff | clean |
| pylint | clean |
| file-size gate (750 lines) | passed, 814 files |
| vulture | no output |
| lint-imports | PASSED — 21 contracts kept, 0 broken |

**Outstanding, unverified (not fixable here):** the two `langchain_integration` gates this branch added — `test_agent_stream_two_turns_store_system_free_history` (the only real-LangGraph check of the root-`run_id` terminal-event assumption) and the non-empty `raw_response["usage"]` assertion in `test_agent_simple_prompt` — were not executed; no endpoint is configured. The acceptance criteria's manual LiteLLM/Qwen checks (`prompt --add-system-prompts`, a 2+ turn icoder session) were likewise not performed. The root-`run_id` mechanism is therefore proven only against hand-built `graph_events()` fixtures. A skip is not a pass; this was dismissed in log 1 round 3 as unfixable without an endpoint and is recorded here as a known gap, not a resolved item.
