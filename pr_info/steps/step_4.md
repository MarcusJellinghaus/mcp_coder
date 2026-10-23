# Step 4 — `.claude/skills/issue_update/SKILL.md`: ref-name rule

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`). Implement only Step 4: replace the Base Branch sentence in `.claude/skills/issue_update/SKILL.md` as described below. Change the skill text only, no code. Then run `mcp__mcp-tools-py__run_format_code`, pylint, mypy and the fast pytest suite (see CLAUDE.md), and make one commit: `docs(skills): state Base Branch ref-name rule in issue_update (#1275)`.

## Precondition

`.claude/skills/issue_update/SKILL.md` contains the sentence `The base branch must be a single line. Multiple lines will cause an error during branch creation.` If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`.claude/skills/issue_update/SKILL.md`, around line 49, under **Editing Base Branch:**.

## WHAT

Replace that sentence with:

```markdown
The base branch must be a single line and a valid git ref name (no spaces, `..`, `~^:?*[\`, `@{` or `//`; no leading `-`/`.`; no trailing `.`, `/` or `.lock`). `github_issue_edit` rejects an invalid value on write; if it is written another way, it is ignored and the base branch falls back — see `docs/repository-setup/github.md`.
```

## HOW

Text edit only. Leave `.claude/skills/issue_create/SKILL.md` unchanged.

## ALGORITHM

None.

## DATA

None.

## Tests

No tests, because this step changes skill text only. The quality checks must pass.
