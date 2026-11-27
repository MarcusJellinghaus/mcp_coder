# Step 4 — `.claude/CLAUDE.md`: ownership rule, manual cleanup, probe name, Jenkins run folder

See [summary.md](./summary.md), design changes 3, 4 and 5.

## WHERE

- `.claude/CLAUDE.md` (not deployed — Python and `tools/` paths are allowed here)

## WHAT

No functions — prose only. Four edits:

1. **"No session scratchpad" line** — append the one ownership rule and the manual-cleanup line:
   > Other sessions may share this folder: name your files by issue or topic, and delete only
   > the files you wrote (`delete_this_file`) or a `.scratch/` subfolder you created
   > (`delete_directory(<subfolder>, recursive=True)`) — never `.scratch/` itself. The user
   > deletes `.scratch/` and leftover `pr_info/issue_analysis_log_*.md` by hand, when no session
   > runs in this folder.
2. **"Scratch probes" section**
   - Both code lines use `.scratch/test_probe_<issue or topic>.py`.
   - Replace "Delete when done — `delete_directory(".scratch", recursive=True)`" with
     "Delete your probe file when done (`delete_this_file`)". Keep "CI still blocks any PR
     carrying one" and the rest of the paragraph.
3. **Jenkins section** — run folder `.scratch/jenkins_logs_<issue or topic>_<date>/`:
   - Download console logs: `--outdir .scratch/jenkins_logs_<issue or topic>_<date>` (not in
     brackets); "delete `.scratch/` when done" → "delete that run folder when done".
   - Download one build: example output
     `.scratch/jenkins_logs_<issue or topic>_<date>/Executor_2935.txt` (the tool creates parent
     folders); "delete it afterwards" → "delete the run folder afterwards".
   - Analyse failures: `tools/jenkins_classify_logs.sh --logdir .scratch/jenkins_logs_<issue or topic>_<date>`
     (explicit, not in brackets; the same folder as the download's `--outdir`).
4. No other section changes.

## HOW

Edit with `mcp__mcp-workspace__edit_file`. CLAUDE.md is not a protected file.

## ALGORITHM

None — wording only.

## DATA

Names: `.scratch/test_probe_<issue or topic>.py`, `.scratch/jenkins_logs_<issue or topic>_<date>/`.

## Precondition

If `.claude/CLAUDE.md` has no "No session scratchpad" line or no "Scratch probes" section,
write one line to `pr_info/.blocked.txt` and stop.

## Verify

- `mcp__mcp-workspace__search_files(pattern="jenkins_logs(?!_<)", glob=".claude/CLAUDE.md")` → no matches.
- `mcp__mcp-workspace__search_files(pattern="(?i)delete_directory\\(\"\\.scratch\"|delete `\\.scratch/?`", glob=".claude/CLAUDE.md")`
  → no matches (the user cleanup line says "deletes `.scratch/`", addressed to the user).
- `test_probe_<issue or topic>.py` appears in both Scratch probes code lines.
- Tests: `tests/cli/commands/test_init_deployed_neutral.py`,
  `tests/cli/commands/test_init_deployed_paths.py`, `tests/icoder/test_repo_skills.py`,
  `tests/icoder/test_repo_agents.py`, then the fast unit tests, pylint and mypy as CLAUDE.md lists.
- Format, then one commit: `docs(claude): scratch ownership rule and per-run Jenkins folder`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement step 4 only: in
> `.claude/CLAUDE.md`, extend the "No session scratchpad" line with the ownership rule and the
> manual-cleanup line, rename the probe to `.scratch/test_probe_<issue or topic>.py` and make it
> delete only the probe file, and change the Jenkins lines to the run folder
> `.scratch/jenkins_logs_<issue or topic>_<date>/` with explicit `--outdir` / `--logdir`,
> deleting only that folder. Run the checks in the step's Verify section, format, and make one
> commit.
