# Step 13 — `verify`'s test prompt carries the real message shape

`verify.py:591` already sends `"Reply with OK"` through `prompt_llm` on every
run — the round-trip is already paid for. Its only defect is the missing
`project_dir=` kwarg: without it `prompt_llm` never calls `load_prompts`
(`interface.py:160-163`), so `ask_langchain` receives
`system_prompt=None, project_prompt=None`. **That one missing kwarg is why the
#1116 bug was invisible to `verify`.**

Lands **after** step 12 so the prompt provably goes to the provider `verify`
reported on.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — the `prompt_llm` call at ~line 591
- `tests/cli/commands/test_verify_orchestration.py`

## WHAT

One kwarg:

```python
response = prompt_llm(
    "Reply with OK",
    provider=active_provider,
    timeout=30,
    mcp_config=mcp_config_resolved,
    settings_file=settings_file,
    execution_dir=str(project_dir),
    env_vars=env_vars,
    project_dir=str(project_dir),      # <-- added
)
```

## HOW

- No new flag and no second check (Decision 1): fix the existing prompt.
- Applies to the **active provider**, uniformly, with no per-provider
  conditional — `verify` only ever exercises one provider, so there is no
  cross-provider blast radius.
- Deliberate, documented behaviour change to state in the commit message:
  - **langchain** now receives the merged system + project prompt in one
    `SystemMessage` — icoder's shape, which is what catches the #1116 class of
    bug.
  - **claude** now builds `--append-system-prompt` (`interface.py:249-252`)
    where it previously sent a bare message.
  - **copilot** now receives the system prompt only (`interface.py:211-213`).
- Do **not** touch the MCP edit smoke test (`_run_mcp_edit_smoke_test`); it is a
  separate, informational check.

## DATA

No new data structures. `response` is the same `LLMResponseDict`; the claude
branch still reads `raw_response["system"]` for the tools-exposed section.

## TDD

1. Patch `prompt_llm`; assert it is called with
   `project_dir=str(project_dir)` for `active_provider == "langchain"`.
2. Same assertion for `active_provider == "claude"`.
3. `--project-dir` given explicitly → the resolved path is what gets passed
   (not CWD).
4. Regression: a prompt failure still yields exit 1 with the classified message.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_13.md`.
> Implement step 13: add `project_dir=str(project_dir)` to the existing test
> prompt `prompt_llm(...)` call in `cli/commands/verify.py`, so the prompt
> carries the real merged system + project prompt for the active provider. No new
> flag, no second check, no per-provider conditional. Leave the MCP edit smoke
> test alone. Write tests first (TDD) asserting the kwarg is forwarded for both
> the langchain-active and claude-active cases, and note the behaviour change for
> claude/copilot in the commit message.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
