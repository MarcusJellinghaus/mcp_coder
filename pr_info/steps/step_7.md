# Step 7: `/rebase` skill

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md`. Steps 1 to 6 are already committed. Edit the skill, run the checks listed in the summary, and produce exactly one commit. Implement only this step.

## WHERE

`.claude/skills/rebase/SKILL.md` only.

## WHAT

A new section, "Branch Moved Check", plus two new items in the numbered workflow. `allowed-tools` does not change: do not add `git reset`. `workflows/rebase_permissions.py` reads that list.

## HOW

All git calls go through the already-allowed `mcp__mcp-workspace__git`. `--quiet` is not on the MCP allowlist, so an absent ref shows up as an error.

Compare with `refs/remotes/origin/<branch>`, not the bare name, because a tag named `origin/<branch>` makes the check pass wrongly.

## ALGORITHM

Replace the `## Workflow` list with:

```text
1. git fetch origin (as today)
2. Branch Moved Check, before the rebase:
   - branch = command "branch", args ["--show-current"]
   - PRE_SHA = command "rev_parse", args ["HEAD"]
   - command "rev_parse", args ["--verify", "refs/remotes/origin/<branch>"]
     - error: the ref is absent; skip this check and rely on the lease
   - command "merge_base", args ["--is-ancestor", "refs/remotes/origin/<branch>", PRE_SHA]
     - "false": stop and report. Nothing to undo.
3. git rebase origin/${BASE_BRANCH}
4. For each conflict: as today
5. Run code checks: as today
6. Fix any issues from merge
7. Report summary and ask for user confirmation
8. Repeat the Branch Moved Check against the same PRE_SHA
   - "false": stop, and print `git reset --hard <PRE_SHA>` for the human to run.
9. git push --force-with-lease
```

## DATA

The new section must state:

- **Why:** a fetch refreshes the tracking ref, which disables the lease for commits someone else pushed.
- **Abort instruction:** the `git rebase --abort` line under Abort Rules does not apply to either stop. At the first, no rebase has started. At the second, the rebase has already completed.
- **Do not work around it:** on a stop, do not fetch and push again.

## Tests

No new tests. `tests/workflows/rebase/test_prompt.py` and `test_rebase_permissions.py` read or depend on this file and must keep passing. Leave the `allowed-tools` block and the `## Abort Rules` section's numbering unchanged.
