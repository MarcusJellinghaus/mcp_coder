# Step 2: Remove `claude_code_api` support and the `method` parameter

## Overview
Simplify the LLM provider interface from `(provider, method)` pairs to just `provider`. The `claude_code_api` method is being discontinued. After this change, the only valid providers are `"claude"` (always uses CLI) and `"langchain"`.

## Files to change (in dependency order)

### 2a. `src/mcp_coder/llm/session/resolver.py`
- Simplify `parse_llm_method()` to return just `provider: str` (not a tuple)
- Remove `claude_code_api` case
- Valid inputs: `"claude_code_cli"` → `"claude"`, `"langchain"` → `"langchain"`
- Keep accepting `"claude_code_cli"` as input for CLI `--llm-method` compatibility

### 2b. `src/mcp_coder/cli/utils.py`
- Update `parse_llm_method_from_args()` to return just `provider: str`
- Update callers' unpacking from `provider, method = ...` to `provider = ...`

### 2c. `src/mcp_coder/llm/interface.py` — Core branching logic
- Remove `method` parameter from `ask_llm()` and `prompt_llm()`
- Remove import of `ask_claude_code_api`
- In `prompt_llm()`: remove the `method == "cli"` / `method == "api"` branching
- Claude provider always calls `ask_claude_code_cli()` directly
- Langchain path is unchanged (already ignores `method`)

### 2d. CLI commands — remove `method` from all callers
Each CLI command parses `parse_llm_method_from_args()` and passes `provider, method` to workflow functions. Update all to pass just `provider`:
- `src/mcp_coder/cli/commands/commit.py`
- `src/mcp_coder/cli/commands/create_plan.py`
- `src/mcp_coder/cli/commands/implement.py`
- `src/mcp_coder/cli/commands/create_pr.py`
- `src/mcp_coder/cli/commands/prompt.py`
- `src/mcp_coder/cli/commands/check_branch_status.py`

### 2e. Workflow functions — remove `method` parameter
Remove `method` from function signatures, pass only `provider` to LLM interface:
- `src/mcp_coder/workflows/create_plan.py` — `run_create_plan_workflow()`, `run_planning_prompts()`
  - **Also removes the buggy `llm_method = f"{provider}_code_{method}"` reconstruction (line 540)**
- `src/mcp_coder/workflows/implement/core.py` — `ImplementConfig`, `run_implement_workflow()`, and internal functions
- `src/mcp_coder/workflows/create_pr/core.py` — `run_create_pr_workflow()`, `_generate_pr_summary()`
- `src/mcp_coder/workflow_utils/commit_operations.py` — `generate_commit_message_with_llm()`
- `src/mcp_coder/workflows/implement/task_processing.py` — all functions with `method` param

### 2f. Logging utilities — remove `method` parameter
- `src/mcp_coder/llm/providers/claude/logging_utils.py` — `log_llm_request()`, `log_llm_response()`, `log_llm_error()`
- Update log messages/tags to use `provider` instead of `method`

### 2g. `src/mcp_coder/llm/providers/claude/claude_code_api.py`
- Do NOT delete the file in this PR (may have other consumers)
- Remove the import from `interface.py`

### 2h. Documentation
- `docs/cli-reference.md` — update `--llm-method` descriptions to remove `claude_code_api` references

## Rationale
- `claude_code_api` is not actively used and adds unnecessary complexity
- The `method` parameter threads through ~15 function signatures but only branches in one place (`prompt_llm`)
- With only two providers (`claude`, `langchain`), branching on `provider` alone is sufficient
- This also fixes the reconstruction bug (`langchain_code_api`) by eliminating the need for reconstruction entirely
