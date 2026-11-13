# Step 2 — CLAUDE.md and repository-setup docs describe the git-write tools

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. Step 1
> is already committed. Only edit the three files listed under WHERE, and only the sentences
> named below — no restructuring, no other wording changes. If an anchor text quoted below is
> not found in its file, write one line to `pr_info/.blocked.txt` naming the file and anchor,
> and stop. Run the verification and checks, then make exactly one commit.

## WHERE

- `.claude/CLAUDE.md`
- `docs/repository-setup/agent-permissions.md`
- `docs/repository-setup/README.md`

## WHAT

No functions — Markdown text only.

### 1. `.claude/CLAUDE.md`

**a. Tool mapping** — insert one row directly after this row:

```markdown
| Git read-only (status, diff, log, show, fetch, ls_tree, ls_files, ls_remote, rev_parse, branch list) | `mcp__mcp-workspace__git` |
```

New row:

```markdown
| Git write (switch/create branch, delete branch, commit, push, force-push after rebase) | `mcp__mcp-workspace__git_branch`, `git_branch_delete`, `git_commit`, `git_push`, `git_push_force` |
```

**b. `paths` rule** — insert one paragraph between the end of the table and the
`Sibling repos are readable in full …` paragraph (blank line on each side):

```markdown
**`git_commit`:** always pass `paths`, never `all=True` — `all` is `git add -A`, and `.scratch/` is not gitignored (CI blocks PRs carrying it).
```

**c. Git operations** — replace:
- `Skills that instruct bash commands (e.g. \`git commit\`) must also use Bash.` →
  `Skills that instruct bash commands (e.g. \`git rebase\`) must also use Bash.`
- Code-block line `git commit / add / rebase / push / checkout -b / branch` →
  `git add / rebase / push --force-with-lease`
  (keep the `mcp-coder gh-tool set-status <label>` line).
- The whole `**Privileged agents:** …` paragraph →
  ```markdown
  **Privileged agents:** `commit-pusher`, `issue-updater` and `issue-approver` run with `bypassPermissions`, so they skip the prompts their tools normally trigger — `git_commit` and `git_push` for `commit-pusher`, the MCP issue write tools for `issue-updater`, and `github_issue_comment` plus its `Bash` commands (including `mcp-coder gh-tool set-status`) for `issue-approver`. That is an ergonomics device, not access control — any session can launch them, and `Bash` is unrestricted inside `issue-approver`; `commit-pusher` and `issue-updater` have no `Bash`. Rationale and limits: `docs/repository-setup/agent-permissions.md` in the mcp-coder repository.
  ```
- `**Before every commit:** run \`mcp__mcp-tools-py__run_format_code\`, then stage and commit.` →
  `**Before every commit:** run \`mcp__mcp-tools-py__run_format_code\`, then \`mcp__mcp-workspace__git_commit\`.`
- Delete the `**Multi-line commit messages:** …` paragraph (and one adjacent blank line).

Leave **Bash discipline** (`cd`, `git -C`) unchanged — it still applies to the remaining Bash
git commands.

### 2. `docs/repository-setup/agent-permissions.md`

Sentence-level edits only:

**a. "What `permissionMode: bypassPermissions` does"** — replace the paragraph with:

```markdown
`.claude/settings.local.json` deliberately omits `Bash(git add|commit|push)`, the git-write
MCP tools (`mcp__mcp-workspace__git_commit`, `_push`, `_push_force`, `_branch`,
`_branch_delete`) and the issue write tools (`mcp__mcp-workspace__github_issue_create`,
`_edit`, `_comment`), so those prompt in the main session. The agents carry
`bypassPermissions` so they run unprompted there, without widening the global allow list.
`commit-pusher` has no `Bash`, so there it auto-approves only its listed MCP tools.
```

**b. "What it does not do", bullet `**\`Bash\` is all-or-nothing.**`** — replace with:

```markdown
- **`Bash` is all-or-nothing.** Agent `tools:` takes bare tool names, so the shell limit
  stated in the agent body is prose: `issue-approver` `mcp-coder gh-tool set-status` only.
  `commit-pusher` and `issue-updater` have no `Bash` at all. Under `bypassPermissions`,
  *every* shell command is auto-approved.
```

**c. "The alternative this does not rule out"** — two replacements in the same paragraph
(keep line wrapping readable; rest of the paragraph unchanged):
- `the scope is a command pattern rather than all of \`Bash\`` →
  `the scope is the specific MCP git write tools (\`git_commit\`, \`git_push\`)`
- `Putting \`Bash(git add *) Bash(git commit *) Bash(git push *)\` on the three` →
  `Putting \`mcp__mcp-workspace__git_commit\` and \`mcp__mcp-workspace__git_push\` on the three`

**d. Net trade** — replace
`Net trade: the agents survive escalations, but \`commit-pusher\` and \`issue-approver\` carry an
unrestricted \`Bash\` (\`issue-updater\` has none);` with
`Net trade: the agents survive escalations, but \`issue-approver\` carries an unrestricted
\`Bash\` (\`commit-pusher\` and \`issue-updater\` have none);` (rest unchanged).

**e. "What actually constrains these agents"** — in the hook bullet replace
`would be the only real enforcement of the agents' shell limits` with
`would be the only real enforcement of \`issue-approver\`'s shell limit`. The scope-check
bullet stays as is.

### 3. `docs/repository-setup/README.md`

In the "Files Shared With Other Projects" table, "What to adjust" column:
- `.claude/CLAUDE.md`: `Project conventions, tool list, allowed commands` →
  `Project conventions, tool list, allowed commands; requires an mcp-workspace version with the git-write tools (mcp-workspace#220)`
- `.claude/skills/`: `Repo-specific paths/commands inside individual SKILL.md files` →
  `Repo-specific paths/commands inside individual SKILL.md files; requires an mcp-workspace version with the git-write tools (mcp-workspace#220)`
- `.claude/agents/commit-pusher.md`: `—` →
  `Requires an mcp-workspace version with the git-write tools (mcp-workspace#220)`

Do not change the `.claude/settings.local.json` row.

## HOW

- `CLAUDE.md` is the single home of the `paths`-not-`all=True` rule; skills rely on it.
- `.claude/settings.local.json` stays unchanged: no git-write tool is allow-listed.

## ALGORITHM

None — text replacement only.

## DATA

None.

## Verification

1. `mcp__mcp-workspace__search_files` on `.claude/CLAUDE.md`:
   - `git_branch_delete` and `never \`all=True\`` → one match each.
   - `heredoc|checkout -b|stage and commit|e\.g\. \`git commit\`` → no match.
2. `mcp__mcp-workspace__search_files` on `docs/repository-setup/agent-permissions.md`:
   - `Bash\(git add \*\) Bash\(git commit` → no match.
   - `commit-pusher\` and \`issue-approver\` carry` → no match.
3. `mcp__mcp-workspace__search_files` on `docs/repository-setup/README.md`:
   `git-write tools \(mcp-workspace#220\)` → exactly three matches.

## Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_mypy_check`

## Commit

`docs: describe mcp-workspace git-write tools in CLAUDE.md and setup docs`
