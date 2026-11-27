# Step 1 — `issue_analyse_supervisor`: per-issue analysis log

See [summary.md](./summary.md), design change 1.

## WHERE

- `.claude/skills/issue_analyse_supervisor/SKILL.md` (deployed file)

## WHAT

No functions — prose only. Two edits:

1. **Setup step 5 (`**Log:**`)** — replace the glob delete and fixed name with:
   > 5. **Log:** `pr_info/issue_analysis_log_<issue>.md`, with the issue number from step 1.
   > If `list_directory` on `pr_info/` shows that file, delete it; then create it with a header.
   > Never delete another issue's log — parallel sessions in this folder may own it. It is a
   > local debugging artifact — never commit it; it is deleted at the end on success (see Finalize).
2. **Finalize, the "On success" bullet** — delete only `pr_info/issue_analysis_log_<issue>.md`
   (keep the "keep it only if the run failed or was interrupted" clause).

Do not change the frontmatter (`allowed-tools`); a missing write/delete tool is out of scope.

## HOW

Edit with `mcp__mcp-workspace__edit_file`. Keep the surrounding wording and numbering.
Deployed prose: no `.py`, no Python tool names, no backticked `tools/…` or `docs/…` paths.

## ALGORITHM (the instruction the skill now gives)

```
log = "pr_info/issue_analysis_log_<issue>.md"
if log in list_directory("pr_info"): delete(log)
create(log, header)
... rounds append to log ...
on success: delete(log)        # this file only, never a glob
```

## DATA

The log file name now carries the issue number. Log format section unchanged.

## Precondition

If Setup step 5 no longer mentions `pr_info/issue_analysis_log*.md`, write one line to
`pr_info/.blocked.txt` and stop.

## Verify

- `mcp__mcp-workspace__search_files(pattern="issue_analysis_log", glob=".claude/**")` → only
  `issue_analysis_log_<issue>.md`; no `issue_analysis_log*` or `issue_analysis_log.md`.
- Tests: `tests/cli/commands/test_init_deployed_neutral.py`,
  `tests/cli/commands/test_init_deployed_paths.py`, `tests/icoder/test_repo_skills.py`,
  `tests/icoder/test_repo_agents.py`, then the fast unit tests, pylint and mypy as CLAUDE.md lists.
- Format, then one commit: `docs(skills): per-issue analysis log in issue_analyse_supervisor`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement step 1 only: edit
> `.claude/skills/issue_analyse_supervisor/SKILL.md` so the analysis log is
> `pr_info/issue_analysis_log_<issue>.md`, Setup checks with `list_directory` that it exists
> before deleting it, there is no glob delete, and Finalize deletes only that file. Leave the
> frontmatter unchanged. Run the searches and checks in the step's Verify section, format, and
> make one commit.
