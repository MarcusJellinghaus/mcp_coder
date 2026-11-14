# Claude Code permissions — design concept

Part 3 of 4 · [How it works](how-it-works.md) · [Tool inventory](tool-inventory.md) · [Implementation](implementation.md)

**Status:** draft. Open: §5.
**Scope:** this repo — interactive sessions, skills, agents/subagents, MCP tools, headless `mcp-coder` workflows. Not: Copilot CLI ([copilot.md](../copilot.md)), iCoder's `.icoder/` permission layer.
**Related:** [agent-permissions.md](../agent-permissions.md), [claude-code.md](../claude-code.md#enhanced-claude-permissions).

## 1. Principles

| # | Principle |
|---|---|
| P1 | MCP tools over Bash; Bash only where no MCP equivalent exists ([inventory §6](tool-inventory.md#6-bash-patterns--mcp-replacement)) |
| P2 | Permissions live in the committed project file; user file = machine settings + optional `deny` |
| P3 | Grant by context (tier), not globally |
| P4 | No permanent grants from prompts ("don't ask again" writes a rule) |

## 2. Tiers

| Tier | Context | Allowed without asking | Asks | Off |
|---|---|---|---|---|
| 1 Headless | `mcp-coder implement`, `create-plan`, `fix-ci`, … | workspace files, git read, mcp-tools-py | — (no one to ask → denied) | Bash, built-in Read/Write/Edit, other MCP servers |
| 2 Interactive | your Claude session | Tier 1 + GitHub read, reference projects | everything else | nothing |
| 3 Skill / agent | `/skill`, `.claude/agents/*` | Tier 2 + its own extras (§4) | rest | — |
| 4 Special mode | "edit all issues per plan" | Tier 2 + one tool group, time-boxed | rest | — |

## 3. Mechanisms

Background: [how-it-works §5–§10](how-it-works.md#5-skills).

| Tier | Mechanism |
|---|---|
| 1 | Generated settings per command (as `rebase_settings`), `--tools ToolSearch`, `--strict-mcp-config`, toolkit grants via `--allowedTools`, `--permission-mode dontAsk` |
| 2 | Committed `.claude/settings.json`: allow = mcp-workspace read/file tools + `mcp__mcp-tools-py`; `defaultMode: default` (`acceptEdits` auto-accepts native edits + `mkdir/mv/cp`) |
| 3 skill | `allowed-tools` (turn-scoped) + `disable-model-invocation` on every skill with write extras |
| 3 agent | `PreToolUse` hook keyed on `agent_type` returning `allow` for that agent's extras |
| 4 | A: user-only skill (e.g. `/issue_bulk_edit`) with `allowed-tools: github_issue_*` — expires on next message. B: `PreToolUse` hook auto-allows a tool group while a flag file exists (TTL, e.g. 30 min) |

## 4. Skill / agent extras — first pass (to brainstorm)

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

## 5. Open design questions

Fact-check questions: [implementation §4](implementation.md#4-open-questions-facts).

| # | Question |
|---|---|
| Q2 | Should a skill's pre-approved GitHub writes be allowed for model-invoked skills at all? |
| Q3 | Threat model: prompt injection via issues / PR comments / web, model mistakes, or both? |
| Q4 | Headless and interactive: one allow-list or separate? (§2 proposes separate) |
| Q8 | Tier 4: one-turn skill (A) enough, or time-boxed hook (B)? |
