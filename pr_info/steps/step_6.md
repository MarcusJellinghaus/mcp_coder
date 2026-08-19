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
  `messages` captured from turn 1's store call — patch
  `mcp_coder.llm.storage.session_storage.store_langchain_history` with the mock you read
  that from, so nothing touches the user's real session directory.
* **Mock-class rule — applies to both agent tests in this step** (the unit-level one above
  and the end-to-end one below). The stubbed react agent must be a
  `MagicMock()`, **never** an `AsyncMock()` — `run_agent_stream` does
  `async for event in agent.astream_events(...)`, and an `AsyncMock` child call returns a
  coroutine, which `async for` rejects with
  `TypeError: 'async for' requires an object with __aiter__ method, got coroutine`. Same
  rule as step 4's conftest-helper note and step 5's conversions;
  `_patch_run_agent_stream` (`test_langchain_agent_streaming.py:41`) is the reference
  shape.
* **Agent path (end-to-end, `test_icoder_agent_flow_...`):** the unit-level agent test
  above hand-builds `system_messages` and hand-feeds turn-2 history, so on the agent side
  neither the merge (`_build_system_messages`) nor the store→load round trip is exercised
  — i.e. not the flow icoder actually ran when the bug was reported (the text-path test
  covers the merge, but only for `_ask_text_stream`). This third test closes that gap and is
  what makes the issue's acceptance criterion ("stub model that rejects >1
  `SystemMessage` passes across two turns **with a system + project prompt**") true for
  the agent path:
  * Drive `ask_langchain_stream(question, session_id=sid, mcp_config="ignored.json",
    tools=[], system_prompt="sys", project_prompt="proj")` twice with the **same**
    `session_id`, so the call goes through `_build_system_messages` → `_ask_agent_stream`
    (thread+queue bridge) → `run_agent_stream`, exactly as icoder does.
  * **Pass `tools=[]`.** `ask_langchain_stream` forwards `tools` to `_ask_agent_stream`
    (`__init__.py:591`) and on to `run_agent_stream` (`:494`), which short-circuits on
    `if tools is not None` (`agent.py:525`) and skips `_load_mcp_server_config` and
    `MultiServerMCPClient` entirely. Without it the test would fail before reaching the
    model: `_load_mcp_server_config` reads `mcp_config` from disk and raises on a path that
    does not exist. `mcp_config` still has to be truthy — it is what routes
    `ask_langchain_stream` to the agent branch — but its value is never read.
  * Use the **real** `store_langchain_history` / `load_langchain_history`: patch
    `mcp_coder.llm.storage.session_storage.get_user_app_data_dir` to return `tmp_path`,
    so turn 1 writes a real JSON file and turn 2 loads it back. This also pins that the
    serialized shape survives a JSON round trip and rehydrates via `messages_from_dict`
    — something an in-memory hand-off cannot show.
  * With `tools=[]` the patch set is exactly four: `_load_langchain_config`,
    `_create_chat_model`, `agent._check_agent_dependencies` and
    `langgraph.prebuilt.create_react_agent` (whose `astream_events` runs the guard on
    `input["messages"]`, then yields `graph_events(...)` with a terminal event so turn 1
    really stores). No MCP patches are needed — that is the point of `tools=[]`.
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

The end-to-end test must go through ask_langchain_stream(..., mcp_config=<any truthy
value>, tools=[]) so it exercises _build_system_messages (the merge) and
_ask_agent_stream, and must use the real store_langchain_history / load_langchain_history
with mcp_coder.llm.storage.session_storage.get_user_app_data_dir patched to tmp_path — do
not hand-build system_messages or hand-feed turn-2 history there. tools=[] is what makes
run_agent_stream skip _load_mcp_server_config and MultiServerMCPClient, so the only
patches needed are _load_langchain_config, _create_chat_model,
agent._check_agent_dependencies and langgraph.prebuilt.create_react_agent.

