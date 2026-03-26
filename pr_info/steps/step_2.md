# Step 2: Rewrite `log_conversation()` and `log_conversation_artifacts()` with step-aware logging

> **Context:** See `pr_info/steps/summary.md` for the full design.
> Builds on step 1's `current_step()`, `_advance_step()`, and `log_metrics(step=)`.

## LLM Prompt

```
Implement step 2 of issue #593 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).

Rewrite log_conversation() and log_conversation_artifacts() to use step-aware
params, metrics, and artifacts. Stable params logged only at step 0. Numeric
values as metrics with step index. All param values dumped to step_N_all_params.json.
Note: log_conversation_artifacts() skips metrics (preserving existing behavior).
Update existing tests first (TDD), then implement, then run all three code quality checks.
```

## WHERE

- `tests/llm/test_mlflow_logger.py` — update existing tests, add multi-step and regression tests
- `src/mcp_coder/llm/mlflow_logger.py` — `MLflowLogger.log_conversation()` and `MLflowLogger.log_conversation_artifacts()`

## WHAT — Tests (update/add)

### `log_conversation()` tests

#### Update `test_log_conversation`

Verify for step 0 (first call):
- `log_params` called once with only stable keys: `model`, `provider`, `working_directory`
- `log_metrics` called with `step=0` for `prompt_length`, `duration_ms`, `cost_usd`
- `log_artifact` called with `step_0_prompt.txt`, `step_0_conversation.json`, `step_0_all_params.json`
- `current_step()` returns 1 after the call

#### Add `test_log_conversation_step1_skips_params`

Simulate step 1 (set `_run_step_count[run_id] = 1` before calling):
- `log_params` NOT called
- `log_metrics` called with `step=1`
- Artifacts prefixed `step_1_`
- `current_step()` returns 2 after the call

### `log_conversation_artifacts()` tests

#### Update `test_log_conversation_artifacts_logs_params_and_artifacts_not_metrics`

Verify for step 0:
- `log_params` called with only stable keys: `model`, `provider`, `working_directory`
- `log_artifact` called 3 times: `step_0_prompt.txt`, `step_0_conversation.json`, `step_0_all_params.json`
- `log_metrics` NOT called (this method never logs metrics)
- `current_step()` returns 1 after the call

#### Add `test_log_conversation_artifacts_step1_skips_params`

Simulate step 1:
- `log_params` NOT called
- Artifacts prefixed `step_1_`
- `current_step()` returns 2

### Add `test_multi_prompt_session_no_param_conflict` (regression test for #593)

Test the full sequence that triggers the original bug:
1. `start_run()` → `log_conversation(params_a)` → `end_run(session_id="s1")`
2. `start_run(session_id="s1")` → `log_conversation(params_b)` → `end_run(session_id="s1")`
3. Assert: `log_params` called exactly once (step 0 only), no MlflowException raised
4. Assert: metrics logged with step=0 and step=1 respectively

## WHAT — Implementation

### `log_conversation()` rewrite

**Algorithm (pseudocode):**
```
step = self.current_step()

if step == 0:
    log_params({model, provider, working_directory})  # stable only

all_params = {model, provider, working_directory, branch_name, step_name, prompt_length}
log_artifact(json.dumps(all_params), f"step_{step}_all_params.json")

numeric_metrics = {prompt_length, duration_ms, cost_usd, usage_*, perf_*}
log_metrics(numeric_metrics, step=step)

log_artifact(prompt, f"step_{step}_prompt.txt")
log_artifact(conversation_json, f"step_{step}_conversation.json")

_advance_step()
```

**Key changes from current code:**
- Params: only 3 stable keys, only at step 0
- `prompt_length` moves from params to metrics
- All 6 original param values dumped to `step_N_all_params.json`
- Artifact filenames gain `step_N_` prefix
- `_advance_step()` called at end

### `log_conversation_artifacts()` rewrite

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
- Same 3 changes as `log_conversation()`: stable params only at step 0, all_params artifact, step-prefixed names
- No metrics (this method intentionally skips metrics — preserving existing behavior)

## DATA

- `step_N_all_params.json` artifact content:
  ```json
  {
    "model": "claude-3",
    "provider": "claude",
    "working_directory": "/tmp",
    "branch_name": "main",
    "step_name": "analysis",
    "prompt_length": 5643
  }
  ```

## HOW — Integration

No callers change. `mlflow_conversation` context manager calls `log_conversation()`
in Phase 2 — that call now does step-aware logging internally.

## Commit

```
fix(mlflow): make log_conversation() and log_conversation_artifacts() step-aware (#593)
```
