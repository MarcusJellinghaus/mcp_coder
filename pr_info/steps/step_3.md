# Step 3 — Text paths adopt the shared helpers

**Goal:** Converge sites 1 and 2 of 4 (`_ask_text`, `_ask_text_stream`). Behaviour is
unchanged — the shared serializer produces byte-identical output to today's inline dump
loops — but the text path is now the same code as the agent path will be.

`_ask_text_stream` is the path `mcp-coder prompt` actually runs, so it is the site the
`--add-system-prompts` repro exercises.

## WHERE

* Modify `src/mcp_coder/llm/providers/langchain/__init__.py` — `_ask_text` (~lines
  296–370) and `_ask_text_stream` (~lines 629–685)
* Create `tests/llm/providers/langchain/test_langchain_multi_turn.py`

## WHAT

No signature changes. Both functions replace their inline assemble block and their
~10-line dump loop with:

```python
lc_messages = assemble_messages(system_messages, history, question)
...
store_langchain_history(session_id, serialize_messages(lc_messages + [ai_msg]))
```

## HOW

* Module-level import in `__init__.py`:
  `from ._messages import assemble_messages, serialize_messages`
  (safe — `_messages` has no intra-package imports).
* `_ask_text`: drop the deferred `from langchain_core.messages import HumanMessage,
  messages_from_dict` (no longer used) and the `history_messages` local.
* `_ask_text_stream`: reduce its deferred import to `AIMessage` only — it still builds
  the final `AIMessage(content=full_text)` from the accumulated deltas.
* Everything else (error handling, `_extract_usage`, 404 hints, timeout watchdog, event
  yielding) is untouched.

## ALGORITHM

```
history      = load_langchain_history(session_id)
lc_messages  = assemble_messages(system_messages, history, question)
ai_msg       = <invoke or stream-then-build AIMessage>
serialize_messages(lc_messages + [ai_msg])  # strips the leading system(s)
store_langchain_history(session_id, <that>)
```

Because `serialize_messages` strips leading systems, the stored list is exactly today's
`history + human + ai` — no behaviour change, one less place to get it wrong.

## DATA

Stored history: `list[dict[str, Any]]`, entries `{"type","data"}`, **no** `"system"`
entries. `LLMResponseDict` / `StreamEvent` output shapes are unchanged.

## Tests (write first)

New file `tests/llm/providers/langchain/test_langchain_multi_turn.py` — the multi-turn
text-path test required by the issue. It must drive the **streaming** text path
(`ask_langchain_stream` without `mcp_config`), because that is what `prompt` uses.

```python
class TestTextPathMultiTurn:
    def test_two_turns_store_no_system_messages_and_send_one(self) -> None: ...
```

Setup: a dict-backed fake for `load_langchain_history` / `store_langchain_history`
patched at `mcp_coder.llm.providers.langchain.<name>`, a `MagicMock` chat model whose
`.stream()` returns one chunk, `_load_langchain_config` and `_create_chat_model` patched
as in the existing tests. Drive two turns with the same `session_id` and both
`system_prompt=` and `project_prompt=` set.

Assertions:

* every stored entry has `entry["type"] != "system"` (both turns);
* `mock_model.stream.call_args_list` — each call's message list contains **exactly one**
  `SystemMessage` and it is at index 0;
* turn 2's message list contains the turn-1 human + AI messages (history really is
  reloaded, so the "no systems" result is not vacuous).

Existing tests in `test_langchain_provider_system_messages.py`,
`test_langchain_provider.py` and `test_langchain_streaming.py` must stay green
unchanged — that is the proof the serializer output is byte-identical.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement step 3 only: make _ask_text and _ask_text_stream in
src/mcp_coder/llm/providers/langchain/__init__.py use assemble_messages() and
serialize_messages() from ._messages, and add
tests/llm/providers/langchain/test_langchain_multi_turn.py with the multi-turn text-path
test described in the step file (it must run through the STREAMING text path).

Write the new test first. Do not touch agent.py in this step. Existing text-path tests
must stay green without modification — if one needs changing, stop and report, because
that means the serialized output is no longer byte-identical.

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```

---

## Implementation note (step 3 run)

**The step-1/2 environment breakage is still present**, but this time the new tests
**were** executed and **passed** via a throwaway shim.

The venv's `mcp-workspace` install is still stale: `src/mcp_coder/checks/branch_status.py:17`
imports `mcp_workspace.checks.branch_status_rendering`, which the installed version does not
have (its `CIStatus` still lives in `mcp_workspace.checks.branch_status`). That import runs at
`import mcp_coder` time (`src/mcp_coder/__init__.py:37`), so the mandated full-suite run still
fails at collection for every module that imports `mcp_coder` — pre-existing, unrelated to this
change, and unfixable here (no shell to reinstall the dependency).

**Workaround used for verification (temporary, not committed).** A throwaway test module
that sorts first alphabetically injected a `mcp_workspace.checks.branch_status_rendering`
stand-in into `sys.modules` (re-exporting `CIStatus` from `mcp_workspace.checks.branch_status`)
before any other module imported `mcp_coder`. With that shim in place the **entire**
`tests/llm/providers/langchain/` directory ran against the real production code. The file was
deleted afterwards; no shim is part of this commit.

Results:

* **New `test_langchain_multi_turn.py` test: PASSED.**
* **Step 1's 8 `test_langchain_messages.py` tests: PASSED** (previously unverified — this
  clears the step-1 caveat).
* **All existing text-path tests passed unmodified** — `test_langchain_provider.py`,
  `test_langchain_streaming.py`, `test_langchain_provider_system_messages.py`,
  `test_langchain_404_hints.py`, `test_langchain_coverage_gaps.py`,
  `test_langchain_provider_usage.py`. This is the byte-identical-serializer proof the step
  asked for; **no existing test needed changing**.
* One pre-existing failure, unrelated to this change:
  `test_langchain_exceptions.py::TestErrorTuples::test_connection_errors_contains_httpx_connect_error`
  — `httpx` is absent, so the conftest injects a `MagicMock` and the assertion
  `httpx.ConnectError in CONNECTION_ERRORS` cannot hold. Fails identically without this commit.

Other checks (run normally, no shim):

* **mypy --strict** on `src/mcp_coder/llm/providers/langchain` + `tests/llm/providers/langchain`:
  clean. Project-wide mypy shows the same 8 pre-existing errors as step 1 (all from the
  `mcp-workspace` skew plus one claude test stub); none in langchain code.
* **pylint**: only `E0401` for the deferred optional-dependency imports (the project-wide
  baseline — langchain/httpx are not installed in the lint env) plus the pre-existing
  `mcp-workspace` skew errors. Nothing new.
* **ruff** (`D`/`DOC`, preview): clean. Fixed one **pre-existing** `D301` introduced by step 2 —
  `_build_system_messages`'s docstring contains `\n\n`, so it is now a raw docstring (`r"""`).
  Docstring text only, no behaviour change.
* **black / isort**: no changes. **file-size gate** (750 lines): passes.
