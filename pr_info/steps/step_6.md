# Step 6: Make verify test prompt log to MLflow; restore `since=`

## Context
See [summary.md](./summary.md) and [Decisions.md](./Decisions.md).

Currently `execute_verify()` calls `ask_llm()` which discards the response. To log the test prompt to MLflow, we need `prompt_llm()` (returns full `LLMResponseDict`) and then call `_log_to_mlflow()`. Once logging works, restore the `since=` timestamp to `verify_mlflow()` so it confirms the run was actually written to the DB.

---

## LLM Prompt

```
Read pr_info/steps/summary.md, pr_info/steps/Decisions.md, and pr_info/steps/step_6.md.

Implement step 6: make the verify test prompt log to MLflow and restore the since= parameter.

1. Update tests first in tests/cli/commands/test_verify_orchestration.py
2. Modify execute_verify() in src/mcp_coder/cli/commands/verify.py
3. Fix the integration test in tests/integration/test_verify_llm_integration.py
4. Run pytest, pylint, mypy, ruff to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| Modified source | `src/mcp_coder/cli/commands/verify.py` |
| Modified tests | `tests/cli/commands/test_verify_orchestration.py` |
| Modified tests | `tests/cli/commands/test_verify_command.py` |
| Modified tests | `tests/integration/test_verify_llm_integration.py` |

---

## WHAT

### Changes to `execute_verify()`

1. **Rename** `_log_to_mlflow` to `log_to_mlflow` in `prompt.py` (remove leading underscore). Update all call sites within `prompt.py`.
2. **Import** `prompt_llm` instead of `ask_llm`; import `log_to_mlflow` from `prompt.py`
3. **Replace** `ask_llm("Reply with OK", ...)` with `prompt_llm("Reply with OK", ...)`
4. **Call** `log_to_mlflow(response, "Reply with OK", project_dir)` after prompt succeeds
5. **Capture** `timestamp = datetime.datetime.now(datetime.timezone.utc)` before the prompt call
6. **Restore** `since=timestamp` in the `verify_mlflow()` call
7. **Derive** `project_dir`: `project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()`
8. **Verify/fix** the E2E integration test (`tests/integration/test_verify_llm_integration.py`) — it directly tests the prompt→MLflow pipeline and should pass after these changes

### Updated imports in `verify.py`

```python
import datetime
from pathlib import Path
from ...llm.interface import prompt_llm
from .prompt import log_to_mlflow
```

In `prompt.py`, rename `_log_to_mlflow` → `log_to_mlflow` and update all call sites within `prompt.py`. Then import from `verify.py` as `from .prompt import log_to_mlflow`.

---

## HOW

### Integration with existing flow

```python
# In execute_verify(), replacing the current test prompt block:

# 3b. Unified test prompt (both providers)
import datetime
timestamp = datetime.datetime.now(datetime.timezone.utc)
test_prompt_ok = True
try:
    response = prompt_llm("Reply with OK", provider=active_provider, timeout=30)
    print(f"  {'Test prompt':<20s} {symbols['success']} responded OK")
    # Log to MLflow (will be confirmed by verify_mlflow's since= check)
    log_to_mlflow(response, "Reply with OK", project_dir)
except Exception as exc:
    test_prompt_ok = False
    print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({exc})")

# 4. MLflow verification (now with since= to confirm logging)
mlflow_result = verify_mlflow(since=timestamp)
```

### `log_to_mlflow` import path

`verify.py` is in `mcp_coder.cli.commands`. `log_to_mlflow` is in `mcp_coder.cli.commands.prompt`. This is a sibling module import — no cross-layer concern. Use:

```python
from .prompt import log_to_mlflow
```

---

## ALGORITHM

```
timestamp = now(utc)
try:
    response = prompt_llm("Reply with OK", provider=active, timeout=30)
    print success
    log_to_mlflow(response, "Reply with OK", project_dir)
except:
    test_prompt_ok = False
    print failure
mlflow_result = verify_mlflow(since=timestamp)
```

---

## DATA

### `prompt_llm` return type

`LLMResponseDict` (TypedDict) with keys: `version`, `timestamp`, `text`, `session_id`, `provider`, `raw_response`.

### `log_to_mlflow` signature

```python
log_to_mlflow(response_data: LLMResponseDict, prompt: str, project_dir: Path,
              branch_name: str | None = None, step_name: str | None = None) -> None
```

---

## TESTS

### `test_verify_orchestration.py` updates

- Replace `mock_ask_llm` patches with `mock_prompt_llm` (returns a minimal `LLMResponseDict`)
- Add `mock_log_to_mlflow` patch for `mcp_coder.cli.commands.verify.log_to_mlflow`
- Update `test_verify_mlflow_called_without_since` → `test_since_timestamp_passed_to_verify_mlflow` (assert `since` kwarg is a datetime)
- Add test: `test_log_to_mlflow_called_on_success` — verify `log_to_mlflow` is called with the response
- Add test: `test_log_to_mlflow_not_called_on_failure` — verify `log_to_mlflow` is NOT called when prompt raises

### `test_verify_command.py` updates

- Replace `@patch("...ask_llm", ...)` with `@patch("...prompt_llm", ...)`
- Mock return value must be a minimal `LLMResponseDict` dict
- Add `@patch("...verify.log_to_mlflow")` to prevent actual MLflow calls

### `test_verify_llm_integration.py` updates

- The E2E test should now work: `execute_verify()` logs the prompt to MLflow, and `query_sqlite_tracking(since=before_ts)` finds it
- Verify `stats.test_prompt_logged is True` assertion
