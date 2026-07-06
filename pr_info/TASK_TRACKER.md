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

### Step 1: DRY shared CLI flags ([step_1.md](./steps/step_1.md))

- [x] Implementation: create `cli/shared_args.py` with five per-flag helpers + canonical wording; write `tests/cli/test_shared_args.py` first (TDD); wire `parsers.py` / `gh_parsers.py` per the table (init / issue-stats / define-labels / verify overrides, `metavar="METHOD"` everywhere). `main.py` untouched.
- [x] Quality checks: pylint, pytest (`-n auto` + fast markers), mypy — fix all issues
- [x] Commit message prepared

### Step 2: Single-source command descriptions ([step_2.md](./steps/step_2.md))

- [x] Implementation: create dependency-free `cli/command_catalog.py` (`COMMAND_DESCRIPTIONS` + `COMMAND_CATEGORIES`); render `help.py` from them, delete `Command`/`Category` NamedTuples + `Category.description`; point leaf `help=` at the catalog; add `gh-tool checkout-issue-branch`; move `create-plan` detail to epilog. Rewrite `tests/cli/commands/test_help.py` first (TDD). `main.py` untouched.
- [x] Quality checks: pylint, pytest (`-n auto` + fast markers), mypy, tach/lint-imports — fix all issues
- [x] Commit message prepared

### Step 3: Anti-drift test lock ([step_3.md](./steps/step_3.md))

- [x] Implementation: create `tests/cli/test_help_anti_drift.py` with `collect_leaves()` walking `create_parser()` tree and the five parity assertions (leaves ⊆ descriptions with matching `help=`, keys == leaf set, every leaf rendered, group/suppressed excluded, every description categorized).
- [x] Quality checks: pylint, pytest (`-n auto` + fast markers), mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [x] Review full diff across all steps for consistency and adherence to summary.md
- [ ] Write PR summary (goal, changes per step, verification)
