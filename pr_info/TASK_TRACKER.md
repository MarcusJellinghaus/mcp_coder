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

### Step 1: Adapter floor `>=0.3.0` + runtime capability check

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation: raise `langchain-mcp-adapters` floor to `>=0.3.0` in `pyproject.toml`; add reusable `_assert_tool_interceptors_supported()` helper (guarded `inspect.signature`) in `agent.py`, called from `_check_agent_dependencies()`; tests first (TDD)
- [x] Quality checks: pylint, pytest, mypy (+ ruff, lint-imports) — fix all issues
- [x] Commit message prepared: `I2.3 step 1: raise langchain-mcp-adapters floor to >=0.3.0 with capability check`

### Step 2: Unify the three tool-build loops + `MCPManager` interceptor param (D1)

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation: extract `_convert_server_tools()` helper; rewire `run_agent`, `run_agent_stream` (else-branch), and `MCPManager._connect_and_discover`; add pass-through `tool_interceptors` param to `MCPManager.__init__`; preserve launch-error handling + canonical-name stamping; tests first (TDD)
- [x] Quality checks: pylint, pytest, mypy (+ ruff, lint-imports) — fix all issues
- [x] Commit message prepared: `I2.3 step 2: unify MCP tool-build loops into one interceptor-aware helper`

### Step 3: Gateway core — turn filter + interceptor + frame builder + deny bridge (D3/D4/D5)

Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation: add `permission_bridge.build_deny_tool_message`, `gateway.build_legacy_frame` (returns `(frame, warnings)`), `gateway.LangchainEnforcementGateway` (`begin_turn`/`filter_tools`/async `interceptor`); narrow `permissions_leaf_isolation` import-linter contract; tests first (TDD)
- [x] Quality checks: pylint, pytest, mypy (+ ruff, lint-imports) — fix all issues
- [x] Commit message prepared: `I2.3 step 3: enforcement gateway (turn filter + call interceptor + frame + deny bridge)`

### Step 4: Turn-level integration in `RealLLMService`; remove I1.1 filter (D5)

Detail: [step_4.md](./steps/step_4.md)

- [x] Implementation: add `gateway` param to `RealLLMService`; replace `filter_tools_by_declaration` block in `stream()` with `build_legacy_frame` + `begin_turn` + `filter_tools`; repurpose `permission_warning` emission for malformed tokens; update docstring; delete `filter_tools_by_declaration` + its test file; tests first (TDD)
- [x] Quality checks: pylint, pytest, mypy (+ ruff, lint-imports) — fix all issues
- [x] Commit message prepared: `I2.3 step 4: enforce never/always at turn level in RealLLMService; drop I1.1 filter`

### Step 5: Startup wiring + bypass guard + real-agent integration (D1/D2)

Detail: [step_5.md](./steps/step_5.md)

- [ ] Implementation: in `execute_icoder()` call `_assert_tool_interceptors_supported()` early, `load_permission_config(project_dir)` once, construct gateway, inject `tool_interceptors=[gateway.interceptor]` into `MCPManager`, pass `gateway` to `RealLLMService`; add wiring, bypass-guard (site 2 + site 3), ordering, and `langchain_integration` integration tests first (TDD)
- [ ] Quality checks: pylint, pytest, mypy (+ ruff, lint-imports, `langchain_integration` marker) — fix all issues
- [ ] Commit message prepared: `I2.3 step 5: wire permission gateway into iCoder startup + bypass guard + integration`

## Pull Request

- [ ] PR review: address review feedback across all steps
- [ ] PR summary: write final summary from [summary.md](./steps/summary.md)
