# Claude Code permissions — TODOs

Part 3 of 3 · [How it works](how-it-works.md) · [Design](design.md)

Refs (`§`, `F#`) point to [design.md](design.md).

## 1. Decisions / changes

| # | Item | Ref |
|---|---|---|
| T1 | Apply settings layout | §4.1 |
| T2 | Define `deny` baseline (e.g. `git push --force`, `rm -rf`, `.env` / `~/.ssh` reads) — user or project? | F1 |
| T3 | Restrict `WebFetch` to a domain list | F3 |
| T5 | Narrow `mcp-coder gh-tool:*` to `set-status`, `get-base-branch` | §2.6 |
| T7 | `PreToolUse` hook restricting agent Bash to git/gh | F4 |
| T8 | `pr_comment_triage`: fix tool names; decide `disable-model-invocation` | F5, F6 |
| T9 | Decide project `defaultMode` (`acceptEdits` vs `default`); interacts with F9 | F2, §4.2 |
| T10 | Decide obsidian `delete_note` / `rename_tag` pre-approval | §2.3 |
| T11 | Add `run_deptry_check`, `github_subissue_list` to allow-list (read-only) | §2.1, §2.2 |
| T12 | Test what mode `commit-pusher` actually runs in; fix [agent-permissions.md](../agent-permissions.md) | F9 |
| T13 | Evaluate `disallowedTools` (agents) / `disallowed-tools` (skills) as real restrictions | F4 |
| T14 | Evaluate `dontAsk` / `denyInsteadOfPrompting` for headless runs | §1.4, §4.2 |
| T15 | Drop all ✓ Bash patterns from allow-lists; drop dead script entries | §2.6 |
| T16 | Skills/agents: `gh issue create/edit/comment` → `github_issue_*` MCP tools | §2.6 |
| T17 | CLAUDE.md "Git operations": move `gh pr create`, `gh issue *` to MCP; keep only ✗ commands | §2.6 |
| T18 | Upgrade mcp-workspace to expose `workspace.git` write tools; then `git commit/push/branch` → MCP in skills, agents, CLAUDE.md | §2.6, F6 |
| T19 | After T18: re-evaluate whether `commit-pusher` (and its Bash + bypass) is still needed | F4, F9 |
| T20 | Remaining ✗: decide MCP tool vs narrow Bash — `set-status`, Jenkins scripts, rebase conflict commands | §2.6 |

T4, T6 merged into T1.

## 2. Follow-up tasks (code)

| # | Task | Where |
|---|---|---|
| FU1 | `mcp-coder verify`: new **CLAUDE SETTINGS** section. Warn (not fail) if user settings has `permissions.allow` / `ask` entries; list them. Honour `CLAUDE_CONFIG_DIR`. `deny` entries = info | `cli/commands/verify*.py` |
| FU2 | Same section: warn on stale `mcp__<server>__*` entries (server not in `.mcp.json`) and broad patterns (`Bash(*)`, `Bash(find:*)`, `WebFetch(domain:*)`) at any level | `cli/commands/verify*.py` |
| FU3 | Copilot provider reads allows only from `settings.local.json` → also read / merge `settings.json` | `llm/providers/copilot/copilot_cli.py` (`_read_settings_allow`) |
| FU4 | Settings auto-detect prefers `settings.local.json`; confirm headless runs still get `settings.json` allows (Claude cwd merge) | `cli/utils.py` |
| FU5 | `mcp-coder init`: deploy `.claude/settings.json` template; gitignore `settings.local.json` | `cli/commands/init.py` |
| FU6 | Update [claude-code.md](../claude-code.md#enhanced-claude-permissions) to the new layout | docs |
| FU7 | Propagate to sibling repos | Chore Propagation process |

## 3. Open questions

| # | Question |
|---|---|
| Q1 | Where are `obsidian-wiki` and `claude-artifacts` configured (`~/.claude.json`? connector despite `ENABLE_CLAUDEAI_MCP_SERVERS=false`)? |
| Q2 | Should a skill's pre-approved GitHub writes be allowed for model-invoked skills at all? |
| Q3 | Threat model: prompt injection via issues / PR comments / web, model mistakes, or both? |
| Q4 | Headless and interactive: one allow-list or separate? (§4.2 proposes separate) |
| Q5 | Do custom agents inherit the parent's `allow` rules? (docs: built-ins only) |
| Q6 | Do `PreToolUse` hooks fire under `bypassPermissions`? |
| Q7 | Any plugins enabled (`enabledPlugins`)? |
| Q8 | Tier 4: one-turn skill (A) enough, or time-boxed hook (B)? |
| Q9 | Tier 1: do `create-pr` / `review-*` need GitHub or git writes from the LLM? |
