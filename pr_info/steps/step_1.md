# Step 1 — Skills, agent and rebase design doc use the git-write MCP tools

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Only edit the five files listed under WHERE. Replace Bash git commit/push instructions with
> the mcp-workspace git-write tools as specified — no other wording changes. If an anchor
> text quoted below is not found in its file, write one line to `pr_info/.blocked.txt` naming
> the file and anchor, and stop. Run the verification and checks, then make exactly one commit.

## WHERE

- `.claude/skills/commit_push/SKILL.md`
- `.claude/agents/commit-pusher.md`
- `.claude/skills/pr_comment_triage/SKILL.md`
- `.claude/skills/rebase/SKILL.md`
- `.claude/skills/rebase/rebase_design.md`

## WHAT

No functions — Markdown instructions and YAML frontmatter only.

### 1. `.claude/skills/commit_push/SKILL.md`

Frontmatter `allowed-tools`: remove `"Bash(git add *)"`, `"Bash(git commit *)"`,
`"Bash(git push *)"`; add `mcp__mcp-workspace__git_commit` and `mcp__mcp-workspace__git_push`
directly after `mcp__mcp-workspace__git`.

Keep `## 1. Format Code` and `## 2. Review Changes` unchanged. Replace everything from
`## 3. Stage Changes` to the end of the file with:

```markdown
## 3. Commit
Call `mcp__mcp-workspace__git_commit` with `message` and `paths` built from `git status`:
- Include modified, new and deleted files, and both the old and the new path of a rename
  (`git_commit` commits only the given paths).
- Exclude any files that shouldn't be committed.
- If no paths remain, skip the commit and go to step 4.

Use a clear, conventional commit message:
- Use format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep summary under 50 characters
- **No Claude Code footer or attribution in commit message**

If the result starts with `Nothing to commit`, go to step 4 (earlier commits may be unpushed).
If it starts with `Error:`, report it and stop — do not push.

## 4. Push
Call `mcp__mcp-workspace__git_push` (no arguments).

If it refuses (e.g. on the default branch), report it and stop. If step 3 made a commit, state
that the commit exists locally and is unpushed.
```

### 2. `.claude/agents/commit-pusher.md`

Frontmatter `tools:` becomes exactly (keep `permissionMode: bypassPermissions`):

```yaml
tools:
  - mcp__mcp-workspace__git
  - mcp__mcp-workspace__git_commit
  - mcp__mcp-workspace__git_push
  - mcp__mcp-tools-py__run_format_code
  - mcp__mcp-workspace__read_file
```

Replace the bullet list under "On top of that process:" with:

```markdown
- **Scope** — only the files named in your launch prompt may be modified. Confirm with
  `mcp__mcp-workspace__git` `"status"` before committing; if anything else changed, stop and
  report back without committing. Call `mcp__mcp-workspace__git_commit` with `paths` = the
  files named in your launch prompt.
- **Message** — use the one from your launch prompt.
- **Report** the commit SHA, the files committed, and the push result.
```

Delete the line `The working directory is already correct — do not use \`cd\` or \`git -C\`.`
(and the blank line after it). Everything else stays.

### 3. `.claude/skills/pr_comment_triage/SKILL.md`

Frontmatter only: replace `"Bash(git add *)"`, `"Bash(git commit *)"`, `"Bash(git push *)"`
with `mcp__mcp-workspace__git_commit` and `mcp__mcp-workspace__git_push` (same position).
Keep `"Bash(mcp-coder gh-tool set-status *)"`. Body unchanged.

### 4. `.claude/skills/rebase/SKILL.md`

Frontmatter `allowed-tools`:
- Remove `"Bash(git commit *)"`.
- Add `mcp__mcp-workspace__git_commit`, `mcp__mcp-workspace__git_push`,
  `mcp__mcp-workspace__git_push_force` directly after `mcp__mcp-workspace__git`.
- Keep `"Bash(git push --force-with-lease *)"` and all other entries.

Workflow step 7: `7. Report summary and ask for user confirmation` → `7. Report summary`.

Workflow step 9: replace `9. \`git push --force-with-lease\`` with:

```markdown
9. Push, choosing by the Branch Moved Check result:
   - `refs/remotes/origin/<branch>` absent (never pushed): `mcp__mcp-workspace__git_push`.
   - Otherwise: `mcp__mcp-workspace__git_push_force`. If it refuses with a message containing
     `needs git 2.30+` or `has no reflog`, run `git push --force-with-lease` instead.
   - Any other refusal or failure: report it and stop. This is not Abort Rule 1 — do not run
     `git rebase --abort`; the rebase has already completed.
```

Branch Moved Check, item 3, first bullet: replace
`Skip the rest of this check and rely on the lease.` with
`Skip the rest of this check; workflow step 9 uses \`git_push\`.`
Nothing else in the Branch Moved Check, conflict handling (`git add`, `git rebase --continue`),
Base Branch Confirmation or Abort Rules changes.

### 5. `.claude/skills/rebase/rebase_design.md`

In the permission code block:
- `# Staging and committing`: replace `Bash(git commit:*)` with `mcp__mcp-workspace__git_commit`.
- `# Pushing` becomes:
  ```
  mcp__mcp-workspace__git_push
  mcp__mcp-workspace__git_push_force
  Bash(git push --force-with-lease:*)  # fallback when git_push_force refuses (git < 2.30, no reflog)
  ```

Key Design Decision 5: replace heading and text with:

```markdown
### 5. Summary Before Push
Force-push is destructive. Show a summary without waiting for confirmation; the Branch Moved Check guards the force push.
```

No other changes to this file.

## HOW

- Interactive skills get the tools through their `allowed-tools` (a pre-approval for the
  invoking turn). `commit-pusher` gets them through `bypassPermissions` on its `tools:` list.
- `commit-pusher` reads `commit_push/SKILL.md` at runtime, so the new skill steps must work
  unattended. Agent-specific deltas (paths = launch-prompt files) stay in the agent file.
- `.claude/settings.local.json` is **not** touched.

## ALGORITHM

`/commit_push`:
```
format; status; diff
paths = changed files from status (deleted, renamed old+new) minus excluded
if paths: r = git_commit(message, paths); if r starts "Error:": report, stop
r = git_push()
if refused: report; if a commit was made: say it is local and unpushed
```

`/rebase` step 9:
```
if origin/<branch> absent (Branch Moved Check): git_push(); on failure: report, stop
else r = git_push_force()
  if r contains "needs git 2.30+" or "has no reflog": Bash git push --force-with-lease
  elif refused/failed: report, stop (no rebase --abort)
```

## DATA

Tool results the skills branch on (mcp-workspace `origin/main`):
- `git_commit`: `Committed <sha7> on <branch> (<n> files)` | `Nothing to commit for paths: …` |
  `Error: <reason>`.
- `git_push` / `git_push_force`: `Pushed …` / `Force-pushed …` | `Error: <reason>`.

## Verification

1. `mcp__mcp-workspace__search_files` with `glob=".claude/**"`:
   - pattern `Bash\(git (add|commit) \*\)|Bash\(git push \*\)` → matches only
     `.claude/skills/rebase/SKILL.md` (`Bash(git add *)`, kept for conflict resolution).
   - pattern `heredoc|git add -A|git -C` → no match in `.claude/agents/commit-pusher.md`.
   - pattern `^\s+- Bash$` in `.claude/agents/commit-pusher.md` → no match.
2. Read each edited file once to confirm the frontmatter is still valid YAML (list items,
   quoting unchanged for remaining `Bash(...)` entries).

## Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_mypy_check`

## Commit

`refactor(skills): commit and push via mcp-workspace git tools`
