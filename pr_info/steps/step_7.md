# Step 7: Document the epic-branch procedure and fix the CLI reference

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md`. Steps 1-6 are in place. Docs only; keep the text short and match the surrounding style. One commit.

## WHERE

- `docs/cli-reference.md`
- `docs/repository-setup/github.md`

## WHAT / HOW

### `docs/cli-reference.md`, section `### rebase` (around lines 427-429)

- `--base-branch` option: "Base branch to rebase onto (default: auto-detect). Needed only when the detected base is not `main`/`master` and was not named in the issue's `### Base Branch` section."
- Description: the base is auto-detected; a base named in the issue's `### Base Branch` is trusted; bases found from an open PR, git merge-base or the default branch are accepted automatically only for `main`/`master`. The command fails (exit 2) if the base does not exist on origin.

### `docs/cli-reference.md`, section `### gh-tool get-base-branch` (around lines 936-938)

Priority list in code order:
1. Linked issue's base branch (`### Base Branch`)
2. GitHub PR base branch
3. Git merge-base
4. Default branch

### `docs/repository-setup/github.md`

- Update `### Validation` (line ~178): create-plan, create-pr, `mcp-coder rebase` and the implement workflow's rebase step check that the base exists on origin and report a clear error (the implement step only warns and skips the rebase).
- New subsection `### Epic Branches`, placed after `### Validation`:
  1. Create and push the epic branch from main (`git checkout -b epic/<name> origin/main`, `git push -u origin epic/<name>`).
  2. Add `### Base Branch` with `epic/<name>` to each sub-issue. create-plan, implement, `mcp-coder rebase`, review and create-pr then use it without flags.
  3. Sub-PRs target and merge into the epic branch.
  4. Finish: open the epic-to-main PR manually (`mcp-coder create-pr` does not apply; the epic branch has no issue number). GitHub does not auto-close issues on merges to a non-default branch, so the PR body lists every sub-issue with `Closes #N` (`Closes owner/repo#N` for other repos).
  5. Multi-repo epics: a base branch is resolved in the sub-issue's own repo, so create one epic branch per repo, ideally with the same name.
  6. Rebasing the epic branch onto main rewrites its history. Rebase each open sub-branch onto the new tip: `git rebase --onto <new-epic-tip> <old-epic-tip>` (manual).

## DATA

None.

## Checks

No code changes and no tests cover these two docs. Review the Markdown with `git diff`.
