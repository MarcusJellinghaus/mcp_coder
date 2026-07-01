# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Tool-list reader in the MCP guard
Detail: [step_1.md](./steps/step_1.md) — `feat: add find_exposed_mcp_tools reader to claude_mcp_guard`

- [x] Implementation: add `TestFindExposedMcpTools` tests, then pure `find_exposed_mcp_tools()` in `claude_mcp_guard.py` + re-export from `claude_code_cli.py` (`__all__` + import block)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `verify` surfaces tool status + count (exit-code-affecting)
Detail: [step_2.md](./steps/step_2.md) — `feat: report MCP tools exposed to model in verify`

- [x] Implementation: add tests for `_format_tools_exposed_section` + `tools_exposed_ok` branch, then edit `verify.py` (capture test-prompt response, print tools-exposed row, thread `tools_exposed_ok` into `_compute_exit_code`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: icoder startup banner surfaces tool status + count
Detail: [step_3.md](./steps/step_3.md) — `feat: show MCP tools exposed in icoder startup banner`

- [x] Implementation: add tests for `env_setup`/`runtime_banner`, then add `RuntimeInfo` fields + `_probe_exposed_mcp_tools`, `provider`/`mcp_config` params, wire `icoder.py`, render banner line, include fields in `emit_session_start`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Workflow failure output names unavailable MCP servers
Detail: [step_4.md](./steps/step_4.md) — `feat: surface McpServersUnavailableError in workflow failure output`

- [ ] Implementation: add tests for `format_mcp_unavailable_message` + re-raise regression, then add formatter + typed-error import, `except McpServersUnavailableError: raise` in `task_processing.py`, route implement/create_plan/create_pr failure boundaries through the formatter
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Review PR: verify all acceptance items (1–5) are met and steps are cohesive
- [ ] Write PR summary