MOCK CLASS: in both agent tests the stubbed react agent must be a MagicMock(), NOT an
AsyncMock() — run_agent_stream does `async for event in agent.astream_events(...)`, and an
AsyncMock child call returns a coroutine, which async for rejects ("TypeError: 'async for'
requires an object with __aiter__ method, got coroutine").

No production logic changes in this step. Run pylint, pytest and mypy via the MCP tools,
plus one full pytest run without the marker exclusions. Then report the manual
verification status honestly — if no LiteLLM/Qwen endpoint is available, say so instead
of claiming the acceptance criteria are met.

Produce exactly one commit.
```

---

## Implementation note (step 6 run)

### What was added

`tests/llm/providers/langchain/test_langchain_multi_turn.py` (185 → 407 lines, under the
750-line gate) gained the shared `_reject_multiple_systems()` guard, a
`_guarded_react_agent()` factory (a `MagicMock()`, per the mock-class rule) and
`TestSingleSystemProviderRejection` with all three tests. `docs/architecture/architecture.md`
gained the `agent.py` / `_messages.py` bullets and the system-free-history note on the
session-storage bullet. **No production code was touched** — `git status` shows exactly two
modified files.

### The tests are not vacuous — mutation-checked

Tightening the guard's threshold from `> 1` to `> 0` made **all three** tests fail with
`ValueError: system messages must be at the beginning`, proving the guard is actually
reached on each path and that the exception propagates out of `ask_langchain_stream` /
`run_agent_stream` rather than being swallowed. The threshold was restored afterwards and
all 5 tests in the file pass.

### Full-suite run — done in chunks, not one invocation

The MCP pytest tool hard-caps a run at 300s; the mandated no-exclusions full-suite run
exceeds that (it timed out at 300s even *with* the marker exclusions). The suite was
therefore covered in five chunks that between them span every directory under `tests/`.
**The langchain directory is fully green apart from one pre-existing failure** (see below).

### Environment caveat — same pre-existing breakage as steps 1–5

The venv's `mcp-workspace` install is still stale: `src/mcp_coder/checks/branch_status.py:17`
imports `mcp_workspace.checks.branch_status_rendering`, which the installed package does not
have, and its `CIStatus` lacks the `UNAVAILABLE` / `UNKNOWN` members. That import runs at
`import mcp_coder` time, so every test module fails at import without a workaround. Proven
independently by `tests/cli/test_main.py::TestFaulthandlerSafetyNet::test_faulthandler_enabled_on_import`,
which shells out to a fresh interpreter and gets the same `ModuleNotFoundError`.

Verification used the same throwaway shim as steps 3–5 (a `sys.modules` stand-in prepended
to `tests/conftest.py`, re-exporting `CIStatus` / `GITHUB_TOKEN_HINT` from
`mcp_workspace.checks.branch_status`). **It was removed before finishing** — `git status`
confirms `tests/conftest.py` is unmodified.

Failures observed across the sweep, all pre-existing and none in code this step touches:

* the `mcp_workspace` skew — `tests/checks/`, `tests/cli/commands/test_check_branch_status*`,
  `tests/workflows/review/`, `tests/utils/test_crash_logging.py`;
* missing optional deps — `test_langchain_exceptions.py::test_connection_errors_contains_httpx_connect_error`
  (`httpx` absent, conftest substitutes a `MagicMock`; the one langchain-directory failure,
  identical before this commit) and `tests/icoder/test_snapshots.py` (`snap_compare` fixture,
  `pytest-textual-snapshot` not installed);
* no credentials — `tests/llm/providers/copilot/test_copilot_integration.py`.

Other checks: **mypy --strict** clean on `src/mcp_coder/llm/providers/langchain` +
`tests/llm/providers/langchain`; **pylint** shows only the project-wide `E0401` baseline for
the deferred optional-dependency imports; **black / isort** no changes; **`check_file_size`**
passes (all 812 files within 750 lines).

### Manual verification — NOT PERFORMED, acceptance criteria NOT confirmed against a real backend

Neither manual step was run:

1. `mcp-coder prompt "hello" --add-system-prompts` — **not run**.
2. A 2+ turn icoder session — **not run**.

There is no LiteLLM/Qwen endpoint configured for this environment, langchain is not installed
in the test venv (the directory conftest substitutes stub message classes, which is why the
unit tests run at all), and this session has no shell with which to invoke the CLI. The
regression is therefore locked in **against a stub** that reproduces LiteLLM's rejection
behaviour, not against the real provider. Together with the still-open gates from steps 4
(root-`run_id` terminal-event assumption vs. real LangGraph) and 5 (`usage` sourced from
`on_chat_model_end` vs. `ainvoke`), the issue's acceptance criteria remain **unverified
end-to-end** and should be exercised manually before merge.
