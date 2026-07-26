# Issue #1090 — MCP guard: tolerate claude.ai account connectors (needs-auth) + commit hardening

## Problem

The `review-plan` run for #1085 (2026-07-26) went UNSTABLE because of three stacked defects:

1. **Root cause:** The Claude CLI injects claude.ai account-level connectors (`claude.ai Google Drive` etc.) into the session `init` event. On a headless agent they report `needs-auth`. The MCP guard treats any status other than `connected`/`pending` as terminal, so the commit-message LLM call raised `McpServersUnavailableError` even though every *configured* server was healthy.
2. `commit_changes` returns `False` when commit-message generation fails, so the round's work was never committed.
3. The review loop ignores the return values of `commit_changes`/`push_changes` and kept looping over state invisible to CI and reviewers.

## Design changes (architectural summary)

**Part 1 — guard, three independent layers (each alone would have prevented the incident):**

- **Layer 1 (semantics):** `needs-auth` becomes a non-fatal status, tolerated exactly like `pending` in `find_fatal_mcp_servers`. It means "optional unauthenticated account connector", not "crashed server". The guard module exports a `MCP_NEEDS_AUTH_STATUS` constant so consumers classify by status value — no new guard functions, no signature changes to the three existing public helpers.
- **Layer 2 (scoping):** When a session is launched with an explicit `mcp_config`, only servers listed in that file's `mcpServers` can ever be fatal. A new pure helper `load_mcp_server_names()` parses the config (relative paths resolved against the subprocess `cwd`, i.e. `execution_dir`) **before the subprocess launches**; a missing/unreadable/malformed file raises `ValueError` naming the file (operator error — fail fast, per issue decision). Scoping is applied as a dict filter at the single abort site in `ask_claude_code_cli_stream` — the guard module's public API is unchanged. With `mcp_config=None` behavior is unchanged (guard everything; layer 1 still applies).
- **Layer 3 (hermetic workflow-internal LLM calls):** `commit_changes` and `generate_commit_message_with_llm` accept and forward all three session params (`mcp_config`, `execution_dir`, `settings_file`), and every workflow caller passes them, so the commit-message call runs with `--mcp-config`/`--strict-mcp-config`, a pinned cwd, and `--settings` exactly like the workflow's main sessions. Explicitly **not** doing the `LLMSessionParams` dataclass bundling (deferred by the issue). The interactive `mcp-coder commit` keeps `mcp_config=None` on purpose.
- **Presentation:** `env_setup`'s probe status stays `connected` and `verify_formatting`'s row stays OK when the only non-connected servers are `needs-auth`; both list those connectors at info level, labeled as unauthenticated account connectors outside the configured-server health assessment. No new status bucket.

**Part 2 — fallback commit message:** On LLM generation failure, `workflow_steps/commit.py` logs the error and commits with the static message `chore: automated commit (message generation failed)` (no error text in git history). The fallback lives ONLY there — the shared `generate_commit_message_with_llm` and the interactive `mcp-coder commit` keep failing loudly. A clean tree intentionally flows through the fallback: `commit_all_changes` no-ops with `success=True`, so `commit_changes` returns `True` — this is load-bearing for Part 3.

**Part 3 — review loop fails on commit/push failure:** `run_review_workflow` checks both return values; on `False` it writes a round-log entry naming the failed step and routes through the existing `_fail(...)` path with reason `commit-failed` / `push-failed` (unknown reason keys fall back to the `general` failure label by design — no new label config needed). Depends on Part 2: without the fallback, transient LLM failures would abort whole runs.

## Step / commit plan (one commit per step, TDD)

| Step | Content |
|------|---------|
| 1 | Layer 1: `needs-auth` non-fatal in guard + streaming log split |
| 2 | Layer 2: `load_mcp_server_names()` + positive-list scoping at the abort site |
| 3 | Presentation: `env_setup` probe classification |
| 4 | Presentation: `verify_formatting` MCP tools row |
| 5 | Layer 3: thread `mcp_config`/`execution_dir`/`settings_file` through the commit path |
| 6 | Part 2: fallback commit message in `commit_changes` |
| 7 | Part 3: review loop fails on commit/push failure |

Steps 1–5 are independent of each other. Step 7 requires step 6.

## Files modified (no new modules)

Source:
- `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py` (steps 1, 2)
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` (steps 1, 2)
- `src/mcp_coder/icoder/env_setup.py` (step 3)
- `src/mcp_coder/cli/commands/verify_formatting.py` (step 4)
- `src/mcp_coder/workflow_utils/commit_operations.py` (step 5)
- `src/mcp_coder/workflow_steps/commit.py` (steps 5, 6)
- `src/mcp_coder/workflow_steps/ci.py` (step 5)
- `src/mcp_coder/workflows/implement/core.py` (step 5)
- `src/mcp_coder/workflows/implement/task_processing.py` (step 5)
- `src/mcp_coder/workflows/implement/finalisation.py` (step 5)
- `src/mcp_coder/cli/commands/commit.py` (step 5 — comment only)
- `src/mcp_coder/workflows/review/core.py` (steps 5, 7)

Tests (all existing files, extended):
- `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py` (steps 1, 2)
- `tests/icoder/test_env_setup.py` (step 3)
- `tests/cli/commands/test_verify_format_mcp_section.py` (step 4)
- `tests/workflow_utils/test_commit_operations.py` (step 5)
- `tests/workflow_steps/test_commit.py` (steps 5, 6)
- `tests/workflows/review/test_core.py` (step 7)

## Quality gates (every step, via MCP tools)

- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
- `mcp__tools-py__run_mypy_check`
- `./tools/format_all.sh` before each commit.
