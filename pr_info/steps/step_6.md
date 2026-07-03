# Step 6 — Retire orchestration templates + docs

Read `pr_info/steps/summary.md` first. Final cleanup: after Step 5 the old
orchestration template constants are dead product code (only the old tests still
reference them). Remove both, and refresh the docs.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/templates.py` (delete constants)
- `tests/workflows/vscodeclaude/test_templates.py` (delete their tests)
- `docs/coordinator-vscodeclaude.md` (Generated-Files table)
- `.github/workflows/ci.yml` (drift-guard comment only, ~lines 132–166)

## WHAT
Delete these now-unused constants from `templates.py`:
- `VENV_SECTION_WINDOWS`, `VENV_SECTION_POSIX`
- `AUTOMATED_SECTION_WINDOWS`, `AUTOMATED_SECTION_POSIX`
- `AUTOMATED_RESUME_SECTION_WINDOWS`, `AUTOMATED_RESUME_SECTION_POSIX`
- `INTERACTIVE_ONLY_SECTION_WINDOWS`, `INTERACTIVE_ONLY_SECTION_POSIX`
- `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS`, `INTERACTIVE_RESUME_WITH_COMMAND_POSIX`
- `STARTUP_SCRIPT_WINDOWS`, `STARTUP_SCRIPT_POSIX`
- `INTERVENTION_SCRIPT_WINDOWS`, `INTERVENTION_SCRIPT_POSIX`

Keep: `LAUNCHER_WINDOWS`, `LAUNCHER_POSIX`, `WORKSPACE_FILE_TEMPLATE`,
`TASKS_JSON_TEMPLATE`, `STATUS_FILE_TEMPLATE`, `BANNER_TEMPLATE`,
`INTERVENTION_LINE`, `GITIGNORE_ENTRY`. Optionally trim the module docstring's
two-environment narrative to match the new model.

## HOW
- Grep for each deleted name to confirm no remaining import in `src/`
  (`workspace.py` no longer imports them after Step 5). Delete the corresponding
  tests in `test_templates.py` (they only assert on removed constants); keep the
  Step-4 launcher tests.
- Docs: add `.vscodeclaude_session.json` to the "Generated Files" table and
  update the startup-script row to describe the thin launcher + Python
  `session_setup`.
- `.github/workflows/ci.yml`: the `vscodeclaude-template-install` job
  (~lines 132–166) documents itself (in a comment) as exercising
  `templates.py:VENV_SECTION_POSIX` and a `_build_github_install_section_posix`
  helper that this step deletes. Update that comment to point at the new source
  of truth (`session_setup.build_install_argv`). **Comment-only** — the job body
  runs `tools/install.py` directly and does not break.

## ALGORITHM
None (deletion + doc edit).

## DATA
None.

## TESTS
- No new behaviour. Existing suite must stay green; `test_templates.py` retains
  only launcher/`GITIGNORE_ENTRY` assertions.
- Confirm nothing imports the removed constants (a stale import would fail
  collection).

## LLM PROMPT
> Implement Step 6 from `pr_info/steps/step_6.md` (context in
> `pr_info/steps/summary.md`). Delete the retired orchestration constants from
> `src/mcp_coder/workflows/vscodeclaude/templates.py` and remove the tests in
> `tests/workflows/vscodeclaude/test_templates.py` that reference them (keep the
> launcher tests). Update `docs/coordinator-vscodeclaude.md` Generated-Files
> table to mention `.vscodeclaude_session.json` and the thin launcher, and update
> the `vscodeclaude-template-install` drift-guard comment in
> `.github/workflows/ci.yml` (~lines 132–166) to point at
> `session_setup.build_install_argv` (comment-only). Verify no `src/` code still
> imports the removed names. Use MCP workspace tools. Run pylint, pytest
> (`-n auto` + standard exclusions), mypy; fix all. One commit.
