# Claude Code permissions — tool inventory

Part 2 of 5 · [How it works](how-it-works.md) · [Design concept](design-concept.md) · [Implementation](implementation.md) · [Skills and agents](skills-agents.md)

| Column | Values |
|---|---|
| `A` — allow-list | L = `settings.local.json`, U = user settings, S = skill `allowed-tools` only, `–` = prompts |
| `C` — CLAUDE.md tool table | ✓ named, ✗ not named, ⛔ CLAUDE.md forbids it |

`C` matters: Claude sees every tool's own description, but CLAUDE.md decides which one it prefers. Servers can also ship their own instructions (`mcp-workspace`, `claude-artifacts` do).

**Versions** (tool env `C:\Jenkins\environments\mcp-coder-dev\.venv`, 2026-11-14):

| Server | Installed | Upstream main | Tools missing locally |
|---|---|---|---|
| mcp-workspace | `f13d197` (2026-10-28) | `1a55e99` (2026-11-14), 21 commits ahead | 6 — marked 🆕 |
| mcp-tools-py | not compared | — | none (upstream README tool list = installed list) |

## 1. mcp-workspace

🆕 = upstream only, available after upgrade (T18).

| Topic | Read | A | C | Write | A | C |
|---|---|---|---|---|---|---|
| Workspace files | read_file, list_directory, search_files, check_file_size | L | ✓ | save_file, edit_file, append_file, move_file, delete_this_file, delete_directory | L | ✓ (delete_directory: prose only) |
| Reference projects | get_reference_projects, list_reference_directory, read_reference_file, search_reference_files | L | ✓ | — | | |
| Git | git (read-only allowlist; `fetch` touches network/refs), get_base_branch, check_branch_status | L | ✓ | 🆕 git_branch, git_branch_delete, git_commit, git_push, git_push_force | S | ✓ |
| GitHub issues | github_issue_view, github_issue_list, github_search, github_label_list | L | ✓ | github_issue_create, github_issue_edit, github_issue_comment | S | ✓ |
| | | | | 🆕 github_issue_set_status | – | ✗ (CLAUDE.md: use `gh-tool set-status`) |
| GitHub sub-issues | github_subissue_list | – | ✗ | github_subissue_add, github_subissue_remove | – | ✗ |
| GitHub PRs | github_pr_view | L | ✓ | github_pr_create | – | ✓ |
| | | | | github_review_comment_reply, github_review_thread_resolve | S | ✗ |

GitHub writes accept `reference_name` → can write to sibling repos.

**Built-in guards of the 🆕 tools** (upstream README):

| Tool | Does | Refuses |
|---|---|---|
| git_branch | switch, or create from HEAD / local / `origin/` base | — never fetches |
| git_branch_delete | force-delete a local branch | unless its tip is on GitHub; current, default and remote branches |
| git_commit | commit given `paths` or all | amend, hook bypass |
| git_push | push current branch to `origin` with `-u` | default branch |
| git_push_force | `--force-with-lease --force-if-includes` after rebase | default branch |
| github_issue_set_status | set one `status-*` label, removing the others; workspace or reference repos | — |

