# Step 3: Update `mlflow_conversation` context manager for step-prefixed Phase 1 prompt

> **Context:** See `pr_info/steps/summary.md` for the full design.
> This is the final step — builds on steps 1–2, connects the context manager to the step tracking.

## LLM Prompt

```
Implement step 3 of issue #593 (see pr_info/steps/summary.md and pr_info/steps/step_3.md).

Update the mlflow_conversation context manager to use current_step() for
step-prefixed Phase 1 prompt artifact naming (step_N_prompt.txt).
Update existing tests first (TDD), then implement, then run all three code quality checks.
```

## WHERE

- `tests/llm/test_mlflow_conversation_logger.py` — update Phase 1 artifact assertions, add resumed-session test
- `src/mcp_coder/llm/mlflow_conversation_logger.py` — `mlflow_conversation()`

## WHAT — Tests (update/add)

### Update all existing tests that assert `"prompt.txt"`

Change expected artifact name from `"prompt.txt"` to `"step_0_prompt.txt"` in:
- `test_phase1_logs_prompt_phase2_logs_response`
- `test_tool_trace_logged_as_artifact`
- `test_no_tool_trace_artifact_when_absent`
- `test_no_tool_trace_artifact_when_empty_list`

### Add `test_resumed_session_uses_step_1_prompt_artifact`

```python
def test_resumed_session_uses_step_1_prompt_artifact(self) -> None:
    """When resuming a session at step 1, Phase 1 artifact is step_1_prompt.txt."""
    mock_logger._is_enabled.return_value = True
    mock_logger.has_session.return_value = True
    mock_logger.current_step.return_value = 1  # resumed at step 1

    with mlflow_conversation(prompt="hi", provider="claude", session_id="sid-x") as result:
        result["response_data"] = {"text": "ok", "session_id": "sid-x", "provider": "claude"}

    # Phase 1 artifact should be step_1_prompt.txt
    mock_logger.log_artifact.assert_any_call("hi", "step_1_prompt.txt")
```

## WHAT — Implementation

One-line change in `mlflow_conversation()`:

**Before:**
```python
mlflow_logger.log_artifact(prompt, "prompt.txt")
```

**After:**
```python
step = mlflow_logger.current_step()
mlflow_logger.log_artifact(prompt, f"step_{step}_prompt.txt")
```

## DATA

No new data structures. Just uses `current_step()` from step 1.

## HOW — Integration

The Phase 1 prompt artifact now uses the same `step_N_` prefix as Phase 2 artifacts.
When `log_conversation()` runs in Phase 2, it will also write `step_N_prompt.txt`
(same name, same content) — this is intentional: Phase 1 ensures the prompt survives
a timeout/kill, Phase 2 overwrites it as part of the complete artifact set.

## Commit

```
fix(mlflow): use step-prefixed prompt artifact in mlflow_conversation (#593)
```
