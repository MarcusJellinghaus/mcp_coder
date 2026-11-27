# Step 2 — Review supervisors: create the log in the step that picks `{n}`

See [summary.md](./summary.md), design change 2.

## WHERE

- `.claude/skills/plan_review_supervisor/SKILL.md` (deployed file)
- `.claude/skills/implementation_review_supervisor/SKILL.md` (deployed file)

## WHAT

No functions — prose only. In each file, merge Setup steps 3 and 4 into one step 3:

- `plan_review_supervisor`:
  > 3. **Log:** pick `{n}` = one more than the highest number among existing
  > `pr_info/plan_review_log_*.md` (1 if none), and in this same step create
  > `pr_info/plan_review_log_{n}.md` with a header. If that file already exists, take the next number.
- `implementation_review_supervisor`: the same with `pr_info/implementation_review_log_*.md`
  and `pr_info/implementation_review_log_{n}.md`.

Setup then has three steps. All later references to `pr_info/<kind>_log_{n}.md` stay as they
are. No frontmatter change.

## HOW

Edit with `mcp__mcp-workspace__edit_file`. Deployed prose rules apply (no `.py`, no Python tool
names, no backticked `tools/…` / `docs/…` paths).

## ALGORITHM (the instruction the skill now gives)

```
existing = list_directory("pr_info") matching <kind>_log_*.md
n = max(numbers(existing), default=0) + 1
while exists("pr_info/<kind>_log_{n}.md"): n += 1
create("pr_info/<kind>_log_{n}.md", header)   # same step as picking n
```

## DATA

Log names unchanged: `pr_info/plan_review_log_{n}.md`, `pr_info/implementation_review_log_{n}.md`.

## Precondition

If either file's Setup no longer has the separate "determine the next run number" and
"Create … with a header" steps, write one line to `pr_info/.blocked.txt` and stop.

## Verify

- `mcp__mcp-workspace__search_files(pattern="review_log_", glob=".claude/skills/**")` → each
  supervisor's Setup picks `{n}` and creates the file in one step, with the "already exists →
  next number" rule.
- Tests: `tests/cli/commands/test_init_deployed_neutral.py`,
  `tests/cli/commands/test_init_deployed_paths.py`, `tests/icoder/test_repo_skills.py`,
  `tests/icoder/test_repo_agents.py`, then the fast unit tests, pylint and mypy as CLAUDE.md lists.
- Format, then one commit: `docs(skills): create review log in the step that picks its number`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement step 2 only: in
> `.claude/skills/plan_review_supervisor/SKILL.md` and
> `.claude/skills/implementation_review_supervisor/SKILL.md`, merge Setup steps 3 and 4 so the
> supervisor picks `{n}` and creates the log in the same step, taking the next number if that
> log file already exists. No timestamps, no frontmatter change. Run the checks in the step's
> Verify section, format, and make one commit.
