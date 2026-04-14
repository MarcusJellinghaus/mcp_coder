# Step 2: Add `project_dir` to Interface + Load Prompts in `prompt_llm()` / `prompt_llm_stream()`

## References
- Summary: `pr_info/steps/summary.md`
- Depends on: Step 1 (prompt_loader module)

## WHERE

**Modified files:**
- `src/mcp_coder/llm/interface.py` — add `project_dir` param, load prompts, pass to providers
- `tests/llm/test_interface.py` — update tests for new parameter

## WHAT

### `interface.py` changes

Both `prompt_llm()` and `prompt_llm_stream()` gain:

```python
def prompt_llm(
    question: str,
    provider: str = "claude",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    execution_dir: str | None = None,
    mcp_config: str | None = None,
    branch_name: str | None = None,
    project_dir: str | None = None,           # NEW
) -> LLMResponseDict:
```

```python
def prompt_llm_stream(
    question: str,
    provider: str = "claude",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    execution_dir: str | None = None,
    mcp_config: str | None = None,
    branch_name: str | None = None,
    tools: list[Any] | None = None,
    project_dir: str | None = None,           # NEW
) -> Iterator[StreamEvent]:
```

When `project_dir` is provided, load prompts and pass them to providers as keyword arguments. When `project_dir` is None, no prompts are injected (backward compatible).

## HOW

- Import `load_prompts` from `mcp_coder.prompts.prompt_loader`
- At the top of each function, after validation:
  ```python
  system_prompt = None
  project_prompt = None
  if project_dir:
      system_prompt, project_prompt, _config = load_prompts(Path(project_dir))
  ```
- Pass `system_prompt` and `project_prompt` to the langchain provider calls
- For Claude: assemble concatenated prompt string and pass as `append_system_prompt` (details in steps 3-4)
- The actual provider-side handling is added in Steps 3 and 4; this step only passes the parameters through

**Important**: Since steps 3 and 4 haven't been implemented yet, the providers will receive these as unexpected `**kwargs` or we add the parameters now with no-op handling. Simplest approach: add the parameters to the provider function signatures now (with `| None = None` defaults that are ignored), so they're ready for steps 3-4 to implement.

## ALGORITHM

```python
# In prompt_llm():
system_prompt, project_prompt = None, None
if project_dir:
    from mcp_coder.prompts.prompt_loader import load_prompts
    system_prompt, project_prompt, prompt_config = load_prompts(Path(project_dir))

if provider == "langchain":
    response = ask_langchain(..., system_prompt=system_prompt, project_prompt=project_prompt)
elif provider == "claude":
    # Build append_system_prompt for Claude CLI
    append_system_prompt, system_prompt_replace = _build_claude_system_prompts(system_prompt, project_prompt, prompt_config, project_dir)
    response = ask_claude_code_cli(..., append_system_prompt=append_system_prompt, system_prompt_replace=system_prompt_replace)
```

## DATA

No new data structures. Just threading `str | None` values through existing call chains.

## TESTS (`tests/llm/test_interface.py`)

1. **`test_prompt_llm_project_dir_none`** — no prompts loaded, backward compatible
2. **`test_prompt_llm_project_dir_loads_prompts`** — mock `load_prompts`, verify it's called with correct Path and results passed to provider
3. **`test_prompt_llm_stream_project_dir_loads_prompts`** — same for streaming path
4. **Update existing tests** — ensure `project_dir=None` default doesn't break them

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 2.

Add `project_dir: str | None = None` parameter to both prompt_llm() and
prompt_llm_stream() in src/mcp_coder/llm/interface.py. When project_dir is
provided, call load_prompts() from the prompt_loader module (Step 1) and pass
the resulting strings to the provider functions.

For langchain: pass as system_prompt and project_prompt kwargs.
For claude: build a concatenated prompt string and pass as append_system_prompt kwarg.

Add the corresponding parameters to the provider entry points (ask_langchain,
ask_langchain_stream, ask_claude_code_cli, ask_claude_code_cli_stream) with
default None — actual handling is implemented in Steps 3-4.

Update tests in tests/llm/test_interface.py. All quality checks must pass.
```
