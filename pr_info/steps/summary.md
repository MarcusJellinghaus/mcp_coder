# Summary — Migrate commit/push skills and commit-pusher agent to mcp-workspace git-write tools (#1415)

## Goal

Skills and the `commit-pusher` agent commit and push through Bash, which prompts
interactively and is impossible headless. mcp-workspace#220 (merged in #399) adds the
git-write MCP tools `git_branch`, `git_branch_delete`, `git_commit`, `git_push`,
`git_push_force`. mcp_coder installs mcp-workspace from GitHub `main`, so they are available
now — no version floor, no `pyproject.toml` change.

**Rule:** replace Bash git commands with the MCP tools — nothing more, nothing less. The only
agreed extra is dropping the pre-push confirmation in `/rebase` step 7.

## Architectural / design changes

This change touches only Markdown in `.claude/` and `docs/`. No Python code changes.

| Area | Before | After |
|---|---|---|
| `/commit_push` | `git add` → `git commit` → `git push` / `git push -u origin HEAD` via Bash | `git_commit(paths=…)` (stages and commits in one call) → `git_push()` |
| `commit-pusher` agent | `Bash` + `bypassPermissions` = any shell command auto-approved | No `Bash`; `bypassPermissions` auto-approves only its listed MCP tools (`git`, `git_commit`, `git_push`, `run_format_code`, `read_file`) |
| `/pr_comment_triage` | Pre-approves `Bash(git add/commit/push *)` | Pre-approves `git_commit`, `git_push` |
| `/rebase` push | Asks for confirmation, then `git push --force-with-lease` | No confirmation. The Branch Moved Check result decides: never pushed → `git_push`; otherwise `git_push_force`, falling back to Bash `--force-with-lease` only on the `needs git 2.30+` / `has no reflog` refusals |
| `/rebase` step 6 commits | `Bash(git commit *)` | `git_commit` |
| Global allow-list (`.claude/settings.local.json`) | No git writes | **Unchanged** — still no git writes. It is also the headless workflow permission file, so allow-listing would let workflow LLM steps commit or push |
| `CLAUDE.md` | Bash list includes `commit`, `push`, `checkout -b`, `branch`; heredoc rule | Git-write tools in the tool mapping; rule "`git_commit` always with `paths`, never `all=True`"; Bash list = `add`, `rebase`, `push --force-with-lease` |

Guardrails the design relies on (mcp-workspace, verified on `origin/main` `517714f`):

- `git_commit` stages untracked files under `paths` itself, and uses `git commit --only` (hence
  both sides of a rename go in `paths`). Empty `paths` → `Error: pass exactly one of paths or
  all=True`. No changes → `Nothing to commit for paths: …`.
- `git_push` / `git_push_force` refuse the default branch and a detached HEAD;
  `git_push_force` never uses plain `--force`.
- `git_push_force` refusal texts used by `/rebase`:
  `git_push_force needs git 2.30+ (--force-if-includes)` and
  `refs/remotes/origin/<branch> has no reflog (fresh clone?) …`.

## Files modified

No files are created (besides these plan files) and none are deleted.

| File | Step |
|---|---|
| `.claude/skills/commit_push/SKILL.md` | 1 |
| `.claude/agents/commit-pusher.md` | 1 |
| `.claude/skills/pr_comment_triage/SKILL.md` | 1 |
| `.claude/skills/rebase/SKILL.md` | 1 |
| `.claude/skills/rebase/rebase_design.md` | 1 |
| `.claude/CLAUDE.md` | 2 |
| `docs/repository-setup/agent-permissions.md` | 2 |
| `docs/repository-setup/README.md` | 2 |

Explicitly **not** modified: `.claude/settings.local.json`, `pyproject.toml`, any Python under
`src/` or `tests/`, `docs/repository-setup/github.md`, `docs/repository-setup/claude-code.md`.

## Testing approach

No Python behaviour changes, so no new unit tests (TDD not applicable). Each step verifies
with `mcp__mcp-workspace__search_files` that no stale Bash git text remains, then runs the
standard checks (pylint, pytest unit markers, mypy). `tests/workflows/rebase/test_prompt.py`
reads the packaged rebase `SKILL.md`, but only its "Conflict Resolution Strategies" table, which
this change leaves untouched.

## Steps

1. `step_1.md` — Skills, agent and rebase design doc (the instructions agents follow).
2. `step_2.md` — `CLAUDE.md` and repository-setup docs (descriptive text).

## Out of scope

The tools themselves; `gh-tool set-status` → `github_issue_set_status`; other wording
improvements; human-facing Bash in `docs/repository-setup/github.md`; pre-existing staleness in
`rebase_design.md`; Python-driven prompts (`rebase_permissions.py`, `prompts.md`); the
pre-existing error in `docs/repository-setup/claude-code.md`; propagation via Shared Config Sync.
