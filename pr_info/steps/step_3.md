# Step 3: Move test prompt to `execute_verify()`; remove it from `verify_langchain()`

## Context
See [summary.md](./summary.md) for full architectural overview.

This step has two tightly coupled halves that must land in one commit:
- **A**: Remove the test prompt from `verify_langchain()` (source + tests)
- **B**: Add the unified test prompt call in `execute_verify()` (source + tests)

They are coupled because `verify_langchain()` currently owns the `test_prompt` result key. After this step, that key is gone from `verify_langchain()` and the test prompt result is printed inline in `execute_verify()`. Splitting them would leave either `verify_langchain()` broken or `execute_verify()` with a double test prompt.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement step 3: move the LLM test prompt from verify_langchain() into execute_verify().

Part A — remove from verify_langchain():
  - Remove the test prompt block from src/mcp_coder/llm/providers/langchain/verification.py
  - Remove the test_prompt key from the returned dict
  - Update overall_ok logic (no longer gates on test_prompt_ok)
  - Update tests/llm/providers/langchain/test_langchain_verification.py accordingly

Part B — add to execute_verify():
  - Capture timestamp before the test prompt
  - Call ask_llm("Reply with OK", provider=active_provider, timeout=30)
  - Print the test prompt result inline in the LLM PROVIDER section
  - Pass since=timestamp to verify_mlflow()
  - Update tests/cli/commands/test_verify_orchestration.py and
    tests/cli/commands/test_verify_integration.py accordingly

Follow TDD: update tests first, then implement to make them pass.
Run pytest, pylint, and mypy to confirm all checks pass.
```

---

## WHERE

### Part A — remove test prompt from `verify_langchain()`
| Item | Path |
|------|------|
| Modified source | `src/mcp_coder/llm/providers/langchain/verification.py` |
| Modified tests | `tests/llm/providers/langchain/test_langchain_verification.py` |

### Part B — add test prompt to `execute_verify()`
| Item | Path |
|------|------|
| Modified source | `src/mcp_coder/cli/commands/verify.py` |
| Modified tests | `tests/cli/commands/test_verify_orchestration.py` |
| Modified tests | `tests/cli/commands/test_verify_integration.py` |

---

## WHAT

### Part A: `verify_langchain()` — what is removed

**Remove** the entire test prompt block (currently ~20 lines):
```python
# REMOVE THIS BLOCK:
if api_key and backend:
    start = time.monotonic()
    try:
        ask_langchain("Reply with OK", timeout=15)
        ...
        result["test_prompt"] = {"ok": True, ...}
    except Exception as exc:
        result["test_prompt"] = {"ok": False, ...}
else:
    result["test_prompt"] = {"ok": None, ...}
```

**Remove** the `test_prompt_ok` gate from `overall_ok`:
```python
# BEFORE:
test_prompt_ok = result["test_prompt"]["ok"] is True or result["test_prompt"]["ok"] is None
result["overall_ok"] = bool(
    backend
    and result["backend_package"]["ok"]
    and result["mcp_adapters"]["ok"]
    and result["langgraph"]["ok"]
    and test_prompt_ok          # ← REMOVE
)

# AFTER:
result["overall_ok"] = bool(
    backend
    and result["backend_package"]["ok"]
    and result["mcp_adapters"]["ok"]
    and result["langgraph"]["ok"]
)
```

**Remove** the `import time` and `from . import ... ask_langchain` if `ask_langchain` is no longer used. Check: `ask_langchain` is only used by the test prompt block and the `mcp_agent_test` block. The `mcp_agent_test` block uses `ask_llm` via lazy import from `...interface`, not `ask_langchain` directly. So `ask_langchain` import can be removed from the top-level import. `import time` can also be removed.

### Part B: `execute_verify()` — what is added

**New import** at top of `verify.py`:
```python
import datetime
from ...llm.interface import ask_llm
```

**In `execute_verify()`**, between step 3 (LangChain verification) and step 4 (MLflow verification), insert:

```python
# 3b. Unified test prompt (both providers)
timestamp = datetime.datetime.now(datetime.timezone.utc)
try:
    ask_llm("Reply with OK", provider=active_provider, timeout=30)
    print(f"  {'Test prompt':<20s} {symbols['success']} responded OK")
except Exception as exc:  # pylint: disable=broad-except
    print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({exc})")

# 4. MLflow verification
mlflow_result = verify_mlflow(since=timestamp)
```

---

## HOW

### Import chain

`verify.py` already imports from `...llm.mlflow_logger`. Adding `from ...llm.interface import ask_llm` is safe:
- `cli` → `llm` is allowed by both tach and import-linter (CLI is the presentation layer)
- `ask_llm` is already the public interface used throughout the codebase

### `_LABEL_MAP` — no change needed for the inline print

The test prompt result is printed via a direct `print()` call (same pattern as `Active provider`), not via `_format_section()`. Therefore no new `_LABEL_MAP` entry is needed for the test prompt line itself.

### `verify_mlflow()` call site

```python
# BEFORE:
mlflow_result = verify_mlflow()

# AFTER:
mlflow_result = verify_mlflow(since=timestamp)
```

---

## ALGORITHM

```
# In execute_verify(), after LangChain check, before MLflow check:
timestamp = datetime.now(utc)
try:
    ask_llm("Reply with OK", provider=active_provider, timeout=30)
    print success line in LLM PROVIDER block
