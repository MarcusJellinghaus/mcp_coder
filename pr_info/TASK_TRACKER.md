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

### Step 1: Resolver cross-layer precedence — personal-layer bit (refs #1154)
[step_1.md](./steps/step_1.md) — skip if #1154 has already landed on `main`.
- [x] Implementation: seven new resolver tests, `_PERSONAL_LAYERS` + 6-key `_rule_sort_key`, six prose sites, two docstring notes
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `fix(permissions): let a personal layer win at equal specificity (#1046)` — body `Refs #1154`, no closing keyword

### Step 2: `ApprovalModal` widget
[step_2.md](./steps/step_2.md)
- [x] Implementation: six pilot tests, new `ui/widgets/approval_modal.py` (`DISCLAIMER_TEMPLATE`, `build_prompt_text`, `format_args_full`, `ApprovalModal`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `feat(icoder): add the reactive approval modal (#1046)`

### Step 3: Modal push + `once`/`session` wiring; remove interim auto-deny
[step_3.md](./steps/step_3.md)
- [x] Implementation: delete two obsolete test artefacts, nine new tests, `LOCAL_SETTINGS_RELPATH` in `loader.py`, modal push + `_apply_approval` in `stream_view.py`, move `action_cancel_stream` down from `app.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `feat(icoder): push the approval modal and apply once/session scopes (#1046)`

### Step 4: `permissions/persist.py` — comment-preserving JSONC write-back
[step_4.md](./steps/step_4.md) — gated on step 1.
- [x] Implementation: nineteen unmarked tests in `test_permissions_persist.py`, new `persist.py` (`write_rule`, `PersistError`, `_scan` locator), register in `.importlinter` `permissions_leaf_isolation`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `feat(permissions): add comment-preserving JSONC rule write-back (#1046)`

### Step 5: Wire the `persist` choice + end-to-end composition test
[step_5.md](./steps/step_5.md) — gated on steps 1 and 4.
- [x] Implementation: six pilot tests, disk write in `_apply_approval` (parse guard first, `except OSError` degrade), re-check every #1046 acceptance criterion
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared: `feat(icoder): persist approval grants to settings.local.json (#1046)`

## Pull Request

- [ ] PR review: diff against base branch, all quality checks green, `.scratch/` absent
- [ ] PR summary: describe the change set and note that #1154 stays open
