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

### Step 1: Add `mcp_config_ok` exit-code plumbing

See [step_1.md](./steps/step_1.md).

- [ ] Implementation: add `TestMcpConfigExitCode` tests (TDD) + `mcp_config_ok` param and guard in `_compute_exit_code`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Add `_validate_mcp_config`, render the validity row, delete `_collect_mcp_warnings`

See [step_2.md](./steps/step_2.md).

- [ ] Implementation: add `_validate_mcp_config`, wire `MCP CONFIG` row + downstream short-circuit into `execute_verify`, delete `_collect_mcp_warnings`, update tests/conftest
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
