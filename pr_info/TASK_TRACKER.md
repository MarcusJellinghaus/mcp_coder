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

- [ ] **Step 1: HelpHintArgumentParser class + unit tests** - [step_1.md](steps/step_1.md)
  - [ ] Add `HelpHintArgumentParser` class to `parsers.py`
  - [ ] Add unit tests in `tests/cli/test_parsers.py`
  - [ ] All checks pass (pylint, mypy, pytest)

- [ ] **Step 2: Wire into CLI + update manual error paths** - [step_2.md](steps/step_2.md)
  - [ ] Use `HelpHintArgumentParser` in `create_parser()`
  - [ ] Add help hints to manual error messages in `_handle_*` functions
  - [ ] Downgrade `logger.error` → `logger.debug` in manual error paths
  - [ ] Update/add tests in `tests/cli/test_main.py`
  - [ ] All checks pass (pylint, mypy, pytest)

- [ ] **Step 3: Remove dead "unknown subcommand" branches** - [step_3.md](steps/step_3.md)
  - [ ] Verify each branch is truly unreachable before removing
  - [ ] Remove dead else branches and related tests
  - [ ] Add `return 1` fallbacks for mypy
  - [ ] All checks pass (pylint, mypy, pytest)

## Pull Request
