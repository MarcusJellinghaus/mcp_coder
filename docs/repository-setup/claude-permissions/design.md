# Claude Code permissions — design

Part 2 of 3 · [How it works](how-it-works.md) · [TODOs](todos.md)

**Status:** draft. Open: threat model (Q3), §4.3 per-skill review.
**Scope:** this repo — interactive sessions, skills, agents/subagents, MCP tools, headless `mcp-coder` workflows. Not: Copilot CLI ([copilot.md](../copilot.md)), iCoder's `.icoder/` permission layer.
**Related:** [agent-permissions.md](../agent-permissions.md), [claude-code.md](../claude-code.md#enhanced-claude-permissions).

## 1. Current setup

### 1.1 Settings files

Levels and combining rules: [how-it-works §2](how-it-works.md#2-settings-files).

| # | Level | In use | Content today |
|---|---|---|---|
| 1 | Managed policy | no | — |
| 2 | CLI flags | headless only | mcp-coder passes `--settings settings.local.json`, `--allowedTools` Bash grants |
| 3 | `.claude/settings.local.json` | yes — **tracked** here as template | ~80 allows, MCP enablement; no `deny` / `ask` |
| 4 | `.claude/settings.json` | **absent** | — |
| 5 | `~/.claude/settings.json` | yes | `env`, model, UI, `defaultMode: acceptEdits`, ~45 allows (many stale), `WebFetch(domain:*)`, `Bash(find:*)` |

**Effective today**

| Key | Result |
|---|---|
| `permissions.allow` | user ~45 + local ~80 — all active |
| `permissions.deny` / `ask` | none |
| `defaultMode` | `acceptEdits` (only user sets it) |
| `env` | user's 5 vars |
| `enabledMcpjsonServers`, `enableAllProjectMcpServers` | local |
| `model`, `tui`, … | user |
| Headless `--settings` | `settings.local.json` read twice (CLI + cwd discovery) — same content |

### 1.2 Agents

| Agent | `tools` | `permissionMode` | Launched by |
|---|---|---|---|
| `commit-pusher` | Bash, git (R), run_format_code, read_file | `bypassPermissions` | review/plan supervisors |
| `issue-updater` | Bash, issue_view, save/edit/delete file, read_file | `bypassPermissions` | issue_analyse_supervisor |
| `issue-approver` | Bash, issue_view, read_file, git (R) | `bypassPermissions` | issue_analyse_supervisor |

Intent: unrestricted `Bash` + bypass → git/gh unprompted. Parent `acceptEdits` (user default) overrides it → F9.

### 1.3 Skills

`UI` = `disable-model-invocation: true`. Pre-approvals listed only where they exceed the allow-list.

| Skill | UI | Extra pre-approvals |
|---|---|---|
| check_branch_status | – | – |
| commit_push | ✓ | `Bash(git add/commit/push *)` |
| discuss | ✓ | – |
| implement_direct | ✓ | – |
| implementation_approve | ✓ | – |
| implementation_finalise | ✓ | – |
| implementation_needs_rework | ✓ | – |
| implementation_new_tasks | ✓ | – |
| implementation_review | – | – |
| implementation_review_supervisor | ✓ | – |
| issue_analyse | – | – |
| issue_analyse_supervisor | ✓ | – |
| issue_approve | ✓ | `Bash(gh issue view *)`, `Bash(MSYS_NO_PATHCONV=1 gh issue comment *)` |
| issue_create | ✓ | `Bash(gh issue create *)` |
| issue_requirements | ✓ | – |
| issue_update | ✓ | `Bash(gh issue edit *)` |
| plan_approve | ✓ | – |
| plan_review | – | – |
| plan_review_supervisor | ✓ | – |
| plan_update | – | – |
| pr_comment_triage | **–** | GitHub writes (review reply, thread resolve, issue comment), `Bash(git add *)` |
| rebase | ✓ | `Bash(git rebase/add/rm/commit/checkout/restore/stash *)`, `Bash(git push --force-with-lease *)` |

Knowledge base readers: `implementation_review_supervisor`, `issue_analyse_supervisor`, `plan_review_supervisor`, `plan_review`.

### 1.4 Headless workflows (`mcp-coder implement`, `rebase`, `fix-ci`, …)

| Control | Value |
|---|---|
| Built-in tools | `--tools ToolSearch` (+ `Bash` only if grants) — Read/Write/Edit/Bash off |
| MCP servers | `--mcp-config <file> --strict-mcp-config` |
| Settings | `--settings <file>`; auto-detect `settings.local.json` → `settings.json`; Claude also merges repo files via cwd |
| Bash | exact grants via `--allowedTools` from toolkit `llm_permissions` |
| Rebase | generated least-privilege settings (`workflows/rebase_permissions.py`); Python does all git writes + push |

## 2. Tool inventory

`A` = in an allow-list (L = local, U = user, S = skill-only); `–` = prompts.

### 2.1 mcp-workspace

| Topic | Read | A | Write | A |
|---|---|---|---|---|
| Workspace files | read_file, list_directory, search_files, check_file_size | L | save_file, edit_file, append_file, move_file, delete_this_file, delete_directory | L |
| Reference projects | get_reference_projects, list_reference_directory, read_reference_file, search_reference_files | L | — | |
| Git | git (read-only allowlist; `fetch` touches network/refs), get_base_branch, check_branch_status | L | — (upstream: §2.6 ⏳) | |
| GitHub issues | github_issue_view, github_issue_list, github_search, github_label_list | L | github_issue_create, github_issue_edit, github_issue_comment | – (comment: S) |
| GitHub sub-issues | github_subissue_list | – | github_subissue_add, github_subissue_remove | – |
| GitHub PRs | github_pr_view | L | github_pr_create, github_review_comment_reply, github_review_thread_resolve | – (reply/resolve: S) |

GitHub writes accept `reference_name` → can write to sibling repos.

### 2.2 mcp-tools-py

| Topic | Read / analyse | A | Write / execute | A |
|---|---|---|---|---|
| Static checks | run_pylint_check, run_mypy_check, run_ruff_check, run_bandit_check, run_vulture_check, run_lint_imports_check, run_tach_check | L | — | |
| Dependency check | run_deptry_check | – | — | |
| Tests | — | | run_pytest_check (**executes project code**) | L |
| Formatting | — | | run_format_code, run_ruff_fix | L |
| Refactoring | list_symbols, find_references | L | move_symbol, move_module, rename_symbol | L |
| Library source | get_library_source, search_library_files | L | — | |
| Misc | sleep | L | — | |

### 2.3 obsidian-wiki (user-scope server)

| Topic | Read | A | Write | A |
|---|---|---|---|---|
| Vault notes | list_vaults, read_note, search_vault | L | create_note, edit_note, move_note, **delete_note**, create_directory | L |
| Tags | — | | add_tags, remove_tags, manage_tags, rename_tag | L |

"Write only to `Field Notes/`" is CLAUDE.md prose — not enforced.

### 2.4 claude-artifacts (claude.ai connector)

| Topic | Read | A | Write | A |
|---|---|---|---|---|
| Artifacts | guide, get/read/list_artifacts, list_files, read_file, list/describe_types | – | publish_version, publish_files, edit_version, delete_artifact, pin/unpin | – |
| Assets / data / comments | list/read_asset, db_get/list/query, read_comments | – | upload_asset, db_write, reply_comment, resolve_comment | – |

Write = publishes off-machine.

### 2.5 Claude Code built-ins

| Topic | Read | A | Write / execute | A |
|---|---|---|---|---|
| Files | Read, Glob, Grep | mode | Write, Edit, NotebookEdit | `acceptEdits` (U) |
| Shell | — | | Bash, PowerShell | patterns (L, U) |
| Web | WebSearch | – | WebFetch | `domain:*` (L, U) |
| Orchestration | ToolSearch, AskUserQuestion | | Agent, Skill, Workflow, SendMessage | Skill: L |
| Other | — | | Cron*, ScheduleWakeup, RemoteTrigger, EnterWorktree, PushNotification | – |

### 2.6 Bash patterns → MCP replacement

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

## 3. Findings

| # | Finding |
|---|---|
| F1 | No `deny` rules, no `ask` rules, no hooks anywhere |
| F2 | User `defaultMode: acceptEdits` applies to every repo |
| F3 | `WebFetch(domain:*)` = unrestricted outbound channel |
| F4 | Agents: `bypassPermissions` + unrestricted Bash |
| F5 | `pr_comment_triage` is model-invocable and pre-approves GitHub writes |
| F6 | `pr_comment_triage` lists `git_commit` / `git_push` — exist upstream, not in installed server |
| F7 | User allow-list holds stale server names (`mcp__code-checker__*`, `mcp__filesystem__*`) |
| F8 | `settings.local.json` is tracked here (template) — "local" file acting as shared config |
| F9 | Agents' `bypassPermissions` likely ineffective: parent `acceptEdits` wins ([how-it-works §6](how-it-works.md#6-subagents)) |
| F10 | Under real `bypassPermissions`, writes to `.git` / `.claude` are allowed — agent could rewrite skills/settings |

## 4. Target design

### 4.1 Settings layout

Control in two files: user = machine + safety net, project = permissions.

| File | Holds | Not |
|---|---|---|
| `~/.claude/settings.json` | `env` (MCP venv vars — `.mcp.json` needs them), `model`, `modelSettings`, UI; optional small **`deny`** baseline | `allow`, `ask` |
| `.claude/settings.json` (committed) | `allow` / `ask` / `deny`, `defaultMode`, `enabledMcpjsonServers` | personal extras |
| `.claude/settings.local.json` (gitignored) | empty / absent — personal experiments only | baseline permissions |

| Effect | Detail |
|---|---|
| Single review point | permissions per repo in git, diffable, deployable by `mcp-coder init` |
| User `deny` still global | deny wins at any level |
| Outside a repo | no allows → everything prompts (intended) |
| Fixes | F7, F8, user-level `find:*` / `python -m pytest:*` |

Migration: diff each repo's `settings.local.json` against user `allow` before deleting user entries (mcp-workspace, mcp-tools-py, AutoRunner each have their own local file).

### 4.2 Tiers

| Tier | Context | Allowed without asking | Asks | Off |
|---|---|---|---|---|
| 1 Headless | `mcp-coder implement`, `create-plan`, `fix-ci`, … | workspace files, git read, mcp-tools-py | — (no one to ask → denied) | Bash, built-in Read/Write/Edit, other MCP servers |
| 2 Interactive | your Claude session | Tier 1 + GitHub read, reference projects | everything else | nothing |
| 3 Skill / agent | `/skill`, `.claude/agents/*` | Tier 2 + its own extras (§4.3) | rest | — |
| 4 Special mode | "edit all issues per plan" | Tier 2 + one tool group, time-boxed | rest | — |

| Tier | Mechanism | Exists today? |
|---|---|---|
| 1 | Generated settings per command (as `rebase_settings`), `--tools ToolSearch`, `--strict-mcp-config`, toolkit grants via `--allowedTools`, `--permission-mode dontAsk` | partly — non-rebase commands pass the full interactive `settings.local.json` (+ user allows) |
| 2 | Committed `.claude/settings.json` allow = mcp-workspace read/file tools + `mcp__mcp-tools-py`; `defaultMode: default` (`acceptEdits` auto-accepts native edits + `mkdir/mv/cp`) | no |
| 3 skill | `allowed-tools` (turn-scoped) + `disable-model-invocation` on every skill with write extras | yes; gaps: F5, grant dies on user reply, does not reach subagents |
| 3 agent | `PreToolUse` hook keyed on `agent_type` returning `allow` for that agent's extras | no |
| 4 | A: user-only skill (e.g. `/issue_bulk_edit`) with `allowed-tools: github_issue_*` — expires on next message. B: `PreToolUse` hook auto-allows a tool group while a flag file exists (TTL, e.g. 30 min) | no |

Avoid for Tier 4: "don't ask again" at the prompt — permanent rule.

### 4.3 Skill / agent extras — first pass (to brainstorm)

Extras = beyond Tier 2. MCP names assume T18 (git write tools).

| Skill / agent | Extras needed | Model-invocable |
|---|---|---|
| issue_analyse, issue_requirements, discuss, plan_review, plan_update, implementation_review, implementation_new_tasks, implementation_finalise, check_branch_status | none | mixed |
| issue_create | `github_issue_create` | no |
| issue_update | `github_issue_edit` | no |
| issue_approve | `set-status`, `github_issue_comment` (cross-repo `/approve`) | no |
| plan_approve, implementation_approve, implementation_needs_rework | `set-status` | no |
| implement_direct | `set-status` (today: all of `gh-tool *`) | no |
| commit_push | `git_commit`, `git_push` | no |
| rebase | `git rebase/rm/restore/stash/checkout --ours/--theirs` (Bash), `git_push_force` | no |
| pr_comment_triage | `github_review_comment_reply`, `github_review_thread_resolve`, `github_issue_comment`, `git_commit`, `git_push`, `set-status` | **yes** → change? |
| *_supervisor | `Agent`; extras via agents below | no |
| commit-pusher | `git_commit`, `git_push` → no Bash | — |
| issue-updater | `github_issue_edit` → no Bash | — |
| issue-approver | `set-status`, `github_issue_comment` | — |
| engineer subagents (general-purpose) | none — Tier 2 | — |

After T18 only `set-status` and `rebase` conflict commands still need Bash.
