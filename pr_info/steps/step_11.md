# Step 11: docs: formatting users, pre-flight list, failure behaviour

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_11.md`.
> Docs only, no tests. Run the fast pytest set (`-n auto`) to confirm nothing
> else changed, then make exactly one commit.

## WHERE

- `docs/configuration/toolkits.md`
- `docs/architecture/toolkit-interface.md`
- `docs/repository-setup/python.md`

## WHAT

- `toolkits.md`:
  - Bindings table, `commit` row (~line 80): users become "formatting before
    commits: create-plan, implement (tasks, task tracker preparation,
    finalisation), rebase, review, CI fix".
  - Config-error list (~line 62): "Workflows that run the format pre-flight at
    entry stop: create-plan, implement, rebase, fix_ci and review; …".
  - `format.apply` exit-code note (~line 191): "fails formatting: implement's
    task and final-check commits fail; create-plan, task tracker preparation,
    finalisation, rebase, review and CI fix log a warning and carry on."
- `toolkit-interface.md`, Formatting table (~line 83), row "Any other
  status": "`False`: implement's task and final-check commits fail;
  create-plan, task tracker preparation, finalisation, rebase, review and CI
  fix carry on".
  Add one sentence below the table: `format_best_effort` wraps
  `run_formatters` for the carry-on callers. It logs a warning on `False` or
  an exception and never raises.
- `python.md`, `[tool.mcp-coder] format_code` row (~line 21): opt-out list
  "`create-plan`, `implement`, `rebase`, `review`, `fix-ci` and
  `check_branch_status --fix`".

## HOW

Plain text edits; keep each file's existing style and line wrapping.

## ALGORITHM

None.

## DATA

None.

## Commit

`docs: list create-plan, task tracker preparation and finalisation as formatter users`
