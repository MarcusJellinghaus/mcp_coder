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

### Step 1: Add Failure Labels to labels.json + Update Tests ([step_1.md](./steps/step_1.md))

- [x] Add 5 failure status labels to `src/mcp_coder/config/labels.json`
- [x] Update `tests/cli/commands/test_set_status.py` — add labels to `VALID_STATUS_LABELS` and count `10` → `15`
- [x] Update `tests/cli/commands/test_define_labels.py` — count `10` → `15`
- [x] Update `tests/cli/commands/test_define_labels_label_changes.py` — `created` count `9` → `14` and `call_count` `9` → `14`
- [x] Run quality checks (pylint, pytest, mypy) and fix any issues
- [x] Prepare git commit message for Step 1

### Step 2: Update Development Process Documentation ([step_2.md](./steps/step_2.md))

- [x] Add "8. Failure Handling" section to `docs/processes-prompts/development-process.md`
- [x] Include failure label table with trigger conditions and recovery actions
- [x] Run quality checks (pylint, pytest, mypy) and fix any issues
- [x] Prepare git commit message for Step 2

### Step 3: Fix HTML Matrix Label Names ([step_3.md](./steps/step_3.md))

- [x] Update 5 failure label names in `docs/processes-prompts/github_Issue_Workflow_Matrix.html` to match `labels.json` convention
- [x] Update step-number badges (`6f`, `6f-ci`, `6f-t`) for implementation-cycle failure labels
- [x] Run quality checks (pylint, pytest, mypy) and fix any issues
- [x] Prepare git commit message for Step 3

## Pull Request

- [ ] Review all changes across steps for consistency
- [ ] Verify all failure label names match between `labels.json`, docs, and HTML matrix
- [ ] Prepare PR summary covering all 3 steps
