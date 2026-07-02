# Summary — Unify Claude blocking/streaming onto one streaming core

Issue #1004. Collapse the Claude provider's two parallel execution paths into **one
streaming core**. The blocking entrypoint becomes a thin **drain-wrapper**: it consumes
the streaming generator to completion, assembles the result, translates errors, and runs
the `log_llm_*` side-effects. Then sweep every blocking caller onto an **inactivity**
timeout and add a distinct `mcp_unavailable` failure category.

## Goal / requirements preserved

- One streaming core; **blocking = drain + assemble**; the drain-wrapper is **retry-free**
  (post-#999 the blocking path is already single-attempt).
- Unified `raw_response` is the assembler's **`events`** shape, extended with **`stream_file`**.
  `llm_response["text"]` and `store_session(...)` keep working unchanged. Top-level `text` stays
  **byte-identical** (AC3): the assembler `.strip()`s the concatenated `text_delta` text and falls
  back to the result message's `result` value when no assistant text was seen (parity with
  `parse_stream_json_lines`).
- `prompt --json`'s nested `raw_response` shifts `messages`→`events`; top-level
  `text`/`session_id` unchanged (accepted — Decision 11).
- **Every** blocking caller uses a documented per-site **inactivity** timeout below the CI
  step cap. Two categories: the three **tool-using** sites (implement, mypy-fix, CI-fix) use a new
  `LLM_INACTIVITY_TIMEOUT_SECONDS = 600` (headroom for silent MCP tool calls); the **pure-LLM**
  sites (CI-analysis `300`, commit-msg `120`) stay lower. All other callers
  (create-plan, create-pr `300`, finalisation `600`, task-tracker-prep `600`) are re-documented as
  inactivity budgets; `create_plan` `PROMPT_3_TIMEOUT` drops 900 → 600. No caller keeps 3600s
  wall-clock; **no** overall wall-clock cap; `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` is not relabeled.
- Inactivity: the drain-wrapper distinguishes the timeout error-event from a generic error via
  a **structured discriminator** (`reason`), re-raises `TimeoutExpired` → reused
  `interface.py` `LLMTimeoutError` mapping → `"timeout"` → `llm_timeout` label. No in-workflow
  timeout retry.
- `LLMTimeoutError` and `McpServersUnavailableError` categorized at **all four autonomous
  sites** (implement, mypy-fix, CI-analysis via a shared exception→reason helper; **CI-fix
  absorbs** both into its 4-attempt loop → `ci_fix_needed`), mapping to `llm_timeout` and the
  new `MCP_UNAVAILABLE` category + `mcp_unavailable` label. The pre-existing mypy-fix timeout
  hole is fixed.
- Side-effect parity: `log_llm_request` / `log_llm_response` / `log_llm_error`, two-phase
  MLflow wrapping (kept at `prompt_llm` level), and the **incremental (per-line flush)** NDJSON
  stream log.

## Architectural / design changes

1. **Single execution path.** `ask_claude_code_cli` stops calling `execute_subprocess` and its
   own MCP guard / stream parser. It now iterates `ask_claude_code_cli_stream` (the streaming
   core, which uses `stream_subprocess` with an **inactivity** watchdog). Net effect: the
   duplicated MCP guard, `parse_stream_json_string`, `result.timed_out`/`return_code` handling,
   and the write-once NDJSON dump are **deleted** — the blocking wrapper shrinks from ~230 to
   ~50 lines. This removes the "fix the guard twice" tax.

2. **Timeout model flips from wall-clock to inactivity for blocking callers.** Because the core
   is now `stream_subprocess(inactivity_timeout_seconds=timeout)`, each caller's `timeout`
   becomes an *inactivity* budget (max seconds with no stdout line from `claude`, NOT wall-clock).
   This is made conscious per site and split into two categories: tool-using autonomous sites
   (implement, mypy-fix, CI-fix) use a new `LLM_INACTIVITY_TIMEOUT_SECONDS = 600` — 600s (not ~300)
   because a silent MCP tool call (e.g. a multi-minute `run_pytest`) can go >300s without stdout;
   pure-LLM sites (CI-analysis `300`, commit-msg `120`) stay lower since an LLM emits a token
   quickly. Existing numbers are re-documented elsewhere. Eliminates the #1011 SIGKILL race where a
   3600s wall-clock lost to a ~10-min external watchdog.