except any exception:
    print failure line in LLM PROVIDER block (verify continues regardless)
mlflow_result = verify_mlflow(since=timestamp)
```

The test prompt failure is **informational within the LLM PROVIDER section** — it does not directly set `overall_ok`. The MLflow DB check (`tracking_data`) is what propagates failure to `overall_ok` when the run was not logged. This matches the issue's semantics: the test prompt failure is visible, and the MLflow tracking check confirms end-to-end.

---

## DATA

### `verify_langchain()` return dict — keys after change

```python
# BEFORE (has test_prompt):
{"backend", "model", "api_key", "langchain_core", "backend_package",
 "mcp_adapters", "langgraph", "test_prompt", "overall_ok"}

# AFTER (test_prompt removed):
{"backend", "model", "api_key", "langchain_core", "backend_package",
 "mcp_adapters", "langgraph", "overall_ok"}
# optional: "mcp_agent_test" (when mcp_config_path provided)
# optional: "available_models" (when check_models=True)
```

### `execute_verify()` output change

The `=== LLM PROVIDER ===` section gains a new inline line:
```
=== LLM PROVIDER ===
  Active provider      ✓ claude (from default)
  Test prompt          ✓ responded OK
```
or on failure:
```
  Test prompt          ✗ FAILED (TimeoutExpired: ...)
```

---

## TESTS

### Part A: `tests/llm/providers/langchain/test_langchain_verification.py`

**Remove these 5 test methods** (they test `test_prompt` key which no longer exists):
- `test_test_prompt_success`
- `test_test_prompt_failure`
- `test_test_prompt_skipped_no_api_key` — but keep the `overall_ok is True` assertion by replacing with a simpler test
- All `test_prompt_ok` assertions in other tests

**Update** `test_test_prompt_skipped_no_api_key` → rename to `test_no_api_key_overall_ok_true`:
```python
def test_no_api_key_overall_ok_true(self, mock_config, mock_pkg):
    """overall_ok is True even when no API key (verify_langchain no longer tests prompt)."""
    # backend ok, all packages ok, no api key → overall_ok True
    # (test prompt is now executed in execute_verify, not here)
    ...
    assert "test_prompt" not in result
    assert result["overall_ok"] is True
```

**Update** `_check_package_installed` mock call counts in tests that used to count 4 calls (core, backend, mcp, langgraph) — count is unchanged since `test_prompt` was not a package check; verify no side effects.

### Part B: `tests/cli/commands/test_verify_orchestration.py`

**Update mock helpers** — remove `test_prompt` key from `_langchain_ok()` and `_langchain_fail()`:
```python
# BEFORE:
def _langchain_ok() -> dict[str, Any]:
    return {
        ...
        "test_prompt": {"ok": True, "value": "responded in 1.2s", "error": None},
        "overall_ok": True,
    }

# AFTER:
def _langchain_ok() -> dict[str, Any]:
    return {
        ...
        # test_prompt removed — now executed in execute_verify()
        "overall_ok": True,
    }
```

**Add `ask_llm` patch** to all tests that call `execute_verify()` to prevent real LLM calls:
```python
@patch("mcp_coder.cli.commands.verify.ask_llm")
```
Add `mock_ask_llm: MagicMock` parameter to affected test methods. The mock returns `"OK"` by default.

**Add new test** `test_test_prompt_displayed_in_output`:
```python
def test_test_prompt_displayed_in_output(self, ...):
    """Test prompt result line appears in LLM PROVIDER section."""
    mock_ask_llm.return_value = "OK"
    execute_verify(_make_args())
    output = capsys.readouterr().out
    assert "Test prompt" in output
```

**Add new test** `test_test_prompt_failure_does_not_raise`:
```python
def test_test_prompt_failure_does_not_raise(self, ...):
    """execute_verify() continues when ask_llm raises."""
    mock_ask_llm.side_effect = Exception("timeout")
    result = execute_verify(_make_args())
    # Should still return an exit code, not raise
    assert isinstance(result, int)
```

**Add new test** `test_since_timestamp_passed_to_verify_mlflow`:
```python
def test_since_timestamp_passed_to_verify_mlflow(self, ...):
    """verify_mlflow() is called with a datetime since= argument."""
    execute_verify(_make_args())
    call_kwargs = mock_mlflow.call_args
    assert call_kwargs.kwargs.get("since") is not None
    # or positional: call_kwargs.args[0] is not None
```

### Part B: `tests/cli/commands/test_verify_integration.py`

**Update `_make_langchain_result()`** — remove `test_prompt` key (same as orchestration mock helpers).

**Add `ask_llm` patch** to all `TestVerifyEndToEnd` and `TestExitCodeMatrix` tests. The cleanest approach is to add it to the `_run_verify()` helper in `TestExitCodeMatrix`:
```python
def _run_verify(self, ...) -> int:
    with (
        patch("sys.argv", ["mcp-coder", "verify"]),
        patch("mcp_coder.cli.commands.verify.ask_llm", return_value="OK"),  # ← ADD
        patch("mcp_coder.cli.commands.verify.resolve_llm_method", ...),
        ...
    ):
        return main()
```
