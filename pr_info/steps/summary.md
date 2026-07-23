# Summary — Fix leaked coroutines in langchain provider sync-path tests (#1081)

## Problem

The unit suite emits misattributed `RuntimeWarning: coroutine '...' was never awaited`
for `run_agent` and `_ask_agent_stream.<locals>._run`. These are **GC-timing artifacts**:
a coroutine is leaked by one test and the warning only surfaces later, blamed on whatever
innocent test the garbage collector happens to run under.

This is **not a production bug** — production always awaits both coroutines. The warning is
a genuine signal that the tests mock at the wrong layer. Because Python evaluates call
arguments before the call, patching `asyncio.run` (non-stream) or `threading.Thread`
(stream) still constructs a **real coroutine object** that is handed to the mock and never
awaited → it leaks and is later GC'd with the warning.

## Fix strategy

Two distinct leaks, two distinct fixes:

1. **Non-stream (`run_agent`) — test-only.** Patch the async boundary function
   `run_agent` with an `AsyncMock` so no coroutine is ever constructed. The live patch
   target is `{_MOD}.agent.run_agent` (the source-module attribute), **not**
   `{_MOD}.run_agent`, because `_ask_agent` imports `run_agent` locally at call time.

2. **Stream (`_run`) — small production hardening.** Construct the `_run()` coroutine
   **lazily inside a named thread target** instead of eagerly as a `Thread` argument. The
   coroutine is then created only when the thread actually runs it, eliminating the leak
   at its source for the timeout test and any future test that mocks `Thread`.

### KISS decisions applied

- Test patches use `new_callable=AsyncMock` with the existing `side_effect=` /
  `return_value=` kwargs forwarded inline. This is the smallest possible diff: each site is
  a target-string swap plus one kwarg; no separate mock variables are introduced.
- The 3 non-stream error-path sites share one idiom in one file, so they are **one commit**
  (sibling tests, same fix — not independent parts).
- No `filterwarnings` ignore and no `filterwarnings = error` (per issue Decisions). Warnings
  stay visible so a real leak always surfaces; "0 warnings" is a one-time manual check.
- No `coro.close()` workaround — the stream leak is fixed in production, not papered over
  in the test.

## Architectural / design changes

- **Async boundary is now the mocking seam (tests).** The provider's sync façade
  (`ask_langchain`) delegates to async agent functions across an `asyncio.run` boundary.
  The tests are realigned to mock the **boundary function** (`run_agent`) rather than the
  boundary *mechanism* (`asyncio.run` / `threading.Thread`). This is a cleaner seam: the
  test controls what the agent returns/raises without depending on how the sync↔async
  bridge is implemented, and no unawaited coroutine is ever created.
- **Lazy coroutine construction in the stream thread (production).** The thread target
  changes from `asyncio.run` with an eagerly-built `_run()` argument to a named
  `_thread_main()` closure that builds and runs the coroutine inside the thread. Marginally
  more robust in production (coroutine created only when it will be awaited) and removes the
  test leak at its root. Behaviour is otherwise unchanged.
- **No public API, signature, data-structure, or config changes.** No new modules. The
  provider's contract, return types (`LLMResponseDict`, `StreamEvent`), and error mapping
  are untouched.

## Folders / modules / files created or modified

**Created:**

- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`, `pr_info/steps/step_3.md`

**Modified (production — 1 file):**

- `src/mcp_coder/llm/providers/langchain/__init__.py` — lazy named thread target in
  `_ask_agent_stream` (around line 503).

**Modified (tests — 2 files):**

- `tests/llm/providers/langchain/test_langchain_provider.py` — 3 non-stream error-path
  sites repointed to `{_MOD}.agent.run_agent` with `new_callable=AsyncMock`; add `AsyncMock`
  import.
- `tests/llm/providers/langchain/test_langchain_provider_system_messages.py` —
  `test_agent_mode_passes_system_messages` repointed to `{_MOD}.agent.run_agent` with
  `new_callable=AsyncMock`; assertion strengthened; add `AsyncMock` import.

**Unchanged (verified correct — do NOT touch):**

- `tests/llm/providers/langchain/test_langchain_agent_timeout.py` — the production change
  resolves its leak; the no-op `Thread` patch is still required for the test's purpose.
- `tests/llm/providers/langchain/test_langchain_ollama_agent.py` — already the correct
  pattern (the capability-missing test raises before `_run()` is constructed).

## Step overview

| Step | Scope | Type | File(s) |
|------|-------|------|---------|
| 1 | Lazy named thread target in `_ask_agent_stream` | Production | `__init__.py` |
| 2 | Repoint 3 non-stream error-path patches to `run_agent` | Test-only | `test_langchain_provider.py` |
| 3 | Repoint + strengthen `test_agent_mode_passes_system_messages` | Test-only | `test_langchain_provider_system_messages.py` |

Each step is exactly one commit: change + passing pylint / pytest / mypy.

## Verification (all steps)

- `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`
- `mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`
- Final manual check: the unit subset reports `... passed, ... skipped, 0 warnings`.
