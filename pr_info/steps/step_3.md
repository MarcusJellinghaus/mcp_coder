# Step 3 — Deployed agents and `issue_update`: delete only own `.scratch/` files

See [summary.md](./summary.md), design changes 3 and 5.

## WHERE

- `.claude/agents/code-engineer.md` — the `**Temp files**` bullet
- `.claude/agents/issue-analyst.md` — the `**Writes**` bullet
- `.claude/agents/plan-engineer.md` — the `**Writes**` bullet
- `.claude/skills/issue_update/SKILL.md` — steps 4 and 5

All deployed files.

## WHAT

No functions — prose only.

1. **Agents** — replace "delete it / delete `.scratch/` before you report" with one sentence:
   > delete the `.scratch/` files you wrote with `delete_this_file` before you report; never
   > delete `.scratch/` itself — other sessions may use it.
   - `code-engineer`: `- **Temp files** — only in `.scratch/`; delete the files you wrote …`
   - `issue-analyst`: keep "only `.scratch/` probes (see CLAUDE.md "Scratch probes")" and
     "Never edit the issue or any other file."
   - `plan-engineer`: keep "only `pr_info/`, `.scratch/` probes, and requirement files named in
     the launch prompt" and "Never commit, push or edit GitHub."
   - Keep the existing line wrapping style (~95 chars). Do not mention the subfolder exception.
2. **`issue_update`**:
   - Step 4 (`**Write:**`): when using `body_file`, write the body to
     `.scratch/issue_body_<issue>.md`.
   - Step 5 (`**Temp files:**`): delete only the files this run wrote to `.scratch/`, with
     `delete_this_file`; never `.scratch/` itself.

No change to any `tools:` or `allowed-tools` list (all four already have `delete_this_file`).
`issue-updater.md` already complies — leave it.

## HOW

Edit with `mcp__mcp-workspace__edit_file`. Deployed prose rules: no `.py`, no Python tool names,
no backticked `tools/…` / `docs/…` paths.

## ALGORITHM

None — wording only.

## DATA

New fixed-per-issue name: `.scratch/issue_body_<issue>.md`.

## Precondition

If any of the four bullets/steps named above no longer exists, write one line to
`pr_info/.blocked.txt` and stop.

## Verify

- `mcp__mcp-workspace__search_files(pattern="(?i)delete (it|`\\.scratch/?`) before", glob=".claude/**")`
  → no matches.
- `mcp__mcp-workspace__search_files(pattern="\\.scratch", glob=".claude/agents/*.md")` and the
  same for `.claude/skills/**` → every cleanup instruction deletes only own files.
- Tests: `tests/cli/commands/test_init_deployed_neutral.py`,
  `tests/cli/commands/test_init_deployed_paths.py`, `tests/icoder/test_repo_skills.py`,
  `tests/icoder/test_repo_agents.py`, then the fast unit tests, pylint and mypy as CLAUDE.md lists.
- Format, then one commit: `docs(agents): delete only own .scratch files`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3 only: in
> `.claude/agents/code-engineer.md`, `.claude/agents/issue-analyst.md` and
> `.claude/agents/plan-engineer.md`, change the cleanup instruction so the agent deletes only
> the `.scratch/` files it wrote (`delete_this_file`) and never `.scratch/` itself. In
> `.claude/skills/issue_update/SKILL.md`, name the body file `.scratch/issue_body_<issue>.md`
> and delete only the files the run wrote. No frontmatter changes. Run the checks in the step's
> Verify section, format, and make one commit.
