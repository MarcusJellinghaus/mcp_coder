# Claude Code permissions — design concept

Part 3 of 3 · [How Claude permissions work](how-it-works.md) · [Tool inventory](tool-inventory.md)

**Scope:** this repo — interactive sessions, skills, agents/subagents, MCP tools, headless `mcp-coder` workflows. Not: Copilot CLI ([copilot.md](../copilot.md)), iCoder's `.icoder/` permission layer.
**Related:** [agent-permissions.md](../agent-permissions.md), [claude-code.md](../claude-code.md#enhanced-claude-permissions). Open work: [#1434](https://github.com/MarcusJellinghaus/mcp_coder/issues/1434) (tracking), [#1433](https://github.com/MarcusJellinghaus/mcp_coder/issues/1433) (settings layout). CI warning: [`check-sensitive-files`](../quality-and-security-checks.md#repo-hygiene).

## 1. Principles

| # | Principle |
|---|---|
| P1 | MCP tools over Bash; Bash only where no MCP equivalent exists ([inventory §6](tool-inventory.md#6-bash-patterns--mcp-replacement)) |
| P2 | Permissions live in the committed project file; user file = machine settings + optional `deny` (layout: backlog [#1433](https://github.com/MarcusJellinghaus/mcp_coder/issues/1433)) |
| P3 | Grant by context (tier), not globally |
| P4 | No permanent grants from prompts ("don't ask again" writes a rule) |
| P5 | Threat model: prompt injection (issues, PR comments, web, reference repos) and model mistakes. Injection decides conflicts; mistakes are covered where it costs no autonomy (path limits, read-only rules, `from_status`) |

### 1.1 Skill / agent patterns

Review checklist for every skill and agent. Agents in this repo: [agent-permissions.md](../agent-permissions.md#agents-in-this-repo).

| # | Pattern |
|---|---|
| R1 | MCP tools first. Bash only as last resort: not allow-listed, not in `allowed-tools` / `tools:` when an MCP tool exists → every call prompts |
| R2 | Subagents are dedicated agent files with an explicit `tools:` list — no general-purpose; no `Skill` unless needed (`skills:` preloads instead) |
| R3 | File writes limited by path where possible: agent frontmatter `hooks:` `PreToolUse` (e.g. `.scratch/` only) |
| R4 | No `bypassPermissions`: the agent's own frontmatter hook allows its few extra tools |
| R5 | Untrusted `title/body` → stop before acting on it |
| R6 | Autonomy kept: supervisors don't wait for the user except on escalations |
| R7 | Skill text: only the edits the decision needs; quote current → new |
| R8 | Status changes: `github_issue_set_status` with `from_status` guard; issue number from the branch (`^\d+-`, MCP `git` `branch --show-current`); uncommitted changes (MCP `git` `status`) → stop |

## 2. Tiers

| Tier | Context | Allowed without asking | Asks | Off |
|---|---|---|---|---|
| 1 Headless | `mcp-coder implement`, `create-plan`, `fix-ci`, … | Tier 2 list | — (no one to ask → denied) | Bash (except grants), built-in Read/Write/Edit, other MCP servers |
| 2 Interactive | your Claude session | see Tier 2 allow-list below | everything else, incl. all `git_*` writes and GitHub writes; native writes to `.mcp.json`, `.claude/` (built-in) | — (no deny rules); MCP writes to `.mcp-file-access` read-only files |
| 3 Skill / agent | `/skill`, `.claude/agents/*` | Tier 2 + its own extras (§4) | rest | — |
| 4 Special mode | "edit all issues per plan" | Tier 2 + one tool group, for one turn | rest | — |

**Tier 2 allow-list** (`.claude/settings.local.json`; per tool: [inventory](tool-inventory.md)):

| Group | Entries |
|---|---|
| mcp-workspace | file read/write tools, reference tools, `git` (read-only), `get_base_branch`, `check_branch_status`, GitHub read tools — no `git_*` / GitHub writes |
| mcp-tools-py | every tool, listed by name (no wildcard) |
| obsidian-wiki | every tool, incl. `obsidian_delete_note` |
| Skills | `Skill(<name>)` for most skills — no effect on user-only (`disable-model-invocation`) skills |
| Web | `WebFetch(domain:*)` — unrestricted ([#1434](https://github.com/MarcusJellinghaus/mcp_coder/issues/1434)) |
| Bash | `mcp-coder gh-tool checkout-issue-branch:*`, `tools/jenkins_builds.sh`, `jenkins_download_log.sh`, `jenkins_download_logs.sh` |

## 3. Mechanisms

Background: [how-it-works §5–§10](how-it-works.md#5-skills).

| Tier | Mechanism |
|---|---|
| 1 | Same settings as Tier 2 via `--settings` — one allow-list; a separate headless profile would need `deny` rules (`--settings` adds, never narrows: [how-it-works §2](how-it-works.md#2-settings-files)). Plus `--tools ToolSearch`, `--strict-mcp-config`, toolkit grants via `--allowedTools`. Rebase: generated settings — add only, narrow nothing |
| 2 | Tracked `.claude/settings.local.json`, allows only (committed `settings.json` layout: backlog [#1433](https://github.com/MarcusJellinghaus/mcp_coder/issues/1433)). `git_*` writes not allowed (ask) — headless runs get the same file, and there Python does all git writes. No `deny` rules: protected files rest on git review, Claude Code's built-in protection (`.mcp.json`, `.claude/` prompt) and `.mcp-file-access` (MCP refuses); gap: §3.1. `defaultMode: acceptEdits` comes from the user file |
| 3 skill | `allowed-tools` (turn-scoped) + `disable-model-invocation` on every skill with write extras |
| 3 agent | Agent frontmatter `hooks:` `PreToolUse` (runs only for that agent) — inline one-liner returning `allow` for its extras. The only documented per-agent grant under `acceptEdits` (agent `permissionMode` is ignored there). Not run in untrusted folders or under `-p` ([how-it-works §6](how-it-works.md#6-subagents)) |
| 4 | User-only skill (e.g. `/issue_bulk_edit`) with `allowed-tools: github_issue_*` — expires on next message; added when a real need appears. No TTL hook |

### 3.1 Accepted gaps

| Tier | Gap | Follow-up |
|---|---|---|
| 1 | non-rebase commands get the full interactive `settings.local.json` (+ user allows) — one allow-list for both | headless narrowing: [#1434](https://github.com/MarcusJellinghaus/mcp_coder/issues/1434) |
| 2 | no deny rules: native writes to `.mcp-file-access`, `.mcp.linux.json`, `.mcp.macos.json` run unprompted under `acceptEdits`; caught by git review | CI warning: [`check-sensitive-files`](../quality-and-security-checks.md#repo-hygiene); layout: [#1433](https://github.com/MarcusJellinghaus/mcp_coder/issues/1433) |
| 3 skill | grant ends at the user's reply; does not reach subagents | inherent |
| 3 agent | no per-agent write limits (needs a path-parsing hook); agent files are MCP-writable → an agent with file write tools can edit another agent's hook | [#1434](https://github.com/MarcusJellinghaus/mcp_coder/issues/1434) |
| 4 | not built — one-turn skill when a need appears | — |

## 4. Skill / agent extras

Skills: each skill's `allowed-tools` frontmatter; every skill with write extras is user-only (`disable-model-invocation`). Agents: [agent-permissions.md](../agent-permissions.md#agents-in-this-repo).
