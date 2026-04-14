# Step 5: CLI `prompt` Command — `--add-system-prompts` Flag + Wire `project_dir`

## References
- Summary: `pr_info/steps/summary.md`
- Depends on: Steps 2-4 (interface + providers accept prompts)

## WHERE

**Modified files:**
- `src/mcp_coder/cli/parsers.py` — add `--add-system-prompts` flag to prompt parser
- `src/mcp_coder/cli/commands/prompt.py` — pass `project_dir` to `prompt_llm`/`prompt_llm_stream` when flag is set
- `tests/cli/commands/test_prompt.py` — test the new flag

## WHAT

### `parsers.py` — add flag to `add_prompt_parser()`

```python
prompt_parser.add_argument(
    "--add-system-prompts",
    action="store_true",
    help="Inject system and project prompts into the LLM request",
)
```

### `prompt.py` — wire `project_dir` conditionally

In `execute_prompt()`, after resolving `project_dir`:

```python
# Determine whether to pass project_dir for prompt loading
prompt_project_dir = str(project_dir) if getattr(args, "add_system_prompts", False) else None
```

Then pass to all `prompt_llm()` / `prompt_llm_stream()` calls:

```python
prompt_llm_stream(
    args.prompt,
    ...,
    project_dir=prompt_project_dir,
)

prompt_llm(
    args.prompt,
    ...,
    project_dir=prompt_project_dir,
)
```

## HOW

- `project_dir` is already resolved in `execute_prompt()` (lines ~45-55). We just conditionally pass it.
- Without `--add-system-prompts`, `project_dir=None` is passed → no prompts loaded (backward compatible).
- With `--add-system-prompts`, `project_dir=str(project_dir)` is passed → prompts loaded and injected.
- All 3 call paths in `execute_prompt()` (streaming, session-id, json) get the same treatment.

## ALGORITHM

```python
# In execute_prompt(), after project_dir resolution:
add_prompts = getattr(args, "add_system_prompts", False)
prompt_project_dir = str(project_dir) if add_prompts else None

# Then in each prompt_llm / prompt_llm_stream call:
#   ..., project_dir=prompt_project_dir, ...
```

## DATA

No new data structures. Just a boolean flag and a conditional string.

## TESTS (`tests/cli/commands/test_prompt.py`)

1. **`test_prompt_add_system_prompts_flag_passes_project_dir`** — mock prompt_llm_stream, verify `project_dir` is passed when flag is set
2. **`test_prompt_no_flag_no_project_dir`** — verify `project_dir=None` when flag is absent
3. **`test_prompt_add_system_prompts_all_output_formats`** — verify flag works for rendered, json, session-id modes

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 5.

Add --add-system-prompts flag to the prompt parser in src/mcp_coder/cli/parsers.py.
In src/mcp_coder/cli/commands/prompt.py, pass project_dir to prompt_llm() and
prompt_llm_stream() only when the flag is set. When absent, pass project_dir=None
for backward compatibility.

Update tests in tests/cli/commands/test_prompt.py to verify the flag wiring.
All quality checks must pass.
```
