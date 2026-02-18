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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1 — Add regression test for bundled labels.json loading

- [x] Add `test_load_bundled_labels_config()` to `tests/workflows/test_label_config.py`
- [x] Run pylint, pytest, mypy — fix all issues found
- [x] Prepare git commit message for Step 1

### Step 2 — Fix `label_config.py`: return Traversable + accept it in load_labels_config

- [x] Add `from importlib.resources.abc import Traversable` import to `src/mcp_coder/utils/github_operations/label_config.py`
- [x] Change `get_labels_config_path` return type to `Path | Traversable` and return Traversable directly in bundled branch
- [x] Change `load_labels_config` signature to accept `Path | Traversable` and update body/docstring
- [x] Run pylint, pytest, mypy — fix all issues found
- [x] Prepare git commit message for Step 2

### Step 3 — Remove duplicate anti-pattern call sites in three other files

- [x] Replace `_load_labels_config()` body in `src/mcp_coder/workflows/vscodeclaude/config.py`
- [x] Replace `_load_labels_config()` body in `src/mcp_coder/workflows/vscodeclaude/issues.py`
- [x] Replace inline anti-pattern blocks in `_filter_eligible_issues()` and `get_eligible_issues()` in `src/mcp_coder/cli/commands/coordinator/core.py`
- [x] Run pylint, pytest, mypy — fix all issues found
- [x] Prepare git commit message for Step 3

## Pull Request

- [ ] Review all changes across steps for correctness and consistency
- [ ] Verify all tests pass (full test suite)
- [ ] Write PR summary: title, description, and list of files modified
