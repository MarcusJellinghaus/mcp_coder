# Claude Code permissions — implementation

Part 4 of 4 · [How it works](how-it-works.md) · [Tool inventory](tool-inventory.md) · [Design concept](design-concept.md)

Refs: `§` / `F#` = this file; `inv §` = [tool inventory](tool-inventory.md); `concept §` = [design concept](design-concept.md).

## 1. Current state

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

### 1.5 Findings

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

## 2. Future state

### 2.1 Settings layout

Implements concept P2.

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

### 2.2 Tier gaps

Mechanisms: [concept §3](design-concept.md#3-mechanisms).

| Tier | Today | Gap | Changes |
|---|---|---|---|
| 1 | partly | non-rebase commands pass the full interactive `settings.local.json` (+ user allows) | T14 |
| 2 | no | no committed `settings.json`; `acceptEdits` default | T1, T9 |
| 3 skill | yes | F5; grant dies on user reply; does not reach subagents | T8, T16 |
| 3 agent | no | bypass + Bash (F4, F9) | T7, T12, T13, T19 |
| 4 | no | — | Q8 |

## 3. Required changes

### 3.1 Decisions / config

| # | Item | Ref |
|---|---|---|
| T1 | Apply settings layout | §2.1 |
| T2 | Define `deny` baseline (e.g. `git push --force`, `rm -rf`, `.env` / `~/.ssh` reads) — user or project? | F1 |
| T3 | Restrict `WebFetch` to a domain list | F3 |
| T5 | Narrow `mcp-coder gh-tool:*` to `set-status`, `get-base-branch` | inv §6 |
| T7 | `PreToolUse` hook restricting agent Bash to git/gh | F4 |
| T8 | `pr_comment_triage`: fix tool names; decide `disable-model-invocation` | F5, F6 |
| T9 | Decide project `defaultMode` (`acceptEdits` vs `default`); interacts with F9 | F2, concept §3 |
| T10 | Decide obsidian `delete_note` / `rename_tag` pre-approval | inv §3 |
| T11 | Add `run_deptry_check`, `github_subissue_list` to allow-list (read-only) | inv §1, §2 |
| T12 | Test what mode `commit-pusher` actually runs in; fix [agent-permissions.md](../agent-permissions.md) | F9 |
| T13 | Evaluate `disallowedTools` (agents) / `disallowed-tools` (skills) as real restrictions | F4 |
| T14 | Evaluate `dontAsk` / `denyInsteadOfPrompting` for headless runs | §1.4, §2.2 |
| T15 | Drop all ✓ Bash patterns from allow-lists; drop dead script entries | inv §6 |
| T16 | Skills/agents: `gh issue create/edit/comment` → `github_issue_*` MCP tools | inv §6 |
| T17 | CLAUDE.md "Git operations": move `gh pr create`, `gh issue *` to MCP; keep only ✗ commands | inv §6 |
| T18 | Upgrade mcp-workspace to expose `workspace.git` write tools; then `git commit/push/branch` → MCP in skills, agents, CLAUDE.md | inv §6, F6 |
| T19 | After T18: re-evaluate whether `commit-pusher` (and its Bash + bypass) is still needed | F4, F9 |
| T20 | Remaining ✗: decide MCP tool vs narrow Bash — `set-status`, Jenkins scripts, rebase conflict commands | inv §6 |

T4, T6 merged into T1.

### 3.2 Follow-up tasks (code)

| # | Task | Where |
|---|---|---|
| FU1 | `mcp-coder verify`: new **CLAUDE SETTINGS** section. Warn (not fail) if user settings has `permissions.allow` / `ask` entries; list them. Honour `CLAUDE_CONFIG_DIR`. `deny` entries = info | `cli/commands/verify*.py` |
| FU2 | Same section: warn on stale `mcp__<server>__*` entries (server not in `.mcp.json`) and broad patterns (`Bash(*)`, `Bash(find:*)`, `WebFetch(domain:*)`) at any level | `cli/commands/verify*.py` |
| FU3 | Copilot provider reads allows only from `settings.local.json` → also read / merge `settings.json` | `llm/providers/copilot/copilot_cli.py` (`_read_settings_allow`) |
| FU4 | Settings auto-detect prefers `settings.local.json`; confirm headless runs still get `settings.json` allows (Claude cwd merge) | `cli/utils.py` |
| FU5 | `mcp-coder init`: deploy `.claude/settings.json` template; gitignore `settings.local.json` | `cli/commands/init.py` |
| FU6 | Update [claude-code.md](../claude-code.md#enhanced-claude-permissions) to the new layout | docs |
| FU7 | Propagate to sibling repos | Chore Propagation process |

## 4. Open questions (facts)

Design questions: [concept §5](design-concept.md#5-open-design-questions).

| # | Question |
|---|---|
| Q1 | Where are `obsidian-wiki` and `claude-artifacts` configured (`~/.claude.json`? connector despite `ENABLE_CLAUDEAI_MCP_SERVERS=false`)? |
| Q5 | Do custom agents inherit the parent's `allow` rules? (docs: built-ins only) |
| Q6 | Do `PreToolUse` hooks fire under `bypassPermissions`? |
| Q7 | Any plugins enabled (`enabledPlugins`)? |
| Q9 | Tier 1: do `create-pr` / `review-*` need GitHub or git writes from the LLM? |
