# Claude Code permissions — skills and agents

Part 5 of 5 · [How it works](how-it-works.md) · [Tool inventory](tool-inventory.md) · [Design concept](design-concept.md) · [Implementation](implementation.md)

Per skill / agent: facts, proposal, decision. Tiers and mechanisms: [concept §2–§3](design-concept.md#2-tiers). Tier 2 baseline = workspace files, git read, mcp-tools-py, GitHub read, reference projects.

## 1. Overview

| Caller | Meaning |
|---|---|
| U | user only (`disable-model-invocation: true`) |
| U/M | user or model (Skill tool) |
| S | launched by a supervisor skill — but any session can launch an agent |

🆕 = tool not in the installed server ([inventory §1](tool-inventory.md#1-mcp-workspace)).

| § | Skill / agent | Caller | Reads | Writes local | Writes GitHub / git | Subagents |
|---|---|---|---|---|---|---|
| 2 | issue_analyse | U/M | issue, code | – | – | – |
| 2 | issue_analyse_supervisor | U | issue, knowledge base | analysis log | via agents | engineer ×n, issue-updater, issue-approver |
| 2 | issue_requirements | U | conversation | – | – | – |
| 2 | issue_create | U | conversation | – | issue create | – |
| 2 | issue_update | U | issue | `.scratch/` | issue edit | – |
| 2 | issue_approve | U | issue | – | status (Bash), `/approve` comment | – |
| 2 | issue-updater *(agent)* | S | issue | `.scratch/` | issue edit | – |
| 2 | issue-approver *(agent)* | S | issue | – | status (**Bash**), `/approve` comment | – |
| 3 | plan_review | U/M | plan, code, knowledge base | – | – | – |
| 3 | plan_review_supervisor | U | issue, plan, knowledge base | review log | via agent | engineer ×n, commit-pusher |
| 3 | plan_update | U/M | plan | plan files | – | – |
| 3 | plan_approve | U | – | – | status (Bash) | – |
| 4 | implement_direct | U | issue, code | code | status (Bash, all of `gh-tool`) | – |
| 4 | implementation_review | U/M | diff, code | – | – | – |
| 4 | implementation_review_supervisor | U | issue, plan, knowledge base | review log | via agent | engineer ×n, commit-pusher |
| 4 | implementation_new_tasks | U | review | plan files | – | – |
| 4 | implementation_needs_rework | U | – | – | status (Bash) | – |
| 4 | implementation_finalise | U | task tracker, code | code, tracker | – | – |
| 4 | implementation_approve | U | review | – | status (Bash) | – |
| 5 | commit_push | U | diff | format | 🆕 commit, push | – |
| 5 | rebase | U | diff | conflict files | 🆕 commit, force-push; Bash git | – |
| 5 | pr_comment_triage | **U/M** | PR, alerts | code | replies, resolve, comment, 🆕 commit, push, status (Bash) | – |
| 5 | check_branch_status | U/M | CI, PR, labels | – | – | – |
| 5 | commit-pusher *(agent)* | S | diff | format | 🆕 commit, push | – |
| 6 | discuss | U | conversation | – | – | – |
| 6 | engineer *(general-purpose subagent)* | S | **all tools** | **all tools** | **all tools, incl. Bash** | – |

## 2. Issue

### issue_analyse

| Row | Content |
|---|---|
| Purpose / caller | Discuss an issue against the codebase, no code. U/M; also run by supervisor engineers |
| Launches | – |
| Uses | `github_issue_view`, `git` (`ls_remote`), `read_file`, `list_directory`; `.vscodeclaude_status.txt` |
| Pre-approved | nothing beyond Tier 2 |
| Risk | Reads issue text, possibly from untrusted authors (prompt injection). Read-only itself; the risk is what the session does next |
| Proposal | Keep as is — Tier 2, model-invocable |
| Decision | |

### issue_analyse_supervisor

| Row | Content |
|---|---|
| Purpose / caller | Autonomous loop, max 5 rounds: engineer analyses → supervisor triages, asks the user on scope → issue-updater writes → issue-approver sets `status-02` (queues automated planning). U |
| Launches | engineer (general-purpose) per round, issue-updater, issue-approver |
| Uses | `github_issue_view`, `read_file` (knowledge base), file tools for `pr_info/issue_analysis_log.md`, `Agent` |
| Pre-approved | nothing beyond Tier 2 (log writes rely on the allow-list) |
| Risk | ① Engineers are general-purpose → **all tools incl. Bash**; "analysis is read-only" is prose only. ② Issue is edited and approved without the user seeing the final text. ③ Untrusted issue text flows into every engineer prompt |
| Proposal | ① Custom read-only agent `issue-analyst` (MCP read tools only, no Bash, no writes) instead of general-purpose. ② Keep autonomy, or stop for user confirmation before approve — your call. ③ Stop early when the issue has untrusted `title/body` |
| Decision | |

### issue_requirements

| Row | Content |
|---|---|
| Purpose / caller | Summarise decided / open requirements from the conversation. U |
| Launches | – |
| Uses | no tools |
| Pre-approved | – |
| Risk | none |
| Proposal | Keep |
| Decision | |

### issue_create

| Row | Content |
|---|---|
| Purpose / caller | Create a GitHub issue from the conversation. U |
| Launches | – |
| Uses | `github_issue_create`, `git` (`ls_remote` for base branch) |
| Pre-approved | `github_issue_create` |
| Risk | Publishes conversation content. Tool accepts `reference_name` → could create in a sibling repo |
| Proposal | Keep — U-only + one-turn grant fits |
| Decision | |

### issue_update

| Row | Content |
|---|---|
| Purpose / caller | Rewrite issue title/body after analysis. U |
| Launches | – |
| Uses | `github_issue_view`, `github_issue_edit`, file tools for `.scratch/` body file |
| Pre-approved | `github_issue_edit` (+ file tools, already Tier 2) |
| Risk | Overwrites the body (content loss). Already guarded: stops on truncated view, failed fetch, untrusted `title/body` |
| Proposal | Keep. File writes can't be limited to `.scratch/` — MCP rules match tool names, not arguments |
| Decision | |

### issue_approve

| Row | Content |
|---|---|
| Purpose / caller | Promote status: `01→02`, `04→05`, `07→08`. Cross-repo: comment `/approve` (a GitHub Action sets the label). U |
| Launches | – |
| Uses | `github_issue_view`, `git` (`ls_remote`), `get_reference_projects`, `github_issue_comment`, Bash `mcp-coder gh-tool set-status` |
| Pre-approved | `Bash(mcp-coder gh-tool set-status *)`, `github_issue_comment` |
| Risk | `02` and `05` start automated Jenkins workflows (cost, code changes). `github_issue_comment` is pre-approved for any body on any issue, not only `/approve` |
| Proposal | After T18: `github_issue_set_status` (workspace and reference repos) replaces Bash and the `/approve` comment → T21. Check first: does the `/approve` Action do more than set the label? |
| Decision | |

### issue-updater *(agent)*

| Row | Content |
|---|---|
| Purpose / caller | Runs the `issue_update` process unattended with content from its launch prompt. S (issue_analyse_supervisor) |
| Launches | – |
| Uses | `github_issue_view`, `github_issue_edit`, file tools, `delete_directory` |
| Pre-approved | `permissionMode: bypassPermissions` — likely overridden by your `acceptEdits` default (F9) |
| Risk | Any session can launch it with any content and issue number. `delete_directory` is broader than the `.scratch/` cleanup needs |
| Proposal | Drop bypass; allow `github_issue_edit` via `PreToolUse` hook keyed on `agent_type` (concept §3). Remove `delete_directory` |
| Decision | |

### issue-approver *(agent)*

| Row | Content |
|---|---|
| Purpose / caller | Runs the `issue_approve` steps unattended. S (issue_analyse_supervisor) |
| Launches | – |
| Uses | **Bash** (`set-status`), `github_issue_view`, `github_issue_comment`, `git`, `get_reference_projects`, `read_file` |
| Pre-approved | `bypassPermissions` (F9 applies) |
| Risk | Unrestricted Bash — "`set-status` only" is prose. Any session can launch it |
| Proposal | T21: Bash → `github_issue_set_status`; then no Bash. Until then: T7 hook limiting Bash to `set-status` |
| Decision | |

## 3. Plan

Details: next round.

## 4. Implementation

Details: next round.

## 5. Git / PR

Details: next round.

## 6. Other

Details: next round. Engineer subagents are general-purpose (all tools); a read-only and a read-write engineer agent would cover the supervisors' needs.
