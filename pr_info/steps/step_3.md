# Step 3 — Document resolution order and exit codes 0–3

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> TDD: first extend the epilog test in `tests/cli/commands/test_gh_tool_checkout.py`, then
> update the epilog in `src/mcp_coder/cli/gh_parsers.py`, `docs/cli-reference.md` and
> `.claude/skills/implement_direct/SKILL.md`. Do not touch `command_catalog.py`. Run pylint,
> pytest (fast unit set, `-n auto`) and mypy; all must pass (including
> `tests/cli/test_help_anti_drift.py`). Run `run_format_code`, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/gh_parsers.py`: `checkout-issue-branch` parser epilog
- `docs/cli-reference.md`: `### gh-tool checkout-issue-branch` (Description and Exit codes lines)
- `.claude/skills/implement_direct/SKILL.md`: step 2
- `tests/cli/commands/test_gh_tool_checkout.py`: `test_checkout_issue_branch_help_shows_exit_codes`

## WHAT

Test: add `assert "3" in epilog, "Epilog should document exit code 3"`.

Epilog text:

```
Resolution order:
  1. Linked branch, open PR referencing the issue, closed PR whose
     branch still exists, branch-name pattern (N-... / .../N_...)
  2. Otherwise: linked branches, open closing-PR heads and matching
     remote branches; exactly one is checked out
  3. Otherwise: a new linked branch is created

Exit codes:
  0  Branch checked out (found, single candidate, or created)
  1  Issue not found, or branch creation failed
  2  Error (invalid project dir, no repo identifier, lookup or
     ls-remote failed, API error, git checkout failed)
  3  Ambiguous: two or more candidate branches found (listed in log)
```

`cli-reference.md`:
- Description: same resolution order in one or two sentences. Note that an existing PR's
  head branch is checked out rather than a new branch created.
- Exit codes line: lists 0–3 with the meanings above.

`SKILL.md` step 2: append after the code block:

```
   If it exits with code 3 (ambiguous), stop: show the candidate branches from its log
   output and ask the user which branch to use. Do not continue until they answer.
```

## HOW / ALGORITHM / DATA

Text-only changes. No new functions, no data structures.
