# Step 2 – Simplify LLM Interface: `ask_llm()` thin wrapper + centralise `TimeoutExpired` + delete `claude_code_interface.py`

## Context
See `pr_info/steps/summary.md` for the full picture.

`ask_llm()` currently routes to `ask_claude_code()` → `ask_claude_code_cli/api()` → `result["text"]`.
`prompt_llm()` routes directly to `ask_claude_code_cli/api()`.
These two paths are parallel and nearly identical. The intermediate `ask_claude_code()` layer is pure indirection.

This step:
1. Rewrites `ask_llm()` as a one-liner: `return prompt_llm(...)["text"]`
2. Moves `TimeoutExpired` diagnostics logging into `prompt_llm()` (currently duplicated in `_call_llm_with_comprehensive_capture()` which is removed in Step 3)
3. Deletes `claude_code_interface.py` (now dead code)
4. Updates the two test files that reference the deleted module

After this step, `ask_llm()` callers are unaffected (same signature, same return type). `prompt_llm()` callers are unaffected.

---

## WHERE

- **Modify**: `src/mcp_coder/llm/interface.py`
- **Delete**: `src/mcp_coder/llm/providers/claude/claude_code_interface.py`
- **Modify**: `tests/llm/test_interface.py` — update `TestAskLLM` and `TestIntegration` to mock `ask_claude_code_cli/api` instead of `ask_claude_code`; delete `TestAskClaudeCode` class
- **Delete**: `tests/llm/providers/claude/test_claude_code_interface.py`

---

## WHAT

### `ask_llm()` — new implementation

```python
def ask_llm(...) -> str:
    return prompt_llm(
        question,
        provider=provider,
        method=method,
        session_id=session_id,
        timeout=timeout,
        env_vars=env_vars,
        project_dir=project_dir,
        execution_dir=execution_dir,
        mcp_config=mcp_config,
        branch_name=branch_name,
    )["text"]
```

All input validation (empty question, invalid timeout) is already in `prompt_llm()` — remove the duplicate checks from `ask_llm()`.

### `prompt_llm()` — add `TimeoutExpired` handling

Wrap the provider dispatch in a try/except for `TimeoutExpired`:

```python
try:
    if provider == "claude":
        if method == "cli":
            return ask_claude_code_cli(...)
        elif method == "api":
            return ask_claude_code_api(...)
        ...
except TimeoutExpired:
    logger.error("LLM request timed out after %ds", timeout)
    logger.error("Prompt length: %d characters (%d words)", len(question), len(question.split()))
    logger.error("LLM method: %s/%s", provider, method)
    logger.error("Consider: checking network, simplifying prompt, increasing timeout")
    raise  # re-raise original TimeoutExpired — type transparent to callers
```

### `interface.py` — remove dead imports

Remove:
```python
from .providers.claude.claude_code_interface import ask_claude_code
```

---

## HOW

**Import to add** in `interface.py`:
```python
from .providers.claude.claude_code_api import ask_claude_code_api
from .providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.utils.subprocess_runner import TimeoutExpired
import logging
logger = logging.getLogger(__name__)
```

Note: `ask_claude_code_cli` and `ask_claude_code_api` are already imported in `prompt_llm()`'s call path — just make the module-level imports explicit.

---

## ALGORITHM

```
ask_llm(question, provider, method, session_id, timeout, env_vars, project_dir, execution_dir, mcp_config, branch_name):
    return prompt_llm(same args)["text"]

prompt_llm(same args):
    validate question not empty, timeout > 0
    try:
        route to ask_claude_code_cli() or ask_claude_code_api() based on provider/method
        return LLMResponseDict
    except TimeoutExpired:
        log diagnostics (prompt length, provider/method, guidance)
        raise  # original exception, not wrapped
```

---

## DATA

`ask_llm()` returns: `str` — unchanged from current behaviour
`prompt_llm()` returns: `LLMResponseDict` — unchanged from current behaviour
`TimeoutExpired` propagates unchanged — no wrapping

---

## TESTS

**File**: `tests/llm/test_interface.py`

### Changes needed

The existing `TestAskLLM` class mocks `mcp_coder.llm.interface.ask_claude_code`. After this step, `ask_llm()` calls `prompt_llm()` which calls `ask_claude_code_cli/api` directly. Update all mocks:

- Replace `@patch("mcp_coder.llm.interface.ask_claude_code")` with `@patch("mcp_coder.llm.interface.ask_claude_code_cli")` (for `method="cli"` tests)
- Mock must return `LLMResponseDict` (not plain `str`) — `ask_llm()` now extracts `["text"]`
- Delete the `TestAskClaudeCode` class (tests the deleted module)
- Delete `from mcp_coder.llm.providers.claude.claude_code_interface import ask_claude_code` import

### New test cases to add

In `TestAskLLM`:
- `test_ask_llm_timeout_expired_logged_and_reraised` — mock `ask_claude_code_cli` to raise `TimeoutExpired`, assert it is re-raised as `TimeoutExpired` (not wrapped), and that logger.error was called with diagnostics

In `TestPromptLLM`:
- `test_prompt_llm_timeout_expired_logged_and_reraised` — same as above but calling `prompt_llm()` directly

**File**: `tests/llm/providers/claude/test_claude_code_interface.py`
- Delete this file entirely (module is deleted)

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Your task is to implement Step 2: simplify the LLM interface layer.

Follow TDD:
1. First update tests in `tests/llm/test_interface.py`:
   - Replace all mocks of `ask_claude_code` with `ask_claude_code_cli` or `ask_claude_code_api`
   - Update mock return values to return LLMResponseDict dicts (not plain strings)
   - Delete the TestAskClaudeCode class
   - Add TimeoutExpired tests for both ask_llm() and prompt_llm()
   - Remove the import of ask_claude_code from claude_code_interface
2. Delete `tests/llm/providers/claude/test_claude_code_interface.py`
3. Run tests — they will fail until implementation is done
4. Implement changes in `src/mcp_coder/llm/interface.py`:
   - Rewrite ask_llm() as: return prompt_llm(...)["text"]  (remove duplicate validation)
   - Add TimeoutExpired try/except to prompt_llm() with diagnostics logging, then re-raise
   - Remove import of ask_claude_code; ensure ask_claude_code_cli and ask_claude_code_api are imported
5. Delete `src/mcp_coder/llm/providers/claude/claude_code_interface.py`
6. Run tests to confirm all pass.

IMPORTANT: TimeoutExpired must be re-raised as-is (not wrapped). The exception type must remain
TimeoutExpired so callers that catch it continue to work.
```
