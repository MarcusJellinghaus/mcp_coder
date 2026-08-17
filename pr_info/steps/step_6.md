# Step 6 — Single-system-provider regression test + docs

**Goal:** Lock in the original symptom so it cannot come back from *either* path, and
record the design change in the architecture doc. No production logic changes.

## WHERE

* Modify `tests/llm/providers/langchain/test_langchain_multi_turn.py`
* Modify `docs/architecture/architecture.md` (the langchain block, ~lines 204–210)

## WHAT

```python
class TestSingleSystemProviderRejection:
    def test_text_path_two_turns_never_sends_two_systems(self) -> None: ...
    def test_agent_path_two_turns_never_sends_two_systems(self) -> None: ...
```

Plus a shared guard used by both:

```python
def _reject_multiple_systems(messages: list[Any]) -> None:
    """Raise like a single-system provider does when handed >1 SystemMessage."""
```

## HOW

* `_reject_multiple_systems` counts `SystemMessage` instances and raises
  `ValueError("system messages must be at the beginning")` when the count is > 1 —
  reproducing what LiteLLM's transform does for Qwen-class backends.
* **Text path:** a stub chat model whose `.stream()` calls the guard on the message list
  it receives, then yields one chunk. Drive `ask_langchain_stream` (no `mcp_config`) for
  two turns with a system prompt *and* a project prompt, sharing one `session_id` and a
  dict-backed history fake.
* **Agent path:** the stub lives in the mocked react agent — `astream_events` calls the
  guard on `input["messages"]` before yielding `graph_events(...)`. Drive
  `run_agent_stream` for two turns, feeding turn 2 the `messages` captured from turn 1's
  store call.
* Both tests fail loudly (the raised `ValueError` surfaces) if system messages ever
  duplicate or accumulate — the exact original bug, on turn 1 *and* turn 2.

## ALGORITHM

```
guard(messages):
    if sum(isinstance(m, SystemMessage) for m in messages) > 1:
        raise ValueError("system messages must be at the beginning")

turn 1: drive path with system_prompt + project_prompt -> guard passes, capture stored
turn 2: reload the stored history, drive again          -> guard must still pass
assert no stored entry has type == "system"
```

## DATA

No new production data structures. The tests assert on the stored
`list[dict[str, Any]]` and on the message lists handed to the stub.

## Docs

In `docs/architecture/architecture.md`, extend the `langchain/` bullet list:

* `agent.py` — LangGraph ReAct agent; `run_agent_stream` is the single execution and
  storage site, `run_agent` drains it.
* `_messages.py` — shared assemble/serialize helpers used by the text and agent paths.
* Note on the existing session-storage bullet: stored history is **system-free**; system
  prompts are merged into one `SystemMessage` and applied fresh each turn.

Keep it to a few lines — no restructuring of the document.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Also run the full suite once (no `-m` exclusions) before finishing, to catch anything the
exclusion pattern hides.

## Manual verification (report the outcome; do not skip silently)

Against the LiteLLM/Qwen endpoint:

1. `mcp-coder prompt "hello" --add-system-prompts` — completes without error.
2. A 2+ turn icoder session — no `system messages must be at the beginning` on any turn.

These need a configured endpoint. If it is unavailable, say so explicitly rather than
reporting the acceptance criteria as met.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md.

Implement step 6 only: add the single-system-provider rejection regression tests
(text path and agent path, two turns each, system prompt + project prompt) to
tests/llm/providers/langchain/test_langchain_multi_turn.py, and add the short
architecture.md notes described in the step file.

No production logic changes in this step. Run pylint, pytest and mypy via the MCP tools,
plus one full pytest run without the marker exclusions. Then report the manual
verification status honestly — if no LiteLLM/Qwen endpoint is available, say so instead
of claiming the acceptance criteria are met.

Produce exactly one commit.
```
