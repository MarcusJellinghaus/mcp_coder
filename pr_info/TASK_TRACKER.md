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

### Step 1: `SessionSpec` type + spec read/write helpers

See [step_1.md](./steps/step_1.md).

- [x] Implementation: `SessionSpec` dataclass + `SESSION_SPEC_FILENAME` + `write_session_spec`/`read_session_spec` in `types.py`, with round-trip tests in `test_session_spec.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `session_setup.py` pure helpers (env, argv, banner)

See [step_2.md](./steps/step_2.md).

- [ ] Implementation: create `session_setup.py` pure helpers (env dict, venv-bin, exe/python resolvers, argv builders, `render_banner`), add `INTERVENTION_WARNING` to `templates.py`, with tests in `test_session_setup_env.py` + `test_templates.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: `session_setup.py` orchestration + `main`

See [step_3.md](./steps/step_3.md).

- [ ] Implementation: add `orchestrate`, `run_first_step`, `run_session`, `_force_utf8_stdout`, `main`, `__main__` guard, with flow tests in `test_session_setup_flow.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Thin launcher templates + gitignore entry (additive)

See [step_4.md](./steps/step_4.md).

- [ ] Implementation: add `LAUNCHER_WINDOWS`/`LAUNCHER_POSIX` and extend `GITIGNORE_ENTRY` in `templates.py`, with launcher tests in `test_templates.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Rewrite `create_startup_script` to write spec + launcher

See [step_5.md](./steps/step_5.md).

- [ ] Implementation: rewrite `create_startup_script` (build spec + write launcher), delete `_escape_batch_title`, port/trim tests across `test_workspace_startup_script.py`, `test_workspace_startup_script_github.py`, `test_startup_script_mcp_coder_path.py`, `test_workspace.py`, add `skip_github_install` round-trip test
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Retire orchestration templates + docs

See [step_6.md](./steps/step_6.md).

- [ ] Implementation: delete the 14 retired orchestration constants from `templates.py`, remove their tests, update `docs/coordinator-vscodeclaude.md` Generated-Files table and the `ci.yml` drift-guard comment
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Review full diff across all steps for consistency and completeness
- [ ] Write PR summary describing the launcher + `session_setup` refactor (issue #695)
