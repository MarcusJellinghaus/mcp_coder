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

### Step 1: Add `default`, `promotable`, `failure` fields to label config
- [x] Implementation: add fields to `labels.json`, update `labels_schema.md`, update `test_labels.json`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Config validation (`validate_labels_config`)
- [x] Implementation: add `validate_labels_config()` to `label_config.py` with tests (TDD)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: New config discovery
- [ ] Implementation: modify `get_labels_config_path()` — drop `workflows/config/`, add `pyproject.toml` lookup and `config_override` param, with tests (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: CLI flags in `gh_parsers.py`
- [ ] Implementation: add `--init`, `--validate`, `--config`, `--generate-github-actions`, `--all` arguments and help text, with parser tests (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Gate operations in `define_labels.py` + updated summary
- [ ] Implementation: gate init/validate behind flags, expand `--all`, use `default: true` label, pass `--config` to discovery, call `validate_labels_config()`, update summary output, with tests (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: GitHub Action generation (`--generate-github-actions`)
- [ ] Implementation: add `generate_label_new_issues_yml()`, `generate_approve_command_yml()`, `build_promotions()`, `write_github_actions()` to `define_labels.py`, with tests (TDD)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Documentation updates
- [ ] Implementation: update `label-setup.md`, `github.md`, `README.md`, `cli-reference.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps complete, no regressions
- [ ] PR summary prepared
