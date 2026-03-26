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

### Step 1: Update Help Categories
> [Detail](./steps/step_1.md) — Update `COMMAND_CATEGORIES` in `help.py` to reflect new command structure.
- [x] Implementation: update `help.py` categories and `test_help.py` expectations
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Flatten Coordinator Command
> [Detail](./steps/step_2.md) — Convert `coordinator` from subcommand group to direct command with `--dry-run` flag.
- [x] Implementation: rewrite `add_coordinator_parsers()` in `parsers.py`, update `_handle_coordinator_command()` in `main.py`, update coordinator tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Add vscodeclaude Top-Level Command
> [Detail](./steps/step_3.md) — Add `vscodeclaude` as top-level command with `launch` and `status` subcommands.
- [x] Implementation: add `add_vscodeclaude_parsers()` in `parsers.py`, add `_handle_vscodeclaude_command()` in `main.py`, update vscodeclaude CLI tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Move define-labels and issue-stats to gh-tool
> [Detail](./steps/step_4.md) — Add `define-labels` and `issue-stats` as subcommands under `gh-tool`, remove top-level `define-labels`.
- [ ] Implementation: update `add_gh_tool_parsers()` in `parsers.py`, update `_handle_gh_tool_command()` in `main.py`, remove `add_define_labels_parser()`, update gh-tool and issue-stats tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Migrate Config Keys
> [Detail](./steps/step_5.md) — Migrate config keys from `coordinator.vscodeclaude` to top-level `vscodeclaude` section.
- [ ] Implementation: update config key strings in `vscodeclaude/config.py`, update default config template in `user_config.py`, update `commands.py` error message, update config tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Update Documentation and Slash Commands
> [Detail](./steps/step_6.md) — Update all docs and `.claude/commands/` files to reference new command names.
- [ ] Implementation: update `cli-reference.md`, `coordinator-vscodeclaude.md`, `label-setup.md`, `config.md`, and slash command files
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] Review all changes across steps for consistency
- [ ] Write PR summary
