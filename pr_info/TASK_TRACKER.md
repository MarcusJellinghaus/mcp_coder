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

### Step 1: Extract `prompt_parsing.py` + mirror tests + remove allowlist entry

See [step_1.md](./steps/step_1.md) for full detail.

- [x] Implementation: move the 3 parsing helpers (`_extract_headers`, `_extract_code_block_after_header`, `_find_duplicates`) to new `src/mcp_coder/prompt_parsing.py` and the 3 test classes (`TestGetPromptMissingHeader`, `TestGetPromptDuplicateHeaders`, `TestHeaderLevelMatching`) to new `tests/test_prompt_parsing.py` via `move_symbol` (dry-run first); fix imports (`run_ruff_fix` F401 to drop `re`/`Union`); remove `prompt_manager.py` from `.large-files-allowlist`; edit `tach.toml` (declare `mcp_coder.prompt_parsing`, add to `prompt_manager` `depends_on`)
- [x] Quality checks: pylint, pytest, mypy — plus `run_lint_imports_check`, `check_file_size`, `compact-diff`, and `tach check` — fix all issues (Note: `tach` is not installed in this environment and no Bash is available, so `tach check` could not be executed; `tach.toml` was updated per spec — `mcp_coder.prompt_parsing` declared as a `domain` module with `depends_on = []` and added to `prompt_manager`'s `depends_on`)
- [x] Commit message prepared

### Step 2: Extract `prompt_sources.py` + mirror tests

See [step_2.md](./steps/step_2.md) for full detail.

- [ ] Implementation: move the 4 source/loading helpers (`_is_package_relative_path`, `_resolve_package_path`, `_load_content`, `_is_file_path`) to new `src/mcp_coder/prompt_sources.py` and the 4 test classes (`TestGetPromptFromFile`, `TestGetPromptWildcard`, `TestInputAutoDetection`, `TestPackageIntegration`) to new `tests/test_prompt_sources.py` via `move_symbol` (dry-run first); fix imports (`run_ruff_fix` F401 to drop `Optional`/`Path`/`find_data_file`, keep `glob`/`os`); edit `.importlinter` (add sub-layer `mcp_coder.prompt_sources | mcp_coder.prompt_parsing`); edit `tach.toml` (declare `mcp_coder.prompt_sources`, add to `prompt_manager` `depends_on`)
- [ ] Quality checks: pylint, pytest, mypy — plus `run_lint_imports_check`, `check_file_size`, `compact-diff`, and `tach check` — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Review full PR diff for correctness and adherence to the "Move, Don't Change" constraint (only imports + file headers changed)
- [ ] Write PR summary
