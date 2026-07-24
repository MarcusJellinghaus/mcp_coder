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

### Step 1: `utils/repo_config.py` — `get_repo_flag` primitive
Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code): create `src/mcp_coder/utils/repo_config.py` with `get_repo_flag` and `tests/utils/test_repo_config.py` (TDD)
- [x] Quality checks: pylint, pytest (`-n auto` unit exclusion), mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 2: create-plan config-gated success transition
Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code): gate `to_label_id` on `auto_review_plan` in `workflows/create_plan/core.py` + tests
- [x] Quality checks: pylint, pytest (`-n auto` unit exclusion), mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 3: implement config-gated success transition
Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code): gate `to_label_id` on `auto_review_implementation` in `workflows/implement/core.py` + update tests
- [x] Quality checks: pylint, pytest (`-n auto` unit exclusion), mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 4: Refactor coordinator dispatch to data-driven `WORKFLOW_TEMPLATES` (pure refactor)
Detail: [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code): add `WORKFLOW_TEMPLATES`, replace selector block in `core.py`, export from `__init__.py` + coverage
- [x] Quality checks: pylint, pytest (`-n auto` unit exclusion), mypy, lint-imports, vulture — fix all issues
- [x] Commit message prepared

### Step 5: Add review workflows — templates + routing tables + guard test
Detail: [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code): 4 review templates, `WORKFLOW_MAPPING` entries, `PRIORITY_ORDER`, exports + template/watchdog/guard tests
- [x] Quality checks: pylint, pytest (`-n auto` unit exclusion), mypy, lint-imports, vulture — fix all issues
- [x] Commit message prepared

### Step 6: create-pr auto-path assignee-add (best-effort)
Detail: [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code): `_add_pr_assignee_best_effort` helper + call site in `workflows/create_pr/core.py` + tests
- [x] Quality checks: pylint, pytest (`-n auto` unit exclusion), mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 7: Docs — config.md flags + `executor_test_path` → `executor_job_path` rename
Detail: [step_7.md](./steps/step_7.md)

- [ ] Implementation: add two flag rows to `config.md`, rename `executor_test_path` → `executor_job_path` (15 places), fix `core.py:377` docstring; verify sweep finds no old field name
- [ ] Quality checks: pylint, pytest (`-n auto` unit exclusion), mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Review complete implementation against [summary.md](./steps/summary.md) — verify both concerns (A) wiring and (B) doc-correctness are covered
- [ ] Prepare PR summary/description (flag concerns A and B separately per summary)