**File access rules** 🆕 (`.mcp-file-access`, upstream `f626cf8` / PR #401, unreleased; ref: upstream `docs/file-access.md`):

| Aspect | Fact |
|---|---|
| File | `.mcp-file-access` at project root only; one `<level> <gitignore pattern>` per line; levels `read-only`, `read-write`; last match wins; `!` invalid |
| Effect | rule overrides `.gitignore` both ways: committed + `read-only` → no writes; gitignored + rule → readable / writable |
| Built-ins | the rules file itself is always read-only for MCP (create / edit it by hand); `.git` always hidden |
| Invalid file | fail-safe: all writes refused, nothing gitignored exposed |
| Reload | every tool call (no restart) |
| Obeyed by | all file tools, reference file tools, GitHub `body_file` |
| **Not** obeyed by | `git` tools (`git show HEAD:<path>`), `check_file_size`, native Read/Write/Bash — not a sandbox |

## 2. mcp-tools-py

| Topic | Read / analyse | A | C | Write / execute | A | C |
|---|---|---|---|---|---|---|
| Static checks | run_pylint_check, run_mypy_check, run_ruff_check, run_bandit_check, run_vulture_check, run_lint_imports_check, run_tach_check | L | ✓ | — | | |
| Dependency check | run_deptry_check | – | ✗ | — | | |
| Tests | — | | | run_pytest_check (**executes project code**) | L | ✓ |
| Formatting | — | | | run_format_code, run_ruff_fix | L | ✓ |
| Refactoring | list_symbols, find_references | L | ✓ | move_symbol, move_module, rename_symbol | L | ✓ |
| Library source | get_library_source | L | ✓ | — | | |
| | search_library_files | L | ✗ | | | |
| Misc | sleep | L | ✗ | — | | |

## 3. obsidian-wiki (user-scope server)

| Topic | Read | A | C | Write | A | C |
|---|---|---|---|---|---|---|
| Vault notes | list_vaults, read_note, search_vault | L | server only | create_note, edit_note, move_note, **delete_note**, create_directory | L | server only |
| Tags | — | | | add_tags, remove_tags, manage_tags, rename_tag | L | server only |

"server only" = CLAUDE.md names the server and when to read/write, not the tools. "Write only to `Field Notes/`" is prose — not enforced.

## 4. claude-artifacts (claude.ai connector)

| Topic | Read | A | C | Write | A | C |
|---|---|---|---|---|---|---|
| Artifacts | guide, get/read/list_artifacts, list_files, read_file, list/describe_types | – | ✗ | publish_version, publish_files, edit_version, delete_artifact, pin/unpin | – | ✗ |
| Assets / data / comments | list/read_asset, db_get/list/query, read_comments | – | ✗ | upload_asset, db_write, reply_comment, resolve_comment | – | ✗ |

Write = publishes off-machine.

## 5. Claude Code built-ins

| Topic | Read | A | C | Write / execute | A | C |
|---|---|---|---|---|---|---|
| Files | Read, Glob, Grep | mode | ⛔ (justify) | Write, Edit, NotebookEdit | `acceptEdits` (U) | ⛔ (justify) |
| Shell | — | | | Bash, PowerShell | patterns (L, U) | ⛔ except approved git / `set-status` |
| Web | WebSearch | – | ✗ | WebFetch | `domain:*` (L, U) | ✗ |
| Orchestration | ToolSearch | | ✗ | Agent, Skill, Workflow, SendMessage | Skill: L | ✗ |
| | AskUserQuestion | | ⛔ | | | |
| Other | — | | | Cron*, ScheduleWakeup, RemoteTrigger, EnterWorktree, PushNotification | – | ✗ |

## 6. Bash patterns → MCP replacement

✓ = replace now, ✅ = done, ⏳ = MCP tool now installed, callers still to switch (T21), ✗ = no MCP equivalent.

**Allow-lists**

| Pattern | File | Reach | MCP replacement | |
|---|---|---|---|---|
| `git diff/status/ls-tree:*` | U | read | `mcp-workspace__git` | ✓ |
| `git mv:*` | U | write | `move_file` (git-aware) | ✓ |
| `gh issue view:*` | U | read | `github_issue_view` (+ `reference_name`) | ✓ |
| `gh run view:*` | U | read | `check_branch_status` (current branch CI + log) | ✓ partly |
| `find:*` | U | **arbitrary exec** | `search_files`, `list_directory` | ✓ |
| `python -m pytest:*` | U | arbitrary code | `run_pytest_check` | ✓ |
| `./tools/lint_imports.sh`, `tach_check.sh`, `vulture_check.sh` | U | checks | `run_lint_imports_check`, `run_tach_check`, `run_vulture_check` | ✓ |
| `./tools/format_all.sh`, `pycycle_check.sh` | U | — | not in this repo → delete? | ✓ |
| `mcp-coder check file-size:*` | U | read | `check_file_size` | ✓ |
| `mcp-coder gh-tool get-base-branch` | U | read | `get_base_branch` | ✓ |
| `mcp-coder gh-tool:*` | L | set-status, **define-labels**, **checkout-issue-branch**, issue-stats, get-base-branch | `github_issue_set_status`, `get_base_branch`; rest none → drop or narrow | ⏳ |
| `tools/jenkins_*.sh/.bat:*` | L | Jenkins read | none | ✗ |
| `start docs/architecture/dependency_graph.html` | L | opens browser | none (human action) → drop? | ✗ |

**Skills / agents / CLAUDE.md**

| Former Bash | Now | Where | |
|---|---|---|---|
| `gh issue view/create/edit/comment`, `gh pr create` | `github_issue_*`, `github_pr_create` | all skills, agents, CLAUDE.md (#1406) | ✅ |
| `git commit`, `git push`, `git push --force-with-lease`, `git checkout -b` / `git branch` | `git_commit`, `git_push`, `git_push_force`, `git_branch` | commit_push, rebase, pr_comment_triage, commit-pusher, CLAUDE.md (#1421) | ⏳ |
| `git rebase/add/rm/restore/stash/checkout --ours/--theirs *` | Bash | rebase | ✗ |
| `git remote get-url *` | Bash | rebase | ✗ (`ls_remote` is not equivalent) |
| `git push --force-with-lease *` | Bash fallback | rebase (when `git_push_force` refuses) | ✗ |
| `mcp-coder gh-tool set-status *` | Bash | approve skills, pr_comment_triage, issue-approver; implement_direct: all of `gh-tool *` | ⏳ `github_issue_set_status` (#391) — not yet used anywhere |
| `/approve` comment for cross-repo issues | `github_issue_comment` | issue_approve, issue-approver | ⏳ `github_issue_set_status` with `reference_name`? — check whether the comment triggers more than the label |

⏳ = tools installed since T18 (2026-11-15); the replacement in skills / agents is still to do (T21).

**Target: Bash only as last resort.** No Bash in any allow-list; every call prompts. What still needs Bash after T15 + T21:

| Bash left | Why | Plan |
|---|---|---|
| `git rebase/add/rm/restore/stash/checkout --ours/--theirs` | rebase conflict handling, no MCP tool | keep in `rebase` skill only (turn-scoped); option: request MCP rebase tools upstream |
| `git push --force-with-lease` | fallback when `git_push_force` refuses (no reflog, fresh clone) | keep in `rebase` skill, prompts |
| `tools/jenkins_*.sh` | Jenkins read, no MCP tool | T20: MCP tool vs prompt |
| `git remote get-url` | dead grant in `rebase` `allowed-tools`, never used | remove |
| `mcp-coder gh-tool` define-labels / checkout-issue-branch / issue-stats, `start …html` | human CLI actions | drop from allow-list |
