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

### Step 1: Update CLAUDE.md — remaining sections
- [ ] Implementation: update Code Quality Requirements (THREE→FIVE, add lint_imports/vulture bullets and tool names) and add `get_library_source()` to Refactoring row
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `docs: update CLAUDE.md quality checks section and refactoring row`

### Step 2: Add MCP tool references to documentation
- [ ] Implementation: add inline MCP tool notes to `docs/repository-setup.md`, `docs/configuration/claude-code.md`, `docs/processes-prompts/refactoring-guide.md`, `docs/architecture/dependencies/readme.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `docs: add MCP tool references to documentation`

### Step 3: Decouple CI log parser test fixtures from real tool names
- [ ] Implementation: replace real tool names in VULTURE_LOG fixture and assertions with fictional `tool-alpha` / `tool_alpha.sh` in `tests/checks/test_ci_log_parser.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `test: decouple CI log parser fixtures from real tool names`

## Pull Request
- [ ] PR review: verify all steps completed, no regressions
- [ ] PR summary prepared
