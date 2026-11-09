# Step 2 — Update `docs/repository-setup/` for the MCP-only agents

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Step 1 is already committed. Edit only the three `docs/repository-setup/` files listed
> under WHERE. Do not touch `.claude/` or `pr_info/TASK_TRACKER.md`. Run the verification
> and the quality checks listed below, then produce exactly one commit.

## Precondition

`.claude/agents/issue-updater.md` has no `Bash` in `tools:` (step 1 done). If it still has
`Bash`, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

```
docs/repository-setup/agent-permissions.md
docs/repository-setup/README.md
docs/repository-setup/claude-code.md
```

## WHAT / HOW (per file)

### `agent-permissions.md` — rewrite three sentences in place
- **"What `permissionMode: bypassPermissions` does"** (around line 51): replace
  `` `Bash(gh issue edit *)` `` with the issue write tools
  (`mcp__mcp-workspace__github_issue_create`, `_edit`, `_comment`). The meaning stays the
  same: they are omitted from the allow list so they prompt in the main session, and the
  agents' `bypassPermissions` lets them run unprompted.
- **"`Bash` is all-or-nothing"** bullet (around line 62): replace "the git/gh-only limits
  stated in the agent bodies are prose" with the following. The shell limits in the agent
  bodies are prose: `commit-pusher` git only, `issue-approver`
  `mcp-coder gh-tool set-status` only. `issue-updater` has no `Bash` at all.
- **`PreToolUse` hook** bullet (around line 111): "the git/gh limit" → "the agents' shell
  limits".
- Search the file for any other claim that `issue-updater` uses `Bash` or `gh`, and fix it.

### `README.md` — agent rows in the file table (around lines 62–64)
- `issue-updater.md` row, last column: `—` → "Requires an mcp-workspace version with
  `github_issue_edit`".
- `issue-approver.md` row, last column, becomes:
  - "Requires `mcp-coder` on PATH and the status labels;
  - an mcp-workspace version with `github_issue_comment`, `get_reference_projects` and
    `reference_name` on the issue write tools (`github_issue_create`, `_edit`, `_comment`)
    and `github_label_list` (mcp-workspace#272) — `github_pr_create` has no
    `reference_name`;
  - cross-repo approval also needs `approve-command.yml` in the target repo, and the target
    configured as an mcp-workspace reference project with a `url` (explicit `url=` or
    detected from its checkout's git `origin`)."

### `claude-code.md`
- **`mcp-workspace` Server** intro (line 154): "plus optional read-only access to reference
  projects" → "plus reference projects: their files are read-only, but their GitHub issues
  can be created, edited and commented on through `reference_name`."
- `--reference-project` argument (line 160) becomes
  ``--reference-project name=<name>,path=<path>[,url=<url>]`` (repeatable). The text says:
  - it makes additional repositories readable from MCP, as `.mcp.json` does;
  - `url` is the explicit `url=` or, when omitted, auto-detected from the checkout's git
    `origin`;
  - a reference project with neither has a null `url`, so its issues can't be written and
    it never matches cross-repo approval;
  - the old `name=<path>` form is skipped with a warning.
- **Enhanced Claude Permissions** JSON example (line 199): replace `"mcp__mcp-workspace__*"`
  with a short explicit list, e.g. `"mcp__mcp-workspace__read_file"`,
  `"mcp__mcp-workspace__save_file"`, `"mcp__mcp-workspace__edit_file"`,
  `"mcp__mcp-workspace__github_issue_view"`. Keep the other entries. Below the block, add
  one sentence: the issue write tools (`github_issue_create`, `github_issue_edit`,
  `github_issue_comment`) are deliberately left out so issue writes prompt in the main
  session (see `agent-permissions.md`). Do not mirror the full `settings.local.json`.

## ALGORITHM (verification)

```
assert search_files(pattern="mcp__mcp-workspace__\\*", glob="docs/repository-setup/claude-code.md") == []
assert search_files(pattern="git/gh|gh issue edit", glob="docs/repository-setup/agent-permissions.md") == []
assert search_files(pattern="name=<path>", glob="docs/repository-setup/claude-code.md") only in the "old form" note
assert README issue-approver row mentions "reference project" and "url"
assert search_files(pattern="(?i)gh issue|gh pr|MSYS_NO_PATHCONV", glob=".claude/**") == []   # still clean
```

## DATA

None (documentation only).

## Checks and commit

- Run `run_format_code`, `run_pylint_check`, `run_mypy_check` and `run_pytest_check` (fast
  unit-test marker set, `-n auto`). All must pass. If a pre-existing failure blocks the
  commit, write one line to `pr_info/.blocked.txt` and stop.
- One commit, e.g. `docs(repository-setup): document MCP-only issue agents (#1145)`.
