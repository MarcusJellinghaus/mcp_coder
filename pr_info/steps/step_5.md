# Step 5 — Jenkins process docs: run folder, delete only it

See [summary.md](./summary.md), design changes 3 and 5.

## WHERE

- `tools/jenkins_status_check.md`
- `tools/jenkins_issue_analysis.md`

Not deployed. Tool code (`tools/jenkins_download_logs.py`, `tools/jenkins_classify_logs.py`)
and its defaults stay unchanged.

## WHAT

No functions — prose only. Run folder: `.scratch/jenkins_logs_<issue or topic>_<date>/`.

1. **`tools/jenkins_status_check.md`**
   - Step 4, **One build**: example output
     `.scratch/jenkins_logs_<issue or topic>_<date>/Executor_2935.txt`; replace "and is deleted
     afterwards" with "; delete the run folder afterwards".
   - Step 4, **Many builds**: `--outdir` and `--logdir` both use the run folder.
   - Step 8: "Delete `.scratch/`." → "Delete the run folder (`delete_directory(<folder>, recursive=True)`)."
2. **`tools/jenkins_issue_analysis.md`**
   - Steps 1 and 2: `--outdir` / `--logdir` use the run folder.
   - Step 7: "Then delete `.scratch/`." → "Then delete the run folder."
   - Tips, first bullet: subagents write their findings files into the run folder.

## HOW

Edit with `mcp__mcp-workspace__edit_file`.

## ALGORITHM (the process the docs now describe)

```
run = ".scratch/jenkins_logs_<issue or topic>_<date>"
download_logs --outdir run ; classify_logs --logdir run
download_log <job> <n> run/<job>_<n>.txt
subagent findings -> run/
report ; delete_directory(run, recursive=True)   # never .scratch/ itself
```

## DATA

`index.csv` and logs live under the run folder.

## Precondition

If either file no longer mentions `.scratch/jenkins_logs`, write one line to
`pr_info/.blocked.txt` and stop.

## Verify

- `mcp__mcp-workspace__search_files(pattern="jenkins_logs(?!_<)", glob="tools/*.md")` → no matches.
- `mcp__mcp-workspace__search_files(pattern="(?i)delete `\\.scratch/?`|deleted afterwards", glob="tools/*.md")`
  → no matches.
- Re-check (issue Decision 6): `mcp__mcp-workspace__search_files(pattern="\\.scratch|delete_directory|pr_info/[^`]*\\*", glob=".claude/**")`
  → no remaining fixed-name file, glob delete or whole-`.scratch/` delete beyond the ones fixed
  in steps 1–4. If one is found, fix it by the same rules in this step.
- Tests: `tests/cli/commands/test_init_deployed_neutral.py`,
  `tests/cli/commands/test_init_deployed_paths.py`, `tests/icoder/test_repo_skills.py`,
  `tests/icoder/test_repo_agents.py`, then the fast unit tests, pylint and mypy as CLAUDE.md lists.
- Format, then one commit: `docs(tools): per-run Jenkins scratch folder`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5 only: in
> `tools/jenkins_status_check.md` and `tools/jenkins_issue_analysis.md`, use the run folder
> `.scratch/jenkins_logs_<issue or topic>_<date>/` for `--outdir`, `--logdir`, the single-build
> output file and the subagent findings files, and delete only that folder instead of
> `.scratch/`. Do not change any tool code. Then do the Decision 6 re-check search, run the
> checks in the step's Verify section, format, and make one commit.
