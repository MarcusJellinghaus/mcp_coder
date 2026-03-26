# Step 3: Rewrite `log_conversation_artifacts()` with step-aware logging

> **Context:** See `pr_info/steps/summary.md` for the full design.
> Same pattern as step 2, applied to the artifacts-only method.

## LLM Prompt

```
Implement step 3 of issue #593 (see pr_info/steps/summary.md and pr_info/steps/step_3.md).

Rewrite log_conversation_artifacts() to use step-aware params and artifacts.
Same pattern as log_conversation(): stable params at step 0 only,
step-prefixed artifact names, all_params JSON dump.
Update existing tests first (TDD), then implement, then run all three code quality checks.
```

## WHERE

- `tests/llm/test_mlflow_logger.py` — update `test_log_conversation_artifacts_logs_params_and_artifacts_not_metrics`, add multi-step test
- `src/mcp_coder/llm/mlflow_logger.py` — `MLflowLogger.log_conversation_artifacts()`

## WHAT — Tests (update/add)

### Update `test_log_conversation_artifacts_logs_params_and_artifacts_not_metrics`

Verify for step 0:
- `log_params` called with only stable keys: `model`, `provider`, `working_directory`
- `log_artifact` called 3 times: `step_0_prompt.txt`, `step_0_conversation.json`, `step_0_all_params.json`
- `log_metrics` NOT called (this method never logs metrics)
- `current_step()` returns 1 after the call

### Add `test_log_conversation_artifacts_step1_skips_params`

Simulate step 1:
- `log_params` NOT called
- Artifacts prefixed `step_1_`
- `current_step()` returns 2

## WHAT — Implementation

Rewrite `log_conversation_artifacts()` body:

**Algorithm (pseudocode):**
```
step = self.current_step()

if step == 0:
    log_params({model, provider, working_directory})

all_params = {model, provider, working_directory, branch_name, step_name, prompt_length}
log_artifact(json.dumps(all_params), f"step_{step}_all_params.json")

log_artifact(prompt, f"step_{step}_prompt.txt")
log_artifact(conversation_json, f"step_{step}_conversation.json")

_advance_step()
```

**Key changes from current code:**
- Same 3 changes as step 2: stable params only at step 0, all_params artifact, step-prefixed names
- No metrics (this method intentionally skips metrics — preserving existing behavior)

## DATA

Same `step_N_all_params.json` structure as step 2.

## HOW — Integration

No callers change. Same internal refactor as step 2.

## Commit

```
fix(mlflow): make log_conversation_artifacts() step-aware (#593)
```
