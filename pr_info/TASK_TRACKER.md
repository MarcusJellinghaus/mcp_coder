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

### Step 1: Delete `tools/reinstall.bat` ([detail](./steps/step_1.md))
- [ ] Implementation: delete file, remove stale references in `reinstall_local.bat` and `docs/repository-setup.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `chore: delete obsolete PyPI reinstall script (#640)`

### Step 2: Create `pyproject_config.py` with tests ([detail](./steps/step_2.md))
- [ ] Implementation: create `tests/utils/test_pyproject_config.py` and `src/mcp_coder/utils/pyproject_config.py` with `GitHubInstallConfig`, `get_github_install_config`, `get_formatter_config`, `check_line_length_conflicts`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat: add shared pyproject.toml config reader (#640)`

### Step 3: Refactor `config_reader.py` to thin wrapper ([detail](./steps/step_3.md))
- [ ] Implementation: delegate `config_reader.py` to `pyproject_config.py`, refactor `formatters/__init__.py` to use `get_formatter_config`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `refactor: delegate config_reader to pyproject_config (#640)`

### Step 4: Refactor `_build_github_install_section()` + regression test ([detail](./steps/step_4.md))
- [ ] Implementation: create `tests/workflows/vscodeclaude/test_build_github_install_section.py`, refactor `workspace.py` to use `get_github_install_config()`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `refactor: use get_github_install_config in workspace (#640)`

### Step 5: Create `read_github_deps.py` + improve `reinstall_local.bat` ([detail](./steps/step_5.md))
- [ ] Implementation: create `tools/read_github_deps.py`, update `reinstall_local.bat` with silent deactivate and dynamic GitHub deps
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat: dynamic GitHub deps in reinstall_local.bat (#640)`

### Step 6: Add version printing to all four launchers ([detail](./steps/step_6.md))
- [ ] Implementation: add `mcp-workspace --version` and `mcp-tools-py --version` to `claude.bat`, `claude_local.bat`, `icoder.bat`, `icoder_local.bat`; verify `.mcp.json` env var consistency
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat: print MCP server versions in launcher scripts (#640)`

### Step 7: Documentation updates + config system docstrings ([detail](./steps/step_7.md))
- [ ] Implementation: update `user_config.py` docstring, add config systems section to `docs/configuration/config.md`, update `docs/environments/environments.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `docs: document config systems, update environments (#640)`

## Pull Request
- [ ] PR review: verify all steps complete and quality checks pass
- [ ] PR summary: write description with reviewer checklist (`.mcp.json` env var consistency, related issues in other repos)
