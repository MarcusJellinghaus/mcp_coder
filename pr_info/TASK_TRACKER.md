# Task Tracker — Issue #524

## Step 1: Add `--llm-method claude_code_cli` to Windows templates

- [x] 1a. Add `--llm-method claude_code_cli` to `AUTOMATED_SECTION_WINDOWS` in `src/mcp_coder/workflows/vscodeclaude/templates.py`
- [x] 1b. Add `--llm-method claude_code_cli` to `DISCUSSION_SECTION_WINDOWS` in `src/mcp_coder/workflows/vscodeclaude/templates.py`
- [x] Run pylint, pytest, mypy — fix all issues
- [x] Prepare git commit message for Step 1

## Step 2: Remove `claude_code_api` support and the `method` parameter

- [x] 2a. Simplify `parse_llm_method()` in `src/mcp_coder/llm/session/resolver.py` — return `str` not tuple, remove `claude_code_api`
- [x] 2b. Update `parse_llm_method_from_args()` in `src/mcp_coder/cli/utils.py` — return just `provider: str`
- [x] 2c. Remove `method` param from `ask_llm()` and `prompt_llm()` in `src/mcp_coder/llm/interface.py`, remove `claude_code_api` import and branching
- [x] 2d. Update CLI commands to pass just `provider` (commit, create_plan, implement, create_pr, prompt, check_branch_status)
- [x] 2e. Remove `method` from workflow function signatures (create_plan, implement/core, create_pr/core, commit_operations, task_processing)
- [x] 2e-ii. Remove `method` field from `LLMResponseDict` in `src/mcp_coder/llm/types.py` and all response construction sites
- [x] 2f. Remove `method` param from logging utils in `src/mcp_coder/llm/providers/claude/logging_utils.py` and update all callers
- [x] 2g. Update `claude_code_api.py` — remove import from `interface.py`, update logging calls
- [x] 2h. Update `docs/cli-reference.md` — remove `claude_code_api` references
- [x] Run pylint, pytest, mypy — fix all issues
- [x] Prepare git commit message for Step 2

## Step 3: Update and add tests

- [ ] 3a. Add template regression tests in `tests/workflows/vscodeclaude/test_templates.py`
- [ ] 3b. Update `parse_llm_method` tests in `tests/llm/session/test_resolver.py`
- [ ] 3c. Update CLI utils tests in `tests/cli/test_utils.py`
- [ ] 3d. Update workflow tests (create_plan, prompt_execution, execution_dir_integration, etc.)
- [ ] 3e. Update interface tests for `ask_llm()` / `prompt_llm()` signatures
- [ ] 3f. Add langchain routing unit test (mock-based, verify `prompt_llm(provider="langchain")` routes to `ask_langchain()`)
- [ ] Run pylint, pytest, mypy — fix all issues
- [ ] Prepare git commit message for Step 3

## Pull Request

- [ ] Run full quality checks (pylint, pytest, mypy) on final state
- [ ] Review all changes for completeness against plan
- [ ] Prepare PR summary and description
