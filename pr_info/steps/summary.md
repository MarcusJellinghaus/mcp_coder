# Issue #984 — Surface "MCP tools exposed to model" in verify, icoder & failure output

## Goal

Detection of crashed/missing MCP servers already exists (`claude_mcp_guard.py`,
delivered by #995/#998/#999/#1005). This issue makes the **"MCP tools actually
exposed to the model"** signal *visible* where humans look:

1. A small **tool-list reader** added to the guard (reused by #1006).
2. **`verify`** reports tool status + count from its existing test prompt and
   lets it affect the exit code.
3. The **icoder startup banner** surfaces status + tool count.
4. **Workflow failure output** detects the typed `McpServersUnavailableError`
   and names the unavailable servers.

We are **surfacing** an already-detected signal — not rebuilding detection.

## Design / architecture changes

- **One shared reader, one mechanism.** A single pure function
  `find_exposed_mcp_tools(system_message)` is added next to the existing
  `find_fatal_mcp_servers` / `find_unavailable_mcp_servers` parsers in
  `claude_mcp_guard.py`. It reads the init event's `tools` field and returns the
  `mcp__*` tool names. No new dataclass, no second parser in `utils/`
  (Decision 4). #1006 consumes the same function.
- **Init event is already captured.** For the Claude provider,
  `create_response_dict_from_stream` stores the init `system` event at
  `LLMResponseDict["raw_response"]["system"]`. Both `verify` and icoder read
  that instead of running a dedicated probe (Decision: in-band, no
  `probe_mcp_tools()`):
  - `verify` reuses its existing `"Reply with OK"` test prompt (zero extra cost).
  - icoder runs one lightweight startup prompt (see tradeoff below).
- **Exit policy mirrors the runtime guard** (Decision 5): `connected` → OK,
  `pending` → WARN (never fails — preserves the #999/#1005 cold-start
  self-heal), `failed`/`unknown` **or** `connected`-but-0-tools → exit 1.
- **`alwaysLoad` hint is narrow** (Decision 7): shown *only* in the
  connected-but-0-tools branch. Fatal servers get a generic
  "check server logs / config" hint.
- **Failure output is detection-only, no re-probe** (Decision 6): the guard
  already raised the typed `McpServersUnavailableError` in-band, carrying
  `unavailable_servers`. `failure_handling.py` only formats it.
- **Layering preserved.** `workflow_utils → llm` is an allowed downward
  dependency (tach + import-linter), so importing the typed error into
  `failure_handling.py` introduces no boundary violation. Runtime stays
  status-only (Decision 8): no new "connected-but-0-tools" runtime abort.

### icoder startup tradeoff (Step 3)

icoder has no init event at startup today (it only runs `claude mcp list`, which
exposes connection status but **not** tool counts). To get a real tool count via
the shared reader with the least code, `setup_icoder_environment` runs one
guarded `"Reply with OK"` prompt and reads `raw_response["system"]` — exactly
verify's mechanism. Cost: one short LLM round-trip at startup (Claude provider
only), wrapped in try/except so any failure degrades to "unknown" and never
blocks launch. This is the simplest *code* path; the alternatives (lazy capture
from the first real session, or a dedicated probe) are more plumbing or are out
of scope.

## Folders / modules / files

### Created
- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` … `step_4.md` (this plan).

### Modified — production
| File | Step | Change |
|------|------|--------|
| `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py` | 1 | Add `find_exposed_mcp_tools()`. |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | 1 | Re-export the new function in `__all__`. |
| `src/mcp_coder/cli/commands/verify.py` | 2 | Capture test-prompt response; add tools-exposed row + `alwaysLoad`/generic hint; thread `tools_exposed_ok` into `_compute_exit_code`. |
| `src/mcp_coder/icoder/env_setup.py` | 3 | `RuntimeInfo` gains `mcp_tools_exposed` / `mcp_tools_status`; `setup_icoder_environment` gains `provider` / `mcp_config` params and the guarded probe. |
| `src/mcp_coder/cli/commands/icoder.py` | 3 | Resolve provider + mcp_config before `setup_icoder_environment` and pass them. |
| `src/mcp_coder/icoder/ui/runtime_banner.py` | 3 | Render the tools-exposed line (live + replay). |
| `src/mcp_coder/icoder/core/event_log.py` | 3 | `emit_session_start` includes the two new fields. |
| `src/mcp_coder/workflow_utils/failure_handling.py` | 4 | Add `format_mcp_unavailable_message()`. |
| `src/mcp_coder/workflows/implement/task_processing.py` | 4 | Let the typed error propagate (don't mask as `"error"`). |
| `src/mcp_coder/workflows/implement/core.py` | 4 | Safety-net uses the formatter for the typed error. |
| `src/mcp_coder/workflows/create_plan/core.py` | 4 | Top-level boundary uses the formatter. |
| `src/mcp_coder/workflows/create_pr/helpers.py` | 4 | `handle_create_pr_failure` uses the formatter when given the typed error. |

### Modified — tests
| File | Step |
|------|------|
| `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py` | 1 |
| `tests/cli/commands/test_verify.py` | 2 |
| `tests/icoder/test_env_setup.py` + `tests/icoder/test_runtime_banner.py` (names per existing layout) | 3 |
| `tests/workflow_utils/test_failure_handling.py` | 4 |

## Step overview (one commit each)

| Step | Title | Independent? |
|------|-------|--------------|
| 1 | Tool-list reader in the guard | Yes — pure function + unit tests |
| 2 | `verify` surfacing + exit code + `alwaysLoad` hint | Yes — depends on Step 1's function |
| 3 | icoder startup banner | Yes — depends on Step 1's function |
| 4 | Workflow failure output | Yes — independent of 2 & 3 |

## Conventions

- **TDD**: write the failing test(s) first, then the implementation.
- **One commit per step**: tests + implementation + all checks green.
- After each edit run, in order: `run_pylint_check`, `run_pytest_check`
  (`extra_args=["-n","auto","-m","not git_integration and not
  claude_cli_integration and not claude_api_integration and not
  formatter_integration and not github_integration and not langchain_integration
  and not llm_integration and not textual_integration"]`), `run_mypy_check`.
- Format before committing (`./tools/format_all.sh`).
