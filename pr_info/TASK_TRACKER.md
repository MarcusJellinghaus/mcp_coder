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

### Step 1: Shared walk `mcp_coder_section` in `config/toml_utils.py` — [step_1.md](./steps/step_1.md)

- [x] Implementation: `TestMcpCoderSection` tests + `mcp_coder_section`; `find_mcp_coder_table` uses it
- [x] Quality checks (pylint, pytest, mypy, ruff) — fix all issues
- [x] Commit message prepared

### Step 2: `_pyproject_section` + legacy `implement` readers — [step_2.md](./steps/step_2.md)

- [ ] Implementation: `TestNonTableImplement`, malformed-file and `check_formatter_config` tests + `_pyproject_section`; rewire `has_legacy_format_code_key` and `get_leftover_check_type_hints`
- [ ] Quality checks (pylint, pytest, mypy, ruff) — fix all issues
- [ ] Commit message prepared

### Step 3: Install readers and `get_github_install_config` — [step_3.md](./steps/step_3.md)

- [ ] Implementation: reader, install, project-setup and vscodeclaude policy tests + rewire `get_install_extras`, `get_post_install_checks`, `get_github_install_config`; `InstallConfig.from_args` docstring
- [ ] Quality checks (pylint, pytest, mypy, ruff) — fix all issues
- [ ] Commit message prepared

### Step 4: `verify` key-warning rows + end-to-end `verify` tests — [step_4.md](./steps/step_4.md)

- [ ] Implementation: `_classify` key-warning and `TestNonTableConfigVerify` tests + two `_classify` branches (check precondition first)
- [ ] Quality checks (pylint, pytest, mypy, ruff) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch
- [ ] PR summary prepared
