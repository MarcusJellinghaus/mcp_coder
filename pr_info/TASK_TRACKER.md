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

### Step 1: Fix `MultiServerMCPClient` Breaking Change — [step_1.md](./steps/step_1.md)

- [ ] Update tests for `MultiServerMCPClient` plain instantiation (TDD)
- [ ] Remove `async with` context manager from `run_agent()` in `agent.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

### Step 2: Core Resolution Logic — Config Key Rename, Return Type, MCP Auto-detect — [step_2.md](./steps/step_2.md)

- [ ] Update tests for `resolve_llm_method()` return type and env var support (TDD)
- [ ] Update tests for `resolve_mcp_config_path()` with `project_dir` param (TDD)
- [ ] Update tests for `_load_langchain_config()` config key rename (TDD)
- [ ] Implement `resolve_llm_method()` → return `tuple[str, str]` with env var support
- [ ] Implement `resolve_mcp_config_path()` → add `project_dir` param, auto-detect `.mcp.json`
- [ ] Rename config key `provider` → `default_provider` in `langchain/__init__.py`
- [ ] Add commented-out `[llm]` section to `create_default_config()` in `user_config.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

### Step 3: Templates and Help Text Updates — [step_3.md](./steps/step_3.md)

- [ ] Update tests for template changes (TDD)
- [ ] Remove `--llm-method claude` from Windows templates in `templates.py`
- [ ] Add `# TODO` comment to Linux templates
- [ ] Update `--llm-method` help text in `parsers.py` (5 commands)
- [ ] Update `--project-dir` and `--execution-dir` help text in `parsers.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

### Step 4: Update All Command Handler Callers — [step_4.md](./steps/step_4.md)

- [ ] Update tests for all 5 command handlers to mock tuple return (TDD)
- [ ] Update `prompt.py` — destructure tuple, pass `project_dir`
- [ ] Update `implement.py` — destructure tuple, pass `project_dir`
- [ ] Update `create_plan.py` — destructure tuple, pass `project_dir`
- [ ] Update `create_pr.py` — destructure tuple, pass `project_dir`
- [ ] Update `check_branch_status.py` — destructure tuple, pass `project_dir`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

### Step 5: CLI Command Consistency — Verify and Commit Auto — [step_5.md](./steps/step_5.md)

- [ ] Update tests for `verify.py` to use shared `resolve_llm_method()` (TDD)
- [ ] Update tests for `commit.py` to remove `--mcp-config` (TDD)
- [ ] Delete `_resolve_active_provider()` and `_VALID_PROVIDERS` from `verify.py`
- [ ] Add `--llm-method` to verify parser in `parsers.py`
- [ ] Remove `--mcp-config` from commit auto parser in `parsers.py`
- [ ] Update `verify.py` to import and use shared `resolve_llm_method()`
- [ ] Update `commit.py` — destructure tuple, remove `mcp_config` handling, add comment
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

### Step 6: API Parity — Export Missing Python APIs — [step_6.md](./steps/step_6.md)

- [ ] Update tests for new exports in `test_module_exports.py` (TDD)
- [ ] Add exports to `src/mcp_coder/__init__.py` (`verify_claude`, `verify_langchain`, `verify_mlflow`, `generate_commit_message_with_llm`, `collect_branch_status`)
- [ ] Add `collect_branch_status` export to `src/mcp_coder/checks/__init__.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

---

## Pull Request

- [ ] Review all steps are complete and checks pass
- [ ] Run full test suite (including integration markers if applicable)
- [ ] Write PR summary covering all 6 steps
- [ ] Create pull request
