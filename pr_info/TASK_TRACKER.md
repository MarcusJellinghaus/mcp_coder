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

### Step 1: Slot filler in `mcp_coder.utils.prompt_slots` — [step_1.md](./steps/step_1.md)

- [x] Implementation: tests + `prompt_slots.py` (`resolve_prompt_slots`, `fill_prompt`), `get_prompt_with_substitutions` uses `fill_prompt`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Workflow prompts — neutral wording + slots, filled by their callers — [step_2.md](./steps/step_2.md)

- [x] Implementation: tests + `prompts.md` rewording/slots, callers (`_run_ci_fix`, `run_finalisation`, `process_single_task`, create_plan) fill slots, `claude-code.md` doc
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: System and project prompts, filled on the inject path — [step_3.md](./steps/step_3.md)

- [x] Implementation: tests + `system-prompt.md` / `project-prompt.md` slots, `_fill_injected_prompts` in `prompt_llm` / `prompt_llm_stream`, `python.md` doc
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Implement fix loop uses the toolkit's `fix.check` — [step_4.md](./steps/step_4.md)

- [x] Implementation: tests + `check_and_fix_mypy` uses `fix.check` fragment, Mypy Fix Prompt removed, `05-implementation.md` doc
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Rebase — `[test_filter]` rename and allowlist from `llm_permissions` — [step_5.md](./steps/step_5.md)

- [x] Implementation: tests + `[test_filter]` rename, `rebase_settings` / `rebase_settings_file` from `llm_permissions`, all-prompts scan test
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
