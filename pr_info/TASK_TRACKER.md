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

- [x] **Step 1: HelpHintArgumentParser class + unit tests** - [step_1.md](steps/step_1.md)
  - [x] Add `HelpHintArgumentParser` class to `parsers.py`
  - [x] Add unit tests in `tests/cli/test_parsers.py`
  - [x] All checks pass (pylint, mypy, pytest)

- [x] **Step 2: Wire into CLI + update manual error paths** - [step_2.md](steps/step_2.md)
  - [x] Use `HelpHintArgumentParser` in `create_parser()`
  - [x] Add help hints to manual error messages in `_handle_*` functions
  - [x] Downgrade `logger.error` → `logger.debug` in manual error paths
  - [x] Update/add tests in `tests/cli/test_main.py`
  - [x] All checks pass (pylint, mypy, pytest)

- [x] **Step 3: Remove dead "unknown subcommand" branches** - [step_3.md](steps/step_3.md)
  - [x] Verify each branch is truly unreachable before removing
  - [x] Remove dead else branches and related tests
  - [x] Add `return 1` fallbacks for mypy
  - [x] All checks pass (pylint, mypy, pytest)

## Pull Request
