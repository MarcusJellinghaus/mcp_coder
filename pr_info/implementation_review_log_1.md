# Implementation Review Log 1 — Issue #586

**Feature:** Streaming Output for LangChain and Claude CLI Providers
**Date:** 2026-03-26

## Round 1 — 2026-03-26

**Findings:**
- C1 (Critical): `_ask_text_stream` silently swallows non-auth/non-connection errors — missing 404/model-not-found handling
- C2 (Critical): `stream_subprocess` reads stderr only after stdout exhausted — pipe-buffer deadlock risk
- C3 (Low): Validation inconsistency between streaming/non-streaming for empty question
- S1 (Medium): MLflow logging missing in streaming path of `execute_prompt`
- S2 (Low): Provider-dependent `json-raw` format differences
- S3 (Low): `ResponseAssembler` accumulates all raw events in memory
- S4 (Low): `StreamResult.__next__` edge case with None return
- S5 (Low): No test for empty question validation in `ask_claude_code_cli_stream`
- S6 (Low): `logs_dir` parameter not plumbed through from `prompt_llm_stream`

**Decisions:**
- C1: Accept — real bug, streaming path loses 404 handling
- C2: Accept — real deadlock risk, `execute_subprocess` uses `communicate()` but streaming doesn't
- C3: Skip — low impact, both paths reject bad input
- S1: Accept — step 7 was supposed to add this
- S2: Skip — by design per issue decision #9
- S3: Skip — speculative, low impact
- S4: Skip — speculative, only affects misuse
- S5: Accept — small Boy Scout fix
- S6: Skip — pre-existing, consistent with non-streaming path

**Changes:**
- `src/mcp_coder/llm/providers/langchain/__init__.py`: Re-raise non-auth errors with 404/model-not-found handling
- `src/mcp_coder/utils/subprocess_streaming.py`: Read stderr in background thread
- `src/mcp_coder/cli/commands/prompt.py`: Add MLflow logging to streaming path
- `tests/llm/providers/claude/test_claude_code_cli.py`: Add empty question validation test
- `tests/llm/providers/langchain/test_langchain_streaming.py`: Update error test to expect re-raise

**Status:** Committed as `ab0c452`

## Round 2 — 2026-03-26

**Findings:**
- F1 (Info): Generator yield-then-raise is subtle but correct
- F2 (Low): Redundant 404 check pattern (pre-existing)
- F3 (Medium): No error handling for log file open failure in `ask_claude_code_cli_stream`
- F4 (Info): Exception propagation in `StreamResult.__next__` is correct
- F5 (Info): `finally` block correctly cleans up on `GeneratorExit`
- F6 (Low): No test for MLflow logging in streaming path
- F7 (Info): Docstring correctly describes responsibility delegation
- F8 (Medium): `ResponseAssembler` stores duplicate raw_line events

**Decisions:**
- F1: Skip — correct behavior
- F2: Skip — pre-existing pattern
- F3: Accept — robustness gap vs non-streaming path
- F4: Skip — correct
- F5: Skip — correct
- F6: Accept — test coverage gap for S1 fix
- F7: Skip — correct
- F8: Skip — speculative, raw events useful for debugging

**Changes:**
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py`: Wrap log file open in try/except, fallback to os.devnull
- `tests/cli/commands/test_prompt_streaming.py`: Add MLflow streaming test

**Status:** Committed as `5cf5396`

## Round 3 — 2026-03-26

**Findings:** None — all previous fixes verified correct, no new actionable issues found.

**Status:** No changes needed

## Final Status

- **Rounds:** 3
- **Commits:** 2 (`ab0c452`, `5cf5396`)
- **All code quality checks pass:** pylint, pytest (2773 tests), mypy, ruff
- **CI:** Green
- **Rebase needed:** Yes — branch is behind `origin/main`
