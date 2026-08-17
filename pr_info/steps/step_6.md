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
    def test_icoder_agent_flow_two_turns_never_sends_two_systems(
        self, tmp_path: Path
    ) -> None: ...
```

Plus a shared guard used by all three:

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
* **Agent path (unit level):** the stub lives in the mocked react agent —
  `astream_events` calls the guard on `input["messages"]` before yielding
  `graph_events(...)`. Drive `run_agent_stream` for two turns, feeding turn 2 the
  `messages` captured from turn 1's store call.
* **Agent path (end-to-end, `test_icoder_agent_flow_...`):** the two tests above hand-build
  `system_messages` and hand-feed turn-2 history, so between them they exercise neither
  the merge (`_build_system_messages`) nor the store→load round trip — i.e. not the flow
  icoder actually ran when the bug was reported. This third test closes that gap and is
  what makes the issue's acceptance criterion ("stub model that rejects >1
  `SystemMessage` passes across two turns **with a system + project prompt**") true for
  the agent path:
  * Drive `ask_langchain_stream(question, session_id=sid, mcp_config="/tmp/mcp.json",
    system_prompt="sys", project_prompt="proj")` twice with the **same** `session_id`, so
    the call goes through `_build_system_messages` → `_ask_agent_stream` (thread+queue
    bridge) → `run_agent_stream`, exactly as icoder does.
  * Use the **real** `store_langchain_history` / `load_langchain_history`: patch
    `mcp_coder.llm.storage.session_storage.get_user_app_data_dir` to return `tmp_path`,
    so turn 1 writes a real JSON file and turn 2 loads it back. This also pins that the
    serialized shape survives a JSON round trip and rehydrates via `messages_from_dict`
    — something an in-memory hand-off cannot show.
  * Patch only `_load_langchain_config`, `_create_chat_model`,
    `agent._check_agent_dependencies` and the react agent (whose `astream_events` runs
    the guard on `input["messages"]`, then yields `graph_events(...)` with a terminal
    event so turn 1 really stores).
  * Assert: no `ValueError` on either turn; the on-disk history after each turn has zero
    `"system"` entries; turn 2's `input["messages"]` starts with exactly one
    `SystemMessage` whose content is the merged `"sys\n\nproj"`; and turn 2's input
    contains turn 1's human + AI messages (so the "no systems" result is not vacuous).
* All three tests fail loudly (the raised `ValueError` surfaces) if system messages ever
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

For `test_icoder_agent_flow_...` the reload in turn 2 is not simulated — the production
`load_langchain_history` reads the file the production `store_langchain_history` wrote
under `tmp_path`.

## DATA

No new production data structures. The tests assert on the stored
`list[dict[str, Any]]` (in memory for the two unit-level tests, on disk under `tmp_path`
for the end-to-end one) and on the message lists handed to the stub.

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
(text path, agent path, and the end-to-end icoder agent flow — two turns each, system
prompt + project prompt) to
tests/llm/providers/langchain/test_langchain_multi_turn.py, and add the short
architecture.md notes described in the step file.

The end-to-end test must go through ask_langchain_stream(..., mcp_config=...) so it
exercises _build_system_messages (the merge) and _ask_agent_stream, and must use the real
store_langchain_history / load_langchain_history with
mcp_coder.llm.storage.session_storage.get_user_app_data_dir patched to tmp_path — do not
hand-build system_messages or hand-feed turn-2 history there.

No production logic changes in this step. Run pylint, pytest and mypy via the MCP tools,
plus one full pytest run without the marker exclusions. Then report the manual
verification status honestly — if no LiteLLM/Qwen endpoint is available, say so instead
of claiming the acceptance criteria are met.

Produce exactly one commit.
```
