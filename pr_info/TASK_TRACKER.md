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

### Step 1: Single dispatch call-site invariant + boundary documentation

Detail: [step_1.md](./steps/step_1.md) — AC3 (primary), AC6 (boundary doc), AC7

- [ ] Implementation: create `tests/icoder/test_self_invocation_guard.py` (`_call_sites` helper + `test_exactly_one_dispatch_call_site`); replace module docstring with boundary note and add marker comment above the `registry.dispatch(text)` call in `app_core.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: `InputSubmitted` post-site invariant

Detail: [step_2.md](./steps/step_2.md) — AC4

- [ ] Implementation: append `test_input_submitted_constructed_only_in_input_area` to `test_self_invocation_guard.py`; add marker comment at the `InputSubmitted` post site in `input_area.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Behavioural dispatch boundary — human in, model out

Detail: [step_3.md](./steps/step_3.md) — AC1, AC2, AC3 (supporting)

- [ ] Implementation: add `test_user_typed_skill_dispatches_and_invokes` to `test_app_core.py`; add `test_model_stream_slash_text_never_dispatches` to `test_app_pilot.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `user-invocable: false` absent from registry + flag doc-note

Detail: [step_4.md](./steps/step_4.md) — AC5, AC6 (flag doc-note)

- [ ] Implementation: add `test_user_invocable_false_skill_absent_from_registry` to `test_skills.py`; add field doc-note above `disable_model_invocation` in `skills.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: address review feedback
- [ ] PR summary prepared
