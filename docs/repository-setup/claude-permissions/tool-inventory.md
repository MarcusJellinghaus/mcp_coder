# Claude Code permissions — tool inventory

Part 2 of 4 · [How it works](how-it-works.md) · [Design concept](design-concept.md) · [Implementation](implementation.md)

`A` = in an allow-list (L = `settings.local.json`, U = user settings, S = skill `allowed-tools` only); `–` = prompts.

## 1. mcp-workspace

| Topic | Read | A | Write | A |
|---|---|---|---|---|
| Workspace files | read_file, list_directory, search_files, check_file_size | L | save_file, edit_file, append_file, move_file, delete_this_file, delete_directory | L |
| Reference projects | get_reference_projects, list_reference_directory, read_reference_file, search_reference_files | L | — | |
| Git | git (read-only allowlist; `fetch` touches network/refs), get_base_branch, check_branch_status | L | — (upstream: §6 ⏳) | |
| GitHub issues | github_issue_view, github_issue_list, github_search, github_label_list | L | github_issue_create, github_issue_edit, github_issue_comment | – (comment: S) |
| GitHub sub-issues | github_subissue_list | – | github_subissue_add, github_subissue_remove | – |
| GitHub PRs | github_pr_view | L | github_pr_create, github_review_comment_reply, github_review_thread_resolve | – (reply/resolve: S) |

GitHub writes accept `reference_name` → can write to sibling repos.

## 2. mcp-tools-py

| Topic | Read / analyse | A | Write / execute | A |
|---|---|---|---|---|
| Static checks | run_pylint_check, run_mypy_check, run_ruff_check, run_bandit_check, run_vulture_check, run_lint_imports_check, run_tach_check | L | — | |
| Dependency check | run_deptry_check | – | — | |
| Tests | — | | run_pytest_check (**executes project code**) | L |
| Formatting | — | | run_format_code, run_ruff_fix | L |
| Refactoring | list_symbols, find_references | L | move_symbol, move_module, rename_symbol | L |
| Library source | get_library_source, search_library_files | L | — | |
| Misc | sleep | L | — | |

## 3. obsidian-wiki (user-scope server)

| Topic | Read | A | Write | A |
|---|---|---|---|---|
| Vault notes | list_vaults, read_note, search_vault | L | create_note, edit_note, move_note, **delete_note**, create_directory | L |
| Tags | — | | add_tags, remove_tags, manage_tags, rename_tag | L |

"Write only to `Field Notes/`" is CLAUDE.md prose — not enforced.

## 4. claude-artifacts (claude.ai connector)

| Topic | Read | A | Write | A |
|---|---|---|---|---|
| Artifacts | guide, get/read/list_artifacts, list_files, read_file, list/describe_types | – | publish_version, publish_files, edit_version, delete_artifact, pin/unpin | – |
| Assets / data / comments | list/read_asset, db_get/list/query, read_comments | – | upload_asset, db_write, reply_comment, resolve_comment | – |

Write = publishes off-machine.

## 5. Claude Code built-ins

| Topic | Read | A | Write / execute | A |
|---|---|---|---|---|
| Files | Read, Glob, Grep | mode | Write, Edit, NotebookEdit | `acceptEdits` (U) |
| Shell | — | | Bash, PowerShell | patterns (L, U) |
| Web | WebSearch | – | WebFetch | `domain:*` (L, U) |
| Orchestration | ToolSearch, AskUserQuestion | | Agent, Skill, Workflow, SendMessage | Skill: L |
| Other | — | | Cron*, ScheduleWakeup, RemoteTrigger, EnterWorktree, PushNotification | – |

## 6. Bash patterns → MCP replacement

✓ = replace now, ⏳ = after mcp-workspace upgrade, ✗ = no MCP equivalent.

**Allow-lists**

| Pattern | File | Reach | MCP replacement | |
|---|---|---|---|---|
| `git diff/status/ls-tree:*` | U | read | `mcp-workspace__git` | ✓ |
| `git mv:*` | U | write | `move_file` (git-aware) | ✓ |
| `gh issue view:*` | U, S | read | `github_issue_view` (+ `reference_name`) | ✓ |
| `gh run view:*` | U | read | `check_branch_status` (current branch CI + log) | ✓ partly |
| `find:*` | U | **arbitrary exec** | `search_files`, `list_directory` | ✓ |
| `python -m pytest:*` | U | arbitrary code | `run_pytest_check` | ✓ |
| `./tools/lint_imports.sh`, `tach_check.sh`, `vulture_check.sh` | U | checks | `run_lint_imports_check`, `run_tach_check`, `run_vulture_check` | ✓ |
| `./tools/format_all.sh`, `pycycle_check.sh` | U | — | not in this repo → delete? | ✓ |
| `mcp-coder check file-size:*` | U | read | `check_file_size` | ✓ |
| `mcp-coder gh-tool get-base-branch` | U | read | `get_base_branch` | ✓ |
| `mcp-coder gh-tool:*` | L | set-status, **define-labels**, **checkout-issue-branch**, issue-stats, get-base-branch | none for `set-status` (MCP rejects `status-*` by design) → narrow | ✗ |
| `tools/jenkins_*.sh/.bat:*` | L | Jenkins read | none | ✗ |
| `start docs/architecture/dependency_graph.html` | L | opens browser | none (human action) → drop? | ✗ |

**Skills / agents**

| Pattern | Used by | MCP replacement | |
|---|---|---|---|
| `gh issue create *` | issue_create | `github_issue_create` | ✓ |
| `gh issue edit *` | issue_update, issue-updater | `github_issue_edit` | ✓ |
| `gh issue comment *` (`/approve`) | issue_approve, issue-approver | `github_issue_comment` (+ `reference_name`) | ✓ |
| `gh pr create` | CLAUDE.md | `github_pr_create` | ✓ |
| `git commit *` | commit_push, rebase, commit-pusher | `git_commit` | ⏳ |
| `git push *` | commit_push, commit-pusher | `git_push` | ⏳ |
| `git push --force-with-lease *` | rebase | `git_push_force` | ⏳ |
| `git checkout -b`, `git branch` | CLAUDE.md | `git_branch` | ⏳ |
| `git add *` | commit_push, rebase, pr_comment_triage | folded into `git_commit(paths=…)` | ⏳ |
| `git rebase/rm/restore/stash/checkout --ours/--theirs *` | rebase | none | ✗ |
| `git remote get-url *` | rebase | none (`ls_remote` is not equivalent) | ✗ |
| `mcp-coder gh-tool set-status *` | approve skills, issue-approver | none (by design) | ✗ |

⏳ tools exist upstream (mcp-workspace `toolset/git_write.py`, group `workspace.git`, #399), not exposed by the installed server.
