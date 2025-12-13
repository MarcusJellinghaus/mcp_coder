# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**

1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**

- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Update Windows Templates ([step_1.md](./steps/step_1.md))

- [x] Update `DEFAULT_TEST_COMMAND_WINDOWS` template (add DISABLE_AUTOUPDATER, MCP verification steps, archive listing)
- [x] Update `CREATE_PLAN_COMMAND_WINDOWS` template (add DISABLE_AUTOUPDATER, --update-labels flag, archive listing)
- [x] Update `IMPLEMENT_COMMAND_WINDOWS` template (add DISABLE_AUTOUPDATER, --update-labels flag, archive listing)
- [x] Update `CREATE_PR_COMMAND_WINDOWS` template (add DISABLE_AUTOUPDATER, --update-labels flag, archive listing)
- [x] Update tests in `tests/cli/commands/test_coordinator.py` for Windows templates
- [x] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 1

### Step 2: Update Linux Templates ([step_2.md](./steps/step_2.md))

- [x] Update `DEFAULT_TEST_COMMAND` template (add DISABLE_AUTOUPDATER, MCP verification steps, archive listing)
- [x] Update `CREATE_PLAN_COMMAND_TEMPLATE` template (add DISABLE_AUTOUPDATER, --update-labels flag, change .mcp.linux.json to .mcp.json, archive listing)
- [x] Update `IMPLEMENT_COMMAND_TEMPLATE` template (add DISABLE_AUTOUPDATER, --update-labels flag, change .mcp.linux.json to .mcp.json, archive listing)
- [x] Update `CREATE_PR_COMMAND_TEMPLATE` template (add DISABLE_AUTOUPDATER, --update-labels flag, change .mcp.linux.json to .mcp.json, archive listing)
- [ ] Update tests in `tests/cli/commands/test_coordinator.py` for Linux templates
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all changes across both steps
- [ ] Ensure all quality checks pass (pylint, pytest, mypy)
- [ ] Create PR summary describing the template updates
