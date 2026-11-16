# How Claude permissions work

Part 1 of 3 · [Tool inventory](tool-inventory.md) · [Design concept](design-concept.md)

Generic Claude Code behaviour. Sources: [permissions](https://code.claude.com/docs/en/permissions.md), [permission-modes](https://code.claude.com/docs/en/permission-modes.md), [settings](https://code.claude.com/docs/en/settings.md), [sub-agents](https://code.claude.com/docs/en/sub-agents.md), [skills](https://code.claude.com/docs/en/skills.md), [hooks](https://code.claude.com/docs/en/hooks.md), [claude-directory](https://code.claude.com/docs/en/claude-directory.md). Unverified points are marked.

**Baseline:** Claude Code 2.1.317 · docs read 2026-11-14 (pages carry no version). Re-check on upgrade.
**Tested** = tried 2026-11-16 on Windows, parent session in `acceptEdits`. **Docs** = documented, not tested.

## 1. Claude objects

`~` = user scope; `CLAUDE_CONFIG_DIR` relocates it.

| Object | Project | User | Auto-loaded | Enforces? |
|---|---|---|---|---|
| CLAUDE.md | `./CLAUDE.md`, `.claude/CLAUDE.md` | `~/.claude/CLAUDE.md` | yes | no — prose |
| CLAUDE.local.md | root (personal) | — | yes | no |
| Rules | `.claude/rules/*.md` | `~/.claude/rules/*.md` | yes; `paths:` → on demand | no |
| Settings | `.claude/settings.json`, `.claude/settings.local.json` | `~/.claude/settings.json` | yes | **yes** — allow/ask/deny, mode, hooks |
| Managed settings / CLAUDE.md | system path (Win: `C:\Program Files\ClaudeCode\`) | — | yes | **yes** |
| MCP servers | `.mcp.json` | `~/.claude.json` | yes | yes — which tools exist |
| Skills | `.claude/skills/<n>/SKILL.md` | `~/.claude/skills/` | description; body on invoke | partly (§5) |
| Commands | `.claude/commands/*.md` | `~/.claude/commands/` | as skills | partly |
| Agents | `.claude/agents/*.md` | `~/.claude/agents/` | on launch | partly (§6) |
| Hooks | `hooks` key in settings | same | per event | **yes** (§7) |
| Output styles | `.claude/output-styles/` | `~/.claude/output-styles/` | if selected | no |
| Workflows | `.claude/workflows/*.js` | `~/.claude/workflows/` | on run | no |
| Plugins | — | `~/.claude/plugins/` + `enabledPlugins` | if enabled | via their hooks/agents |
| Auto memory | — | `~/.claude/projects/<p>/memory/` | yes | no |
| Keybindings, themes, status line | — | `~/.claude/` | yes | no |
| `.worktreeinclude` | root | — | on worktree | no |
| `.claude/knowledge_base/` | mcp-coder convention | — | **no** — only when a skill names the path | no |

## 2. Settings files

| # | Level | Location | Scope |
|---|---|---|---|
| 1 | Managed policy | system path (Win: `C:\Program Files\ClaudeCode\managed-settings.json` — path unverified) | machine, admin-owned |
| 2 | CLI flags | `--settings <file>`, `--allowedTools`, `--disallowedTools`, `--permission-mode` | one session |
| 3 | Project local | `.claude/settings.local.json` | personal; Claude Code adds it to the global git excludes on first write |
| 4 | Project shared | `.claude/settings.json` | team, committed |
| 5 | User | `~/.claude/settings.json` | every repo on the machine |

Related, not a settings level: `~/.claude.json` (user/local MCP servers, UI state, folder trust).

**Combining** — two different mechanisms:

| Key type | Conflict resolved by | Example |
|---|---|---|
| Scalars (`defaultMode`, `model`, `enabledMcpjsonServers`) | **level** — highest file that sets it wins | user `acceptEdits` + project `default` → `default` |
| `env` | level, per variable | user `A=1, B=2` + project `B=3` → `A=1, B=3` |
| Lists (`permissions.allow` / `ask` / `deny`) | **merged** into one pool; conflicts settled by rule type (§4), **not** by level | user allow `Bash(git *)` + project deny `Bash(git push *)` → push denied |
| `defaultMode: auto` / `bypassPermissions` | ignored from project / local files | project `bypassPermissions` → no effect |

Allow rules from a committed project file (and a tracked `settings.local.json`) wait for folder trust; `deny` / `ask` apply immediately.

| Loading rule | Detail |
|---|---|
| Project files | read from the cwd only, no walk-up → a session started in a subfolder loads no `<repo>/.claude/settings*.json` (docs) |
| `--settings <file>` | adds to the cwd and user settings, does not replace them → a generated settings file narrows nothing; narrowing needs `deny` (analytical, from the merge rules) |

## 3. Permission modes

Set via `--permission-mode`, `permissions.defaultMode`, `Shift+Tab` (cycle excludes `dontAsk`). Fixed set — no custom modes (§10).

| Mode | Prompts for | Notes |
|---|---|---|
| `default` (`manual`) | first use of each non-read tool | reads in cwd free |
| `acceptEdits` | non-edit tools | auto-accepts edits + `mkdir/touch/mv/cp` in cwd |
| `plan` | — | read-only; no source edits |
| `auto` | nothing routine | background classifier vets actions |
| `dontAsk` | never — **denies** instead | allow-listed tools still run |
| `bypassPermissions` | ask rules, `rm`/`rmdir` on critical paths, interactive tools | **deny rules still block**; `.git` / `.claude` writes allowed |

## 4. Rule evaluation

Per tool call, against the merged pool (§2), first match wins:

| Step | Matching rule | Result |
|---|---|---|
| 1 | any `deny` | **blocked** — every mode, also subagents, also `bypassPermissions` |
| 2 | any `ask` | **prompt** — even if an `allow` also matches |
| 3 | any `allow` | **runs** without prompt |
| 4 | none | **mode decides** (§3): prompt (`default`), auto-accept edits (`acceptEdits`), deny (`dontAsk`, `-p`), run (`bypassPermissions`) |

| Consequence | Detail |
|---|---|
| Level is irrelevant for rules | user deny blocks project allow, and vice versa |
| Specificity is irrelevant | deny `Bash(aws *)` blocks allow `Bash(aws s3 ls)` — no allow-exceptions to a deny |
| `allow` only fills gaps | it can turn step 4 into "runs", never override steps 1–2 |
| CLI flags | `--allowedTools` adds allows (step 3), `--disallowedTools` adds denies (step 1); neither beats a managed deny |
| Hooks | a `PreToolUse` `allow` cannot override a matching deny / ask rule (§7) |
| "Don't ask again" at a prompt | writes a **permanent** `allow` to `settings.local.json` |

**Deny rules on file paths** (docs; live test: an `Edit(/…)` deny refused native `Write`):

| Aspect | Behaviour |
|---|---|
| Matching rule | only `Edit(path)` matches file writes — covers `Write`, `NotebookEdit`, `MultiEdit`; `Write(path)` matches nothing |
| Path | `/path` anchors at the primary working directory; forward slashes on Windows |
| Bash | covers recognised file commands (`cat`, `sed`, `tee`, redirections); not `cp` / `mv` / `Set-Content` (not documented) |
| Other clients | Copilot and iCoder don't apply them |

## 5. Skills

| Field | Effect |
|---|---|
| `allowed-tools` | pre-approval for the invoking turn — **not a restriction**; clears at next user message |
| `disallowed-tools` | removes tools while the skill is active |
| `disable-model-invocation: true` | user `/name` only — also blocks subagents |
| `user-invocable: false` | model only, hidden from `/` |
| `context: fork` + `agent` | runs in a subagent (no conversation history) |

`allowed-tools` grant does not reach spawned subagents (read from the Claude Code 2.1.227 bundle, not re-checked on 2.1.317; see [agent-permissions.md](../agent-permissions.md)).

## 6. Subagents

**Effective mode**

| Parent mode | Subagent mode |
|---|---|
| `bypassPermissions`, `acceptEdits`, `auto` | **parent's** — frontmatter ignored (docs) |
| `plan` | `plan` |
| `default`, `dontAsk` | frontmatter `permissionMode` (unset → parent's; docs: `bypassPermissions` "keeps the parent's mode") |

| Field | Effect |
|---|---|
| `tools` | allowlist; omitted → inherit all |
| `disallowedTools` | applied first; a specifier (`Bash(git push *)`) removes the whole tool |
| Own allow list | none in frontmatter |
| Parent `allow` rules | inherited by built-in subagents and custom agents (custom: tested) |
| Frontmatter `hooks:` `PreToolUse` | fire only for that agent; `allow` runs a non-allow-listed tool (`git_branch`, `github_issue_set_status`) with no prompt and no bypass; exit 2 + stderr blocks, the reason reaches the agent (tested) |
| Hook command | inline one-liner works without a script and without a `shell:` key (Git Bash); a script hook `"${CLAUDE_PROJECT_DIR}/.venv/Scripts/python.exe" "<script>"` works too (tested). YAML: [agent-permissions.md](../agent-permissions.md#the-allow-hook) |
| Hooks not run | **frontmatter hooks are skipped in untrusted folders and under `-p`** (docs) → the hook's tools prompt (interactive) or are denied (`-p`) |
| `skills:` | preloads model-invocable skills' text, not their tools — `tools:` must list them; a user-only skill is silently not preloaded (tested) |
| Agent file changes | new file picked up mid-session after 0.5–2 min; edits only after a restart (tested) |
| Caller restriction | none — any session can launch any agent |

## 7. Hooks (`PreToolUse`)

| Aspect | Behaviour |
|---|---|
| When | before the permission check, every tool except `EndConversation` |
| Block | exit 2 or `permissionDecision: "deny"` |
| Allow | `permissionDecision: "allow"` skips the prompt — cannot beat `deny` / `ask` rules |
| Input | `agent_id`, `agent_type`, `permission_mode` → can scope per agent (tested) |
| Under `bypassPermissions` | no exemption documented — firing unverified |

## 8. MCP rule syntax

| Rule | Matches |
|---|---|
| `mcp__<server>__<tool>` | one tool |
| `mcp__<server>`, `mcp__<server>__*` | all tools of a server |
| `mcp__*` | deny only — all MCP tools (skipped as allow) |
| `mcp__…(<specifier>)` | ignored in settings |

Names must match the `.mcp.json` server key exactly.

## 9. Headless (`claude -p`)

| Aspect | Behaviour |
|---|---|
| Unmatched tool needing approval | denied (no prompt) |
| Default mode | `default` since v2.1.302 when nothing sets one |
| Explicit refusal | `--permission-prompts none`, `permissions.denyInsteadOfPrompting` (user/managed) |
| Custom approver | `PermissionRequest` hook or `--permission-prompt-tool` |
| Denials | `permission_denied` events in `stream-json` |

## 10. Custom modes — substitutes

| Mechanism | Acts like | Scope |
|---|---|---|
| Settings profile + `--settings` | named mode | session |
| Agent `tools` / `disallowedTools` / `permissionMode` | mode inside an agent | agent (parent may override) |
| Skill `allowed-tools` / `disallowed-tools` | temporary mode | one turn |
| `PreToolUse` hook | programmable mode | every call |
| `PermissionRequest` hook / `--permission-prompt-tool` | custom approver | prompting calls |
