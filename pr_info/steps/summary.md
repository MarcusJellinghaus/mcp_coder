# Issue #551: Consistent MLflow Logging for All LLM-Calling Commands

## Problem

Only `prompt` and `verify` CLI commands have MLflow logging. Other LLM-calling commands (`implement`, `create-plan`, `create-pr`, `commit auto`) silently skip logging because MLflow integration is scattered across three layers with fragile coordination.

## Solution: Centralized Two-Phase Logging in `prompt_llm()`

Move MLflow logging into `prompt_llm()` so every caller gets it automatically — no explicit calls needed.

## Architectural Changes

### Before (scattered, fragile)

```
prompt command  ──→ prompt_llm() ──→ Claude provider ──→ logging_utils (starts MLflow run, logs metrics)
                                                          ↕
                 log_to_mlflow() ←─────────────────────── (closes run, adds artifacts)

create-pr       ──→ ask_llm()   ──→ prompt_llm() ──→ Claude provider ──→ logging_utils (starts run)
                                                          ↕
                 (NO log_to_mlflow call → run left orphaned or only partially logged)

LangChain path  ──→ prompt_llm() ──→ LangChain provider ──→ _log_text_mlflow / _log_agent_mlflow
                                                              (separate start/log/end cycle)
```

**Problems:** Three independent MLflow lifecycles. Only `prompt` and `verify` close runs properly. Workflows never call `log_to_mlflow()`. `ask_llm()` discards metadata.

### After (single lifecycle in `prompt_llm()`)

```
ANY caller      ──→ prompt_llm()
                     │
                     ├─ Phase 1: start/reuse MLflow run, log prompt + metadata
                     ├─ Call provider (Claude or LangChain)
                     └─ Phase 2 (finally): log response, metrics, artifacts, end run
                                           (or log error + end FAILED on exception)
```

**Result:** Single MLflow codepath. Provider-independent. Timeout-resilient (Phase 1 data survives kills). No command needs explicit MLflow calls.

## Key Design Decisions

See also [Decisions.md](./Decisions.md) for discussion-based decisions.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Logging location | Context manager in `prompt_llm()` | Automatic for all callers |
| Logging strategy | Two-phase (before + after) | Captures prompt even on timeout/kill |
| Session continuity | Reuse MLflow runs by session_id | Multi-turn conversations share one run |
| LangChain artifacts | Pass tool trace via `raw_response` | Central logger handles all artifacts |
| Provider MLflow code | Remove from both providers | Single codepath, no coordination |
| `ask_llm()` | Remove, migrate to `prompt_llm()` | Clean break, preserves metadata |
| Error handling | try/finally only, no orphan cleanup | Orphaned RUNNING runs are acceptable |

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/llm/mlflow_conversation_logger.py` | Context manager for two-phase MLflow logging (~40-60 lines) |
| `tests/llm/test_mlflow_conversation_logger.py` | Tests for the new context manager |

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/llm/interface.py` | Wire context manager into `prompt_llm()`, remove `ask_llm()` |
| `src/mcp_coder/llm/__init__.py` | Remove `ask_llm` export |
| `src/mcp_coder/__init__.py` | Remove `ask_llm` export |
| `src/mcp_coder/cli/commands/prompt.py` | Remove `log_to_mlflow()` function and all calls |
| `src/mcp_coder/cli/commands/verify.py` | Remove `log_to_mlflow` import/calls, enhance MLflow verification |
| `src/mcp_coder/llm/providers/claude/logging_utils.py` | Remove MLflow calls, keep debug logging |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Remove `_log_text_mlflow()`, `_log_agent_mlflow()`, pass tool trace via `raw_response` |
| `src/mcp_coder/workflows/create_pr/core.py` | Replace `ask_llm()` with `prompt_llm()["text"]` |
| `src/mcp_coder/workflow_utils/commit_operations.py` | Replace `ask_llm()` with `prompt_llm()["text"]` |
| `tests/llm/test_mlflow_logger.py` | Update tests affected by removed provider-level logging |
| `tests/cli/commands/test_prompt.py` | Remove tests for `log_to_mlflow()`, add tests for auto-logging |
| `tests/cli/commands/test_verify.py` | Update for enhanced MLflow verification |
| `tests/workflow_utils/test_commit_operations.py` | Update mock from `ask_llm` to `prompt_llm` |
| `tests/workflows/create_pr/test_*.py` | Update mock from `ask_llm` to `prompt_llm` |

## Implementation Steps Overview

| Step | Description | Key Change |
|------|-------------|------------|
| 1a | Update test mocks from `ask_llm` to `prompt_llm` | TDD: all tests mock `prompt_llm`, CI stays green |
| 1b | Remove `ask_llm()`, migrate production callers | Delete wrapper, callers use `prompt_llm()["text"]` |
| 2 | Create `mlflow_conversation_logger.py` | New context manager, tested in isolation |
| 3 | Wire context manager into `prompt_llm()` | All callers get auto-logging |
| 4 | Remove MLflow from Claude provider | Delete MLflow calls from `logging_utils.py` |
| 5 | Remove MLflow from LangChain provider | Delete `_log_text_mlflow`, `_log_agent_mlflow`, pass tool trace via `raw_response` |
| 6 | Remove `log_to_mlflow()` from prompt/verify commands, enhance verify | Final cleanup + enhanced verification |

**Expected net diff: more lines removed than added.**
