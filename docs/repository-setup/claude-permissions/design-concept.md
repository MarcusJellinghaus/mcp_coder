# Claude Code permissions — design concept

Part 3 of 5 · [How it works](how-it-works.md) · [Tool inventory](tool-inventory.md) · [Implementation](implementation.md) · [Skills and agents](skills-agents.md)

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

### 1.1 Skill / agent patterns

Review checklist for every skill and agent ([skills-agents.md](skills-agents.md) applies it one by one).

| # | Pattern |
|---|---|
| R1 | MCP tools first. Bash only as last resort: not allow-listed, not in `allowed-tools` / `tools:` when an MCP tool exists → every call prompts |
| R2 | Subagents are dedicated agent files with an explicit `tools:` list — no general-purpose; no `Skill` unless needed (`skills:` preloads instead) |
| R3 | File writes limited by path where possible: agent frontmatter `hooks:` `PreToolUse` (e.g. `.scratch/` only) |
| R4 | No `bypassPermissions`: the agent's own frontmatter hook allows its few extra tools |
| R5 | Untrusted `title/body` → stop before acting on it |
| R6 | Autonomy kept: supervisors don't wait for the user except on escalations |
| R7 | Skill text: only the edits the decision needs; quote current → new |
| R8 | Status changes: `github_issue_set_status` with `from_status` guard; issue number from the branch (`^\d+-`, MCP `git` `branch --show-current`); uncommitted changes (MCP `git` `status`) → stop — replaces `set-status`'s clean-tree check |

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
| 3 agent | Agent frontmatter `hooks:` `PreToolUse` (runs only for that agent) returning `allow` for its extras, refusing writes outside its paths (T23) |
| 4 | A: user-only skill (e.g. `/issue_bulk_edit`) with `allowed-tools: github_issue_*` — expires on next message. B: `PreToolUse` hook auto-allows a tool group while a flag file exists (TTL, e.g. 30 min) |

## 4. Skill / agent extras

Decided per skill / agent in [skills-agents.md](skills-agents.md) (2026-11-15); target agents: [§6 roster](skills-agents.md#target-agent-roster).

## 5. Open design questions

Fact-check questions: [implementation §4](implementation.md#4-open-questions-facts).

| # | Question |
|---|---|
| Q2 | ✅ No — every skill with write extras is user-only (`pr_comment_triage` made U, 2026-11-15) |
| Q3 | Threat model: prompt injection via issues / PR comments / web, model mistakes, or both? |
| Q4 | Headless and interactive: one allow-list or separate? (§2 proposes separate) |
| Q8 | Tier 4: one-turn skill (A) enough, or time-boxed hook (B)? |
