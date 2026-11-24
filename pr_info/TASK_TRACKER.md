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

### Step 1: Move `toml_utils` into `mcp_coder.config` — [step_1.md](./steps/step_1.md)

- [x] Implementation: move `utils/toml_utils.py` to `config/toml_utils.py` with `move_module`, fix remaining references (no behaviour change; existing suite is the safety net)
- [x] Quality checks: pylint, mypy, pytest, lint-imports, tach, format — fix all issues
- [x] Commit message prepared

### Step 2: Lenient lookup, `format_code` from either file, `format_code` row for every repo — [step_2.md](./steps/step_2.md)

- [x] Implementation: tests first (`TestFindMcpCoderTableLenient`, `TestGetFormatCode`, `TestFormatCodeRow`, `TestProjectSection`), then `find_mcp_coder_table_lenient`, `FormatCodeSetting.source`, `get_format_code`, `_format_code_row` with `indent`, row in no-`pyproject.toml` branch
- [x] Quality checks: pylint, mypy, pytest, lint-imports, tach, vulture, format — fix all issues
- [x] Commit message prepared

### Step 3: `[tool.mcp-coder.prompts]` from either file — [step_3.md](./steps/step_3.md)

- [ ] Implementation: tests first (`TestGetPromptsConfigFiles`), then `get_prompts_config` via `find_mcp_coder_table_lenient`, non-table fallback, source-named mode warning, module docstring
- [ ] Quality checks: pylint, mypy, pytest, format — fix all issues
- [ ] Commit message prepared

### Step 4: `labels-config` from either file, CLI help — [step_4.md](./steps/step_4.md)

- [ ] Implementation: tests first (`mcp-coder.toml` / conflict / malformed / non-string), then rename to `_get_labels_config_from_project` based on `find_mcp_coder_table_lenient`, docstrings, `gh_parsers.py` help strings, `label-setup.md` and `cli-reference.md`
- [ ] Quality checks: pylint, mypy, pytest, lint-imports, tach, format — fix all issues
- [ ] Commit message prepared

### Step 5: `verify` warnings for unknown, retired, misplaced and conflicting keys — [step_5.md](./steps/step_5.md)

- [ ] Implementation: tests first (`test_verify_project_keys.py` unit + integration), then `verify_project_keys.py` (`_SCHEMA`, `KeyWarning`, `scan_project_keys`, `key_warning_rows`), PROJECT rows in `_print_project_section` (both branches), PROMPTS rows in `verify.py`; exit code unchanged
- [ ] Quality checks: pylint, mypy, pytest, lint-imports, tach, vulture, file size, format — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