3. **Unified response contract = `events` shape.** `ResponseAssembler` is the single producer of
   `LLMResponseDict` for both paths, extended to carry `stream_file`. `prompt --json` and the
   workflows move off `messages` for free (no production reader depends on it; `session_info`,
   read by `store_session`/`mlflow_metrics`, is absent from both shapes and keeps falling back).

4. **Error contract: provider raises, workflow categorizes.** The streaming core yields a
   timeout error-event with a machine-readable `reason` and raises `McpServersUnavailableError`
   mid-iteration. The drain-wrapper turns the timeout event into `TimeoutExpired` (reusing the
   existing `interface.py` → `LLMTimeoutError` bridge) and lets `McpServersUnavailableError`
   propagate. A new `MCP_UNAVAILABLE` category keeps a persistent MCP config fault distinguishable
   from a transient timeout on the dashboard. A shared `llm_failure_reason()` helper maps both
   exceptions to reasons/labels at the four autonomous sites; CI-fix's existing broad `except`
   already absorbs them into its retry loop.

## Files to create / modify

**Modified — production**
- `src/mcp_coder/llm/types.py` — `ResponseAssembler` captures `stream_file`.
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — emit `stream_file` event;
  add `reason` discriminator to error events.
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — rewrite `ask_claude_code_cli` as the
  drain-wrapper; delete `create_response_dict_from_stream` and now-dead imports/constants.
- `src/mcp_coder/workflows/implement/constants.py` — add `LLM_INACTIVITY_TIMEOUT_SECONDS`,
  `FailureCategory.MCP_UNAVAILABLE`; remove stale CI comment.
- `src/mcp_coder/workflows/implement/task_processing.py` — repoint timeouts; categorize
  timeout/MCP-unavailable at implement + mypy-fix.
- `src/mcp_coder/workflows/implement/ci_operations.py` — repoint CI-fix timeout; CI-analysis
  propagates the two exceptions; CI-fix keeps absorbing.
- `src/mcp_coder/workflows/implement/core.py` — map `mcp_unavailable` reason; wrap final-mypy and
  `check_and_fix_ci` for categorization.
- `src/mcp_coder/config/labels.json` — add `mcp_unavailable` label.
- `src/mcp_coder/workflows/create_plan/core.py` — timeout doc comments; `PROMPT_3_TIMEOUT` 900 → 600.
- `src/mcp_coder/workflows/create_pr/core.py` — timeout doc comment (`timeout=300`).
- `src/mcp_coder/utils/workflow_utils/commit_operations.py` — `LLM_COMMIT_TIMEOUT_SECONDS = 120`
  doc comment (inactivity budget).
- `docs/architecture/architecture.md` — describe the single streaming core.

**Created — production**
- `src/mcp_coder/workflows/implement/llm_failures.py` — shared `llm_failure_reason()` +
  `REASON_TO_CATEGORY`.

**Created / modified — tests**
- `tests/llm/test_types.py`, `tests/llm/providers/claude/test_claude_cli_stream_*` (Step 1)
- `tests/llm/providers/claude/test_claude_code_cli.py`, `test_claude_cli_wrappers.py`,
  `test_claude_code_cli_heartbeat.py`, `tests/llm/test_interface.py`,
  `tests/cli/commands/test_prompt.py` (Step 2)
- `tests/workflows/implement/test_constants.py` and callers asserting timeouts (Step 3)
- `tests/workflows/implement/test_llm_failures.py`, `tests/config/test_label_config.py` (Step 4)
- `tests/workflows/implement/test_task_processing.py`, `test_core.py` (Steps 5–6)
- `tests/workflows/implement/test_ci_operations.py` (Step 6)

## Steps (one commit each)

1. **step_1** — Streaming core additions: assembler `stream_file` + text parity (strip + result-field fallback) + `reason` discriminator + `stream_file` event.
2. **step_2** — Rewrite `ask_claude_code_cli` as the retry-free drain-wrapper (+ docs, + `prompt --json` shape).
3. **step_3** — Timeout sweep: `LLM_INACTIVITY_TIMEOUT_SECONDS = 600` (tool-using) + pure-LLM sites, repoint callers, per-site doc comments.
4. **step_4** — `MCP_UNAVAILABLE` category + `mcp_unavailable` label + `llm_failure_reason` helper.
5. **step_5** — Categorize timeout/MCP-unavailable at implement + mypy-fix sites (fixes the mypy hole).
6. **step_6** — Categorize at CI sites: CI-analysis propagates, CI-fix absorbs.

Each step is TDD (tests first), one commit, with pylint + pytest + mypy green.
