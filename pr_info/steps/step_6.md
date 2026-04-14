# Step 6: iCoder — Pass `project_dir` for Prompt Injection

## References
- Summary: `pr_info/steps/summary.md`
- Depends on: Steps 2-4 (interface + providers accept prompts)

## WHERE

**Modified files:**
- `src/mcp_coder/icoder/services/llm_service.py` — `RealLLMService` accepts + passes `project_dir`
- `src/mcp_coder/cli/commands/icoder.py` — pass `project_dir` when creating `RealLLMService`
- `tests/icoder/test_llm_service.py` — test `project_dir` pass-through

## WHAT

### `llm_service.py` — add `project_dir` to `RealLLMService`

```python
class RealLLMService:
    def __init__(
        self,
        provider: str = "claude",
        session_id: str | None = None,
        execution_dir: str | None = None,
        mcp_config: str | None = None,
        env_vars: dict[str, str] | None = None,
        timeout: int = ICODER_LLM_TIMEOUT_SECONDS,
        mcp_manager: MCPManager | None = None,
        project_dir: str | None = None,           # NEW
    ) -> None:
        ...
        self._project_dir = project_dir
```

In `stream()`:
```python
for event in prompt_llm_stream(
    question,
    ...,
    project_dir=self._project_dir,          # NEW
):
```

### `icoder.py` — pass `project_dir`

```python
llm_service = RealLLMService(
    ...,
    project_dir=str(project_dir),               # NEW — iCoder always injects prompts
)
```

Note: iCoder **always** injects prompts (no opt-in flag). Per the issue: "Applies To: Both `prompt` command (via `--add-system-prompts`) and `icoder`".

## HOW

- `RealLLMService.__init__` stores `project_dir` as `self._project_dir`
- `stream()` passes it to `prompt_llm_stream()` which was updated in Step 2
- `icoder.py` already resolves `project_dir` (line ~55), just needs to pass it through
- `FakeLLMService` does not need changes (it doesn't call real LLM)
- `LLMService` Protocol does not need changes (project_dir is a constructor concern, not a method concern)

## ALGORITHM

```python
# In RealLLMService.__init__:
self._project_dir = project_dir

# In RealLLMService.stream():
for event in prompt_llm_stream(
    question, ..., project_dir=self._project_dir):
    yield event

# In execute_icoder():
llm_service = RealLLMService(..., project_dir=str(project_dir))
```

## DATA

No new data structures. `project_dir: str | None` stored as instance attribute.

## TESTS (`tests/icoder/test_llm_service.py`)

1. **`test_real_llm_service_passes_project_dir`** — mock `prompt_llm_stream`, verify `project_dir` kwarg is passed
2. **`test_real_llm_service_project_dir_none`** — verify None is passed when not provided (backward compat)

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 6.

Add project_dir parameter to RealLLMService in
src/mcp_coder/icoder/services/llm_service.py. Pass it through to
prompt_llm_stream() in the stream() method.

In src/mcp_coder/cli/commands/icoder.py, pass project_dir=str(project_dir)
when creating RealLLMService. iCoder always injects prompts (no opt-in flag).

Write tests verifying project_dir is passed through correctly.
All quality checks must pass.
```
