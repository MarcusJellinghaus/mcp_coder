# Step 6 — Confirm settings + full quality gates

**Goal:** verify no setting re-disables the wait bridge, and the whole change is
green across the toolchain.

## WHAT
1. **Confirm settings (acceptance):** `.claude/settings.local.json` does not deny
   `ToolSearch` and does not set `ENABLE_TOOL_SEARCH=false` (would force the
   `WaitForMcpServers` path instead). Already verified during analysis — re-check
   after the change and note it. No edit expected.
2. **Dead-reference sweep:** confirm no remaining imports/usages of the removed
   symbols (`MCP_UNAVAILABLE_MAX_RETRIES`, `MCP_UNAVAILABLE_RETRY_WAIT_SECONDS`,
   `_MCP_RETRYABLE_STATUSES`, `mcp_failure_is_retryable`) in src or tests.
3. **Vulture / unused:** ensure no newly-unused code is left behind.

## Quality gates (run in order)
- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_ruff_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` — fast suite:
  `["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_pytest_check` markers=`["claude_cli_integration"]` for Step 5.
- `mcp__mcp-tools-py__run_lint_imports_check` (mcp_coder_utils isolation etc.)

All must pass before commit.

## LLM prompt
> Implement Step 6 from `pr_info/steps/summary.md`. Confirm the settings
> acceptance criterion, sweep for dead references to the removed retry symbols,
> and run the full quality-gate sequence (format, ruff, pylint, mypy, fast
> pytest, claude_cli_integration pytest, lint-imports). Fix until all green.
