# Issue #342 – implement command: improve logging

## Summary

The `implement` command currently logs conversations to `pr_info/.conversations/` as markdown and JSON files. This directory is no longer needed. The goal is to remove it and instead log structured session JSON files to `.mcp-coder/implement_sessions/`, mirroring exactly what `create_plan` already does via `store_session()`.

---

## Architectural / Design Changes

### Before

```
ask_llm()   → ask_claude_code()  → ask_claude_code_cli/api() → returns str (strips text twice)
prompt_llm()                     → ask_claude_code_cli/api() → returns LLMResponseDict

implement workflow:
  _call_llm_with_comprehensive_capture() → ask_llm() or ask_claude_code_api_detailed_sync()
  save_conversation() / save_conversation_comprehensive() → pr_info/.conversations/

create_plan:
  prompt_llm() → manually wraps into dict → store_session() → .mcp-coder/create_plan_sessions/

prompt.py verbose/raw:
  ask_claude_code_api_detailed_sync() → store_session() with manually wrapped dict
```

### After

```
ask_llm()   → prompt_llm()["text"]       (thin wrapper, one stripping layer)
prompt_llm()                     → ask_claude_code_cli/api() → returns LLMResponseDict

implement workflow:
  prompt_llm() → store_session(LLMResponseDict) → .mcp-coder/implement_sessions/
  (no save_conversation, no .conversations/)

create_plan:
  prompt_llm() → store_session(LLMResponseDict directly) → .mcp-coder/create_plan_sessions/

prompt.py verbose/raw:
  prompt_llm() → store_session(LLMResponseDict directly)
  formatters receive raw_response sub-dict (unchanged interface)
```

### Key Principles

- **DRY**: `ask_llm()` reuses `prompt_llm()`. `store_session()` used everywhere — no duplicate storage logic.
- **KISS**: All changes are deletions of dead code or additive optional params. No structural rewrites.
- **Clean**: `TimeoutExpired` handling centralised in `prompt_llm()`. One LLM call layer, one text-stripping point.

---

## Step Name Convention (for `store_session()` `step_name` param)

| Workflow step                    | `step_name`        |
|----------------------------------|--------------------|
| Main task implementation (step N) | `step_N`           |
| Mypy fix (step N, attempt M)     | `step_N_mypy_M`    |
| CI failure analysis (attempt M)  | `ci_analysis_M`    |
| CI fix (attempt M)               | `ci_fix_M`         |
| Task tracker preparation         | `task_tracker`     |
| Finalisation                     | `finalisation`     |

---

## Files Modified or Deleted

| File | Change |
|------|--------|
| `src/mcp_coder/llm/storage/session_storage.py` | Accept `LLMResponseDict` directly; add `step_name`, `branch_name` params; new filename format; update `extract_session_id()` |
| `src/mcp_coder/llm/interface.py` | Rewrite `ask_llm()` as thin wrapper; add `TimeoutExpired` handling to `prompt_llm()` |
| `src/mcp_coder/llm/providers/claude/claude_code_interface.py` | **Delete** (dead code) |
| `src/mcp_coder/workflows/implement/constants.py` | Remove `CONVERSATIONS_DIR` |
| `src/mcp_coder/workflows/implement/task_processing.py` | Remove `save_conversation`, `save_conversation_comprehensive`, `_call_llm_with_comprehensive_capture`; switch to `prompt_llm()` + `store_session()` |
| `src/mcp_coder/workflows/implement/core.py` | Remove `save_conversation` calls; switch `ask_llm()` to `prompt_llm()` + `store_session()` |
| `src/mcp_coder/workflows/create_plan.py` | Remove `.conversations/` dir creation; pass `LLMResponseDict` directly to `store_session()` |
| `src/mcp_coder/cli/commands/prompt.py` | verbose/raw: switch to `prompt_llm()`; pass `LLMResponseDict` to `store_session()`; just-text: same. **Behaviour change**: verbose/raw mode previously forced API method internally; now respects `--llm-method` (default: `claude:api`). Users relying on implicit API behaviour should pass `--llm-method claude:api` explicitly. |
| `tests/llm/storage/test_session_storage.py` | Add tests for new params, new format, updated `extract_session_id()` |
| `tests/llm/providers/claude/test_claude_code_interface.py` | **Delete** (module deleted) |
| `tests/llm/test_interface.py` | Update mocks: `ask_claude_code` → `ask_claude_code_cli/api` |
| `tests/workflows/implement/test_task_processing.py` | Remove tests for deleted functions; update mocks |
| `tests/workflows/create_plan/test_prompt_execution.py` | Update `store_session()` call expectations |
| `tests/cli/commands/test_prompt.py` | Update verbose/raw mocks; update `store_session()` calls |

### Files NOT changed (simplification)
- `src/mcp_coder/llm/formatting/formatters.py` — formatters receive `raw_response` sub-dict, same shape as before
- `tests/llm/formatting/test_formatters.py` — formatter signatures unchanged

---

## Implementation Steps Overview

| Step | Description |
|------|-------------|
| 1 | Extend `store_session()` — accept `LLMResponseDict`, add `step_name`/`branch_name`, update `extract_session_id()` |
| 2 | Simplify LLM interface — rewrite `ask_llm()` as thin wrapper, centralise `TimeoutExpired` in `prompt_llm()`, delete `claude_code_interface.py` |
| 3 | Remove `pr_info/.conversations/` logging — delete `save_conversation`, `save_conversation_comprehensive`, `CONVERSATIONS_DIR`, `_call_llm_with_comprehensive_capture` |
| 4 | Switch `implement` workflow to `prompt_llm()` + `store_session()` in `task_processing.py` |
| 5 | Switch `implement` workflow to `prompt_llm()` + `store_session()` in `core.py` |
| 6 | Update `create_plan.py` and `prompt.py` to pass `LLMResponseDict` directly to `store_session()` |
