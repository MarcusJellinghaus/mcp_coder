# Fix #593: MLflow parameter conflict when logging multiple prompts in same run

## Problem

When workflows execute multiple `prompt_llm()` calls with session continuation,
the shared `session_id` causes `mlflow_conversation` to resume the same MLflow run.
On prompts 2+, `log_conversation()` re-logs params (`prompt_length`, `step_name`,
`branch_name`) with different values, which MLflow rejects (params are immutable).

## Design Change

**One MLflow run per conversation**, with per-step artifacts and metrics:

| Data | Before (broken) | After (fixed) |
|------|-----------------|---------------|
| `model`, `provider`, `working_directory` | Params (every call) | Params (step 0 only) |
| `prompt_length`, `duration_ms`, `cost_usd`, usage | Params/Metrics (no step) | Metrics with `step=N` |
| `branch_name`, `step_name` + all values | Params (every call → conflict) | Per-step JSON artifact (`step_N_all_params.json`) |
| Prompt text | `prompt.txt` (overwritten) | `step_N_prompt.txt` |
| Conversation JSON | `conversation.json` (overwritten) | `step_N_conversation.json` |

## Architectural Change

A single `_run_step_count: dict[str, int]` on `MLflowLogger` tracks the step index
per `run_id`. A `current_step()` method exposes it. Both `log_conversation()` and
`log_conversation_artifacts()` use step-aware logging. The context manager reads
`current_step()` for Phase 1 prompt artifact naming.

No new classes, no new modules, no signature changes to the context manager.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/mlflow_logger.py` | Add `_run_step_count` dict, `current_step()` method, `step` param on `log_metrics()`, rewrite `log_conversation()` and `log_conversation_artifacts()` |
| `src/mcp_coder/llm/mlflow_conversation_logger.py` | Use `current_step()` for step-prefixed Phase 1 prompt artifact |
| `tests/llm/test_mlflow_logger.py` | Update existing tests, add multi-step tests |
| `tests/llm/test_mlflow_conversation_logger.py` | Update artifact name assertions, add resumed-session step test |

No new files created.

## Implementation Steps

1. **Step 1** — `MLflowLogger` infrastructure: `_run_step_count`, `current_step()`, `_advance_step()`, `step` param on `log_metrics()`, `end_run()` cleanup
2. **Step 2** — Rewrite `log_conversation()` and `log_conversation_artifacts()` with step-aware logging
3. **Step 3** — Update `mlflow_conversation` context manager for step-prefixed Phase 1 prompt artifact
