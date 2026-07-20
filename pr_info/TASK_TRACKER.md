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

### Step 1: Data model + package + import-linter contract

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation: write `tests/icoder/test_permissions_model.py` (TDD), then create `permissions/__init__.py`, `permissions/model.py`, and add the `permissions_leaf_isolation` contract to `.importlinter`
- [x] Quality checks: pylint, pytest (fast-unit), mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 2: Matcher engine (parse + rank + match)

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation: write `tests/icoder/test_permissions_matcher.py` (TDD), then create `permissions/matcher.py` and export `parse_matcher` from `__init__.py`
- [x] Quality checks: pylint, pytest (fast-unit), mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 3: Resolver — config precedence + default + config-path degrade

Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation: write `tests/icoder/test_permissions_resolver.py` (TDD, `frame=None`), then create `permissions/resolver.py` (`resolve` + `_resolve_config`), export `resolve`, and whitelist unread params in `vulture_whitelist.py`
- [x] Quality checks: pylint, pytest (fast-unit), mypy, lint-imports, vulture — fix all issues
- [x] Commit message prepared

### Step 4: Resolver — frame semantics + degrade interaction + lifted_never

Detail: [step_4.md](./steps/step_4.md)

- [x] Implementation: extend `tests/icoder/test_permissions_resolver.py` (TDD, frame models A/B/C), then add `_resolve_frame` and wire the frame-first branch into `resolve()`
- [x] Quality checks: pylint, pytest (fast-unit), mypy, lint-imports — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] Review PR against issue #1041 acceptance criteria and summary.md
- [ ] Write PR summary description
