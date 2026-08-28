# Step 1 — Langchain: delete `execution_dir` outright

**Context:** [summary.md](./summary.md), section "Provider layer: the honest name at each layer".

Langchain runs in-process — there is no subprocess to place, and the parameter is already
dead (`agent.py` carries `# pylint: disable=unused-argument` on it). Independent of every
other step; touches only the langchain provider plus the two lines in `interface.py` that
feed it.

## WHERE

| File | Symbols |
|---|---|
| `src/mcp_coder/llm/providers/langchain/__init__.py` | `ask_langchain` (~`:269`), `_ask_agent` (~`:397`), `_ask_agent_stream` (~`:502`), `ask_langchain_stream` (~`:609`) |
| `src/mcp_coder/llm/providers/langchain/agent.py` | `run_agent` (~`:400`), `run_agent_stream` (~`:476`) |
| `src/mcp_coder/llm/interface.py` | langchain branches only (~`:188`, `~:368`) |
| `tests/llm/providers/langchain/test_langchain_coverage_gaps.py` | `:168`, `:173`, `:232`, `:233`, `:269`, `:273`, `:316` |
| `tests/llm/test_interface.py` | langchain kwarg assertions (~`:302-385`, `~:723-773`) |

## WHAT

Delete the parameter, its docstring `Args:` line, and every forwarding keyword:

```python
# before
def ask_langchain(question, session_id=None, timeout=30, mcp_config=None,
                  execution_dir=None, env_vars=None, system_prompt=None,
                  project_prompt=None) -> LLMResponseDict: ...

# after
def ask_langchain(question, session_id=None, timeout=30, mcp_config=None,
                  env_vars=None, system_prompt=None,
                  project_prompt=None) -> LLMResponseDict: ...
```

Same removal in `ask_langchain_stream`, the two private `_ask_agent*` helpers, and:

```python
async def run_agent(question, chat_model, messages, mcp_config_path, session_id,
                    env_vars=None, timeout=30, system_messages=None) -> tuple[...]

async def run_agent_stream(question, chat_model, messages, mcp_config_path, session_id,
                           cancel_event=None, env_vars=None, tools=None,
                           system_messages=None) -> AsyncIterator[StreamEvent]
```

Also delete the now-pointless `# pylint: disable=unused-argument` comment on `run_agent_stream`
and the `execution_dir: Optional working directory (reserved for future).` docstring lines
(`agent.py:423`, `:493`) and `execution_dir: Optional working directory for agent execution.`
(`__init__.py:285`, `:409`, `:518`, and in `ask_langchain_stream`).

## HOW — integration points

- `run_agent` forwards to `run_agent_stream` by keyword inside `_drain()` (`agent.py:450-459`)
  — drop `execution_dir=execution_dir` there.
- `_ask_agent` / `_ask_agent_stream` forward to `run_agent*` by keyword
  (`__init__.py:435`, `:551`) — drop the same line.
- `ask_langchain` / `ask_langchain_stream` forward to `_ask_agent*` (`__init__.py:318`, `:647`)
  — drop the same line.
- `interface.py` stops passing `execution_dir=execution_dir` in the two langchain branches.
  **`prompt_llm`'s own signature is untouched in this step** — the parameter still exists and
  is still used by the Claude and Copilot branches.
- Deleting a middle positional-or-keyword parameter shifts positions; all callers use
  keywords, so no positional call needs fixing. Confirm with a project-wide search for
  `run_agent(` / `ask_langchain(` before committing.

## DATA

No return values or data structures change. `LLMResponseDict` / `StreamEvent` untouched.

## TDD

1. **Tests first.** In `test_langchain_coverage_gaps.py`, delete the `execution_dir=` keyword
   from the calls at `:168`, `:232`, `:269`, `:316` and drop the assertions that it is
   forwarded (`:173`, `:233`, `:273`). Where a test exists *only* to assert forwarding, delete
   the test. In `tests/llm/test_interface.py`, remove `execution_dir` from the expected-kwargs
   dicts of the langchain assertions only — leave the Claude/Copilot ones alone.
2. Run the suite: the langchain tests now fail with `unexpected keyword argument` on the
   assertion side, or pass trivially.
3. **Implementation.** Delete the parameter from the six functions and the two `interface.py`
   forwarding lines.
4. Quality gate (all three MCP checks). Langchain integration tests are marker-excluded from
   the fast run; if `langchain_integration` tests reference the parameter, fix them in this
   step too.

## Commit

```
Remove execution_dir from langchain provider

It runs in-process and has no subprocess to place; the parameter was
already unused and annotated as such. Part of #1132.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`, then implement step 1 only.
>
> Delete the `execution_dir` parameter from `ask_langchain`, `ask_langchain_stream`,
> `_ask_agent` and `_ask_agent_stream` in
> `src/mcp_coder/llm/providers/langchain/__init__.py`, and from `run_agent` and
> `run_agent_stream` in `src/mcp_coder/llm/providers/langchain/agent.py` — including every
> forwarding keyword argument, the docstring `Args:` lines, and the now-obsolete
> `# pylint: disable=unused-argument` comment. In `src/mcp_coder/llm/interface.py`, stop
> passing `execution_dir=` in the two langchain branches **only**; do not change
> `prompt_llm`'s or `prompt_llm_stream`'s own signature — that is step 4.
>
> Follow TDD: update the affected tests first
> (`tests/llm/providers/langchain/test_langchain_coverage_gaps.py` and the langchain
> assertions in `tests/llm/test_interface.py`), then make the source change.
>
> Use MCP tools exclusively (`mcp__workspace__*` for files). Finish with
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` (with
> `extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not
> claude_api_integration and not formatter_integration and not github_integration and not
> langchain_integration"]`) and `mcp__tools-py__run_mypy_check`; all three must pass. One
> commit for this step.
