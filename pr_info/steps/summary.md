# Summary — #1492: unique log and scratch file names, so parallel sessions in one folder don't collide

## Goal

Two Claude sessions in one folder must not overwrite or delete each other's files. Today
`/issue_analyse_supervisor` deletes `pr_info/issue_analysis_log*.md` and writes a fixed name,
and several skills, agents and docs tell a session to delete all of `.scratch/` or write to the
shared `.scratch/jenkins_logs`.

## Design changes

This is a **prose-only change** to instruction files (skills, agents, CLAUDE.md, Jenkins process
docs). No Python source, no tool defaults, no frontmatter / `allowed-tools` / agent `tools:` change.

The design is a set of ownership rules:

1. **Per-issue analysis log:** `pr_info/issue_analysis_log_<issue>.md`. A run deletes only its
   own issue's log (after checking with `list_directory` that it exists), never a glob.
2. **Review logs keep `{n}`**, but the supervisor creates the file in the same step that picks
   `{n}`; if that file already exists it takes the next number. No timestamps. This narrows the
   race (MCP `save_file` has no create-only mode); it does not close it — accepted.
3. **`.scratch/` ownership:** a session deletes only the files it wrote (`delete_this_file`), or a
   `.scratch/` subfolder it created (`delete_directory(<subfolder>, recursive=True)`). Nobody
   deletes `.scratch/` itself. The rule is stated **once** in `.claude/CLAUDE.md` (the
   "No session scratchpad" line); the Scratch probes and Jenkins lines only say what to delete.
   Deployed agents get one short sentence (they never create subfolders, so the subfolder
   exception is not repeated there).
4. **Manual cleanup:** the same CLAUDE.md line tells the user to delete `.scratch/` and leftover
   `pr_info/issue_analysis_log_*.md` by hand when no session runs in the folder.
5. **Unique names:** probe `.scratch/test_probe_<issue or topic>.py` (named in CLAUDE.md only —
   deployed prose may not contain `.py`); issue body `.scratch/issue_body_<issue>.md`; Jenkins run
   folder `.scratch/jenkins_logs_<issue or topic>_<date>/` used for `--outdir`, `--logdir`, the
   single-build output file and subagent findings files. `<date>` stays a placeholder.

### Constraints the edits must respect

- Deployed files (`.claude/skills`, `.claude/agents`, `.claude/knowledge_base`) are checked by
  `tests/cli/commands/test_init_deployed_neutral.py` (no `.py`, no Python tool names in the body)
  and `tests/cli/commands/test_init_deployed_paths.py` (no backticked `tools/…` / `docs/…` paths
  unless the line says "in the mcp-coder repository"). Do not add such text to deployed files.
- `tests/icoder/test_repo_agents.py` checks that a preloaded skill's `allowed-tools` are in the
  agent's `tools`; nothing in frontmatter changes.
- `.claude/CLAUDE.md` and `tools/*.md` are not deployed; Python and `tools/` paths are fine there.

### Tests

No new tests. The change is wording in Markdown; a regex test over prose would be brittle and
the issue's acceptance names only the existing tests. Each step verifies with a content search
(`mcp__mcp-workspace__search_files`) and runs the existing deployed-prose and skill tests plus
the standard checks.

## Files modified

| File | Step | Change |
|---|---|---|
| `.claude/skills/issue_analyse_supervisor/SKILL.md` | 1 | per-issue log name; existence check; no glob delete |
| `.claude/skills/plan_review_supervisor/SKILL.md` | 2 | pick `{n}` and create the log in one step |
| `.claude/skills/implementation_review_supervisor/SKILL.md` | 2 | same |
| `.claude/agents/code-engineer.md` | 3 | delete only own `.scratch/` files |
| `.claude/agents/issue-analyst.md` | 3 | same |
| `.claude/agents/plan-engineer.md` | 3 | same |
| `.claude/skills/issue_update/SKILL.md` | 3 | body file `.scratch/issue_body_<issue>.md`; delete only own files |
| `.claude/CLAUDE.md` | 4 | ownership rule + manual cleanup line; probe name; Jenkins run folder |
| `tools/jenkins_status_check.md` | 5 | Jenkins run folder; delete only it |
| `tools/jenkins_issue_analysis.md` | 5 | Jenkins run folder; subagent findings there; delete only it |

No files or folders are created besides these plan files. Unchanged by decision:
`tools/jenkins_download_logs.py` / `tools/jenkins_classify_logs.py` defaults,
`src/mcp_coder/workflows/review/review_log.py`, `src/mcp_coder/cli/commands/verify.py`,
`/commit_push`, `docs/repository-setup/agent-permissions.md`, the `issue-updater` agent
(already compliant), and all `allowed-tools` / `tools:` lists.

## Steps

1. `issue_analyse_supervisor`: per-issue analysis log.
2. Review supervisors: create the log in the step that picks `{n}`.
3. Deployed agents and `issue_update`: delete only own `.scratch/` files; unique body file name.
4. `.claude/CLAUDE.md`: ownership rule, manual cleanup, probe name, Jenkins run folder.
5. Jenkins process docs: run folder, delete only it.
