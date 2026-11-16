# Claude Code permissions — implementation

Part 4 of 5 · [How it works](how-it-works.md) · [Tool inventory](tool-inventory.md) · [Design concept](design-concept.md) · [Skills and agents](skills-agents.md)

Refs: `§` / `F#` = this file; `inv §` = [tool inventory](tool-inventory.md); `concept §` = [design concept](design-concept.md).

## 1. Current state

### 1.1 Settings files

Levels and combining rules: [how-it-works §2](how-it-works.md#2-settings-files).

| # | Level | In use | Content today |
|---|---|---|---|
| 1 | Managed policy | no | — |
| 2 | CLI flags | headless only | mcp-coder passes `--settings settings.local.json`, `--allowedTools` Bash grants |
| 3 | `.claude/settings.local.json` | yes — **tracked** here as template | ~80 allows, MCP enablement; no `deny` / `ask` |
| 4 | `.claude/settings.json` | yes — committed | `permissions.deny` only: native `Edit` on the 6 protected files (T2) |
| 5 | `~/.claude/settings.json` | yes | `env`, model, UI, `defaultMode: acceptEdits`, ~45 allows (many stale), `WebFetch(domain:*)`, `Bash(find:*)` |

**Effective today**

| Key | Result |
|---|---|
| `permissions.allow` | user ~45 + local ~80 — all active |
| `permissions.deny` | project: 6 `Edit(/…)` rules (T2) |
| `permissions.ask` | none |
| `defaultMode` | `acceptEdits` (only user sets it) |
| `env` | user's 5 vars |
| `enabledMcpjsonServers`, `enableAllProjectMcpServers` | local |
| `model`, `tui`, … | user |
| Headless `--settings` | `settings.local.json` read twice (CLI + cwd discovery) — same content; `settings.json` deny merged via cwd |

### 1.2 Agents (snapshot 2026-11-15, before issues 1–4)

| Agent | `tools` | `permissionMode` | Launched by |
|---|---|---|---|
| `commit-pusher` | git (R), 🆕 git_commit, 🆕 git_push, run_format_code, read_file | `bypassPermissions` | review/plan supervisors |
| `issue-updater` | issue_view, issue_edit, save/edit/delete file, delete_directory, read_file | `bypassPermissions` | issue_analyse_supervisor |
| `issue-approver` | **Bash**, issue_view, issue_comment, read_file, git (R), get_reference_projects | `bypassPermissions` | issue_analyse_supervisor |

🆕 = not in the installed server ([inventory §1](tool-inventory.md#1-mcp-workspace)) → `commit-pusher` cannot commit today. Intent of bypass: write tools unprompted. Parent `acceptEdits` (user default) overrides it → F9.

### 1.3 Skills (snapshot 2026-11-15, before issues 1–4)

`UI` = `disable-model-invocation: true`. Pre-approvals listed only where they exceed the allow-list.

| Skill | UI | Extra pre-approvals |
|---|---|---|
| check_branch_status | – | – |
| commit_push | ✓ | 🆕 `git_commit`, `git_push` |
| discuss | ✓ | – |
| implement_direct | ✓ | `Bash(mcp-coder gh-tool *)` |
| implementation_approve | ✓ | `Bash(… set-status *)` |
| implementation_finalise | ✓ | – |
| implementation_needs_rework | ✓ | `Bash(… set-status *)` |
| implementation_new_tasks | ✓ | – |
| implementation_review | – | – |
| implementation_review_supervisor | ✓ | – |
| issue_analyse | – | – |
| issue_analyse_supervisor | ✓ | – |
| issue_approve | ✓ | `Bash(… set-status *)`, `github_issue_comment` |
| issue_create | ✓ | `github_issue_create` |
| issue_requirements | ✓ | – |
| issue_update | ✓ | `github_issue_edit` |
| plan_approve | ✓ | `Bash(… set-status *)` |
| plan_review | – | – |
| plan_review_supervisor | ✓ | – |
| plan_update | – | – |
| pr_comment_triage | **–** | `github_review_comment_reply`, `github_review_thread_resolve`, `github_issue_comment`, 🆕 `git_commit`, `git_push`, `Bash(… set-status *)` |
| rebase | ✓ | 🆕 `git_commit`, `git_push`, `git_push_force`; `Bash(git rebase/add/rm/checkout --ours/--theirs/remote get-url/restore/stash *)`, `Bash(git push --force-with-lease *)` |

`… set-status` = `mcp-coder gh-tool set-status`; 🆕 = not in the installed server.

Knowledge base readers: `implementation_review_supervisor`, `issue_analyse_supervisor`, `plan_review_supervisor`, `plan_review`.

### 1.4 Headless workflows (`mcp-coder implement`, `rebase`, `fix-ci`, …)

| Control | Value |
|---|---|
| Built-in tools | `--tools ToolSearch` (+ `Bash` only if grants) — Read/Write/Edit/Bash off |
| MCP servers | `--mcp-config <file> --strict-mcp-config` |
| Settings | `--settings <file>`; auto-detect `settings.local.json` → `settings.json`; Claude also merges repo files via cwd — incl. the `settings.json` deny |
| Bash | exact grants via `--allowedTools` from toolkit `llm_permissions` |
| Rebase | generated least-privilege settings (`workflows/rebase_permissions.py`); Python does all git writes + push |

### 1.5 Findings

| # | Finding |
|---|---|
| F1 | No `ask` rules; hooks only in agent frontmatter (allow hooks, T26); `deny` only in project `settings.json` (protected files, T2) |
| F2 | User `defaultMode: acceptEdits` applies to every repo |
| F3 | `WebFetch(domain:*)` = unrestricted outbound channel |
| F4 | ✅ fixed: `issue-approver` had `bypassPermissions` + unrestricted Bash → no Bash ([issue 2](issues/issue_2_skill_text.md)), allow hook instead of bypass ([issue 3](issues/issue_3_agents.md)) |
| F5 | ✅ resolved: `pr_comment_triage` is user-only (T8, T25). Was model-invocable and pre-approved GitHub and git writes |
| F6 | ✅ resolved (T18): git write tools installed and used by CLAUDE.md, `commit_push`, `rebase`, `pr_comment_triage`, `commit-pusher`. Was missing from the installed server (since #1421) → Bash fallback with prompts; `commit-pusher` could not commit |
| F7 | User allow-list holds stale server names (`mcp__code-checker__*`, `mcp__filesystem__*`) |
| F8 | `settings.local.json` is tracked here (template) — "local" file acting as shared config |
| F9 | ✅ resolved ([issue 3](issues/issue_3_agents.md): no agent sets `permissionMode`). Agents' `bypassPermissions` was ineffective under the user's `acceptEdits` — documented, not tested: docs (sub-agents) say the agent's `permissionMode` is ignored when the parent runs `acceptEdits`, `auto` or `bypassPermissions` ([how-it-works §6](how-it-works.md#6-subagents)) |
| F10 | ✅ moot ([issue 3](issues/issue_3_agents.md): no `bypassPermissions`). Under real `bypassPermissions`, writes to `.git` / `.claude` are allowed — agent could rewrite skills; the T2 deny still binds for the 6 protected files — deny rules block in every mode, including `bypassPermissions` (Claude Code docs: permission-modes). Remaining: agent files are MCP-writable, so an agent with file write tools can still edit another agent's hook (no path limits yet) |
| F11 | `--settings` adds to the cwd and user settings, it does not replace them → generated settings (`rebase_settings`) narrow nothing; narrowing needs `deny` (analytical, from the merge rules) |
| F12 | `obsidian-wiki` (user scope, `~/.claude.json`) starts via `npx -y obsidian-mcp` — unpinned, fetches the latest npm version each start |
| F13 | `claude-artifacts` is in no local file (not `~/.claude.json`, user/project settings, `.mcp.json`) and loads despite `ENABLE_CLAUDEAI_MCP_SERVERS=false`: ~39 tools, ~20k tokens per session, unused here |

## 2. Future state

### 2.1 Settings layout

Implements concept P2.

| File | Holds | Not |
|---|---|---|
| `~/.claude/settings.json` | `env` (MCP venv vars — `.mcp.json` needs them), `model`, `modelSettings`, UI, `defaultMode: acceptEdits` (T9) | `allow`, `ask` |
| `.claude/settings.json` (committed) | `allow` / `ask`, `deny` (T2), `enabledMcpjsonServers` | personal extras |
| `.claude/settings.local.json` (gitignored) | empty / absent — personal experiments only | baseline permissions |

| Effect | Detail |
|---|---|
| Single review point | permissions per repo in git, diffable, deployable by `mcp-coder init` |
| Outside a repo | no allows → everything prompts (intended) |
| Fixes | F7, F8, user-level `find:*` / `python -m pytest:*` |

Migration: diff each repo's `settings.local.json` against user `allow` before deleting user entries (mcp-workspace, mcp-tools-py, AutoRunner each have their own local file).

### 2.2 Tier gaps

Mechanisms: [concept §3](design-concept.md#3-mechanisms).

| Tier | Today | Gap | Changes |
|---|---|---|---|
| 1 | partly | non-rebase commands pass the full interactive `settings.local.json` (+ user allows) — accepted for now (Q4) | T14 |
| 2 | partly | deny-only `settings.json` blocks native writes to the protected files (T2 ✅); unrecognised Bash/PowerShell writes not covered; allows layout open | T1 |
| 3 skill | yes | grant dies on user reply; does not reach subagents | T8, T16 |
| 3 agent | yes ([issue 3](issues/issue_3_agents.md)) | ✅ inline allow hooks replace bypass; dedicated engineer agents, no Bash. Open: per-agent write limits (hook with path parsing) | T19, T24, T26 |
| 4 | no | — (one-turn skill when needed, Q8) | — |

## 3. Required changes

### 3.1 Decisions / config

| # | Item | Ref |
|---|---|---|
| T1 | ◐ (deny-only `settings.json` done in [issue 1](issues/issue_1_settings_json.md); layout and user-file parts open) Apply settings layout | §2.1 |
| T2 | ✅ done ([issue 1](issues/issue_1_settings_json.md)): project `settings.json` holds only `permissions.deny` — `Edit(/…)` on `.mcp.json`, `.mcp.linux.json`, `.mcp.macos.json`, `.mcp-file-access`, `.claude/settings.json`, `.claude/settings.local.json`. The only grounded rule (`acceptEdits` stays, `.mcp-file-access` doesn't bind native tools); no generic baseline. Syntax (Claude Code docs: permissions / settings): only `Edit(path)` deny rules match file writes — `Edit` covers `Write`, `NotebookEdit`, `MultiEdit`; `Write(path)` with a path silently matches nothing. `/path` anchors at the session's primary working directory; Windows paths normalised to POSIX before matching → forward slashes; case sensitivity on Windows undocumented. Deny/ask apply before the trust dialog, project allows wait for trust. Built-in protection already prompts for `.mcp.json` and `.claude/` (default / `acceptEdits`) — the deny turns that into a refusal and adds the other three files. Known limits: ① session started in a subfolder loads no `<repo>/.claude/settings*.json` (no parent fallback) → start at the repo root ② deny covers Bash file commands Claude Code recognises (`cat`, `sed`, `tee`, redirections), not arbitrary subprocesses; `cp`, `mv`, `Set-Content` undocumented ③ Copilot, iCoder don't read it ④ `acceptEdits` auto-approves `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` in the working directory; protected paths (`.claude/`, `.mcp.json`) still prompt, but `.mcp-file-access`, `.mcp.linux.json`, `.mcp.macos.json` are not protected paths — whether the `Edit` deny checks `cp`/`mv` targets is undocumented, so `cp`/`mv` onto them may run unprompted (`sed` is covered — recognised command). Live test 2026-11-16 (root session, after restart): native `Write` on `.mcp-file-access` and `.mcp.json` refused without a prompt; `/permissions` lists all 6 rules, no warning. Open (by hand, after restart): "don't ask again" probe | F1 |
| T3 | Restrict `WebFetch` to a domain list | F3 |
| T5 | ✅ (2026-11-16, by hand) `settings.local.json`: `Bash(mcp-coder gh-tool:*)` → `Bash(mcp-coder gh-tool checkout-issue-branch:*)` — the only subcommand a skill still runs (`implement_direct`); `set-status` → `github_issue_set_status` (T21), `get-base-branch` → `get_base_branch`. Checked by `tests/docs/test_claude_settings.py` | inv §6 |
| T7 | ~~`PreToolUse` hook restricting `issue-approver` Bash~~ — obsolete: `issue-approver` loses Bash (T21, T26) | F4 |
| T8 | ✅ decided: `pr_comment_triage` gets `disable-model-invocation: true` → done in T25 | F5 |
| T9 | ✅ decided: keep user `defaultMode: acceptEdits`; protected files covered by T2 | F2, concept §3 |
| T10 | ✅ decided: no change — all obsidian tools stay pre-approved | inv §3 |
| T11 | ✅ done ([issue 1](issues/issue_1_settings_json.md)): `run_deptry_check`, `github_subissue_list` added to `settings.local.json` (read-only) | inv §1, §2 |
| T12 | ✅ moot: no agent sets `permissionMode` any more ([issue 3](issues/issue_3_agents.md)); [agent-permissions.md](../agent-permissions.md) rewritten | F9 |
| T13 | ✅ moot for this goal: per the docs there is no per-agent allow field — `disallowedTools` only removes tools, which explicit `tools:` already does; the grant is the frontmatter hook (T26) | F4 |
| T14 | Evaluate `dontAsk` / `denyInsteadOfPrompting` for headless runs | §1.4, §2.2 |
| T15 | ◐ (this repo's `settings.local.json`: `start …html` and `.bat` Jenkins entries dropped in [issue 1](issues/issue_1_settings_json.md); user-file ✓ patterns open) Drop all ✓ Bash patterns from allow-lists; drop dead script entries | inv §6 |
| T16 | ✅ Skills/agents: `gh issue *` → `github_issue_*` (#1406) | inv §6 |
| T17 | ✅ CLAUDE.md: `gh` → MCP (#1406), git writes → MCP (#1421) | inv §6 |
| T18 | ✅ (2026-11-15; `git_*` writes: ask — not in the shared allow-list, also reaches headless runs where Python does all git writes; agents/skills get them via hooks / `allowed-tools`) Upgrade mcp-workspace in the tool env (6 🆕 tools): ① close Claude sessions + Jenkins jobs using `C:\Jenkins\environments\mcp-coder-dev\.venv` (Windows locks `mcp-workspace.exe`) ② `uv pip install --python <env>\Scripts\python.exe --upgrade "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"` ③ `mcp-workspace.exe --version` ④ restart Claude, check the 🆕 tools are listed (main also brings `.mcp-file-access`, needed for FU9/FU10) | inv §1, F6 |
| T19 | ✅ decided: keep `commit-pusher`, drop its bypass (T26) | F9 |
| T20 | Remaining ✗: decide MCP tool vs narrow Bash — Jenkins scripts, rebase conflict commands | inv §6 |
| T21 | ✅ ([issue 2](issues/issue_2_skill_text.md)) After T18: `mcp-coder gh-tool set-status` → `github_issue_set_status` in skills, `issue-approver`, CLAUDE.md; drop `issue-approver` Bash (makes T7 obsolete) | inv §6, F4 |
| T22 | ◐ (this repo's CLAUDE.md done in [issue 2](issues/issue_2_skill_text.md); FU7 propagation open) CLAUDE.md tool table: add the ✗ tools — `github_issue_set_status` (after T18; also rewrite "Status labels" and drop `set-status` from the approved Bash list), `github_subissue_list/add/remove`, `github_review_comment_reply`, `github_review_thread_resolve`, `run_deptry_check`, `search_library_files`. "Delete directory" row ✅ added. Propagate via FU7 | inv §1, §2 |
| T23 | ✅ Tested 2026-11-16 (probe agent, parent in `acceptEdits`, Windows): frontmatter `PreToolUse` hook `allow` runs a non-allow-listed tool (`git_branch`) with no prompt and no bypass; exit 2 + stderr blocks a write outside `.scratch/`, reason reaches the agent; hook fires only for that agent (input has `agent_type`, `agent_id`, `permission_mode`); Git Bash command `"${CLAUDE_PROJECT_DIR}/.venv/Scripts/python.exe" "<script>"` works; agent inherits the allow-list; `skills:` preloads a model-invocable skill but not its tools (`tools:` must list them); a user-only skill was not preloaded. New agent file picked up mid-session after 0.5–2 min; edits to it only after restart. Documented, not tested: frontmatter hooks are skipped in untrusted folders and under `-p`; agent `permissionMode` is ignored when the parent runs `acceptEdits` (confirms F9) | concept §1.1 R3, R4 |
| T24 | ✅ ([issue 3](issues/issue_3_agents.md)) New agent files `issue-analyst`, `plan-engineer`, `code-engineer` (explicit `tools:`, preloaded skills, no Bash / `Skill` / hook — all tools allow-listed); the three supervisors launch them. `rebaser` dropped (2026-11-16): `/rebase` stays a self-contained skill until mcp-workspace #263. Frontmatter checked by `tests/icoder/test_repo_agents.py` | [roster](skills-agents.md#target-agent-roster) |
| T25 | ✅ (skill text in [issue 2](issues/issue_2_skill_text.md); agent parts in [issue 3](issues/issue_3_agents.md)) Apply every "Skill text changes" row of skills-agents §2–§5 (incl. T21 status changes per R8, `pr_comment_triage` U-only, `implement_direct` narrow Bash, untrusted stops, dead `get-url` grant) | skills-agents |
| T26 | ✅ ([issue 3](issues/issue_3_agents.md)) `commit-pusher`, `issue-updater`, `issue-approver` — drop `bypassPermissions`, add an inline frontmatter allow hook (decided 2026-11-16: allow only, no write limits yet; docs show no other per-agent grant under `acceptEdits`); rewrite CLAUDE.md "Privileged agents"; update [agent-permissions.md](../agent-permissions.md) → [issue 3](issues/issue_3_agents.md). Probe 2026-11-16 (temporary agent, parent `acceptEdits`, Windows, no `shell:` key → Git Bash): `github_issue_set_status` ran with no prompt, twice. Working frontmatter: `hooks: PreToolUse: - matcher: "<extra tools, \|-separated>"  hooks: - type: command  command: "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\"}}'"` | concept §1.1 R4 |
| T27 | Upstream mcp-workspace: rebase tools (#263, comment posted); optional `checkout-issue-branch` tool → then `implement_direct` needs no Bash | skills-agents §4, §5 |
| T28 | By hand (user config): pin `obsidian-mcp@<version>` in `~/.claude.json`; `/mcp` → check source of `claude-artifacts`, disable if unused | F12, F13 |

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
| FU8 | `vscodeclaude`: pre-trust each new clone — set `projects["<clone-root>"].hasTrustDialogAccepted: true` in `~/.claude.json` before launch. Risks: running sessions also write that file (atomic write + re-read); skip when the issue author is untrusted (`_is_untrusted_body`). Alternative: worktrees of one trusted main checkout | `workflows/vscodeclaude/session_launch.py` / `workspace.py` |
| FU9 | ✅ (2026-11-15) Add `.mcp-file-access` to this repo with `read-only /.vscodeclaude_status.txt` → `issue_analyse`, `issue_analyse_supervisor`, `issue_approve`, `implement_direct` read the issue number directly via `read_file`, as their SKILL.md already says (today refused: gitignored; no skill change needed). Create by hand (MCP tools can't write the rules file). Also: `read-only` `/.mcp.json`, `/.mcp.linux.json`, `/.mcp.macos.json` (the last two added in [issue 1](issues/issue_1_settings_json.md)), `/.claude/settings.json`, `/.claude/settings.local.json` (MCP `edit_file` is allow-listed and skips Claude Code's own protection of these); `read-write /.scratch/` (prep for FU11) | repo root |
| FU10 | ✅ ([issue 4](issues/issue_4_init_mcp_file_access.md)) `mcp-coder init`: create `.mcp-file-access` if missing, else append the template rules it lacks — idempotent, like `update_gitignore`. Template (constant in `cli/commands/init_file_access.py`): `read-only` `/.vscodeclaude_status.txt`, `/.mcp.json`, `/.claude/settings.json`, `/.claude/settings.local.json`; `read-write /.scratch/` — no `.mcp.linux/macos.json` (gitignored in target repos, a rule would expose them). Invalid file left unchanged; then gitignores `.scratch/` (init only). Session-folder part **reversed**: session folders get the committed file via git; an untracked one would break checkouts of branches that track it | `cli/commands/init.py`, `cli/commands/init_file_access.py` |
| FU11 | ✅ ([issue 4](issues/issue_4_init_mcp_file_access.md)) `.scratch/` gitignored in this repo (writable via the FU9 rule, never committed). `verify` MCP edit smoke test honours `.mcp-file-access` (`get_file_access`, `validate_access_rules`; gitignore-only without support). CLAUDE.md `git_commit` note, Scratch probes, Jenkins bullet updated; CI `check_forbidden_folder .scratch` stays as a backstop. Needs mcp-workspace with `.mcp-file-access` everywhere (Jenkins, sibling repos — issue 4 task 0) | `cli/commands/verify.py`, `.gitignore`, CLAUDE.md |

### 3.3 Issues

Never filed on GitHub: analysed with the `issue_analyse_supervisor` loop, then implemented on branch `docs/claude-permissions-concept` by an implementer agent + a separate review agent per issue (2026-11-16).

| Issue | Covers | Analysis | Status | Open (manual) |
|---|---|---|---|---|
| [issue 1](issues/issue_1_settings_json.md) | deny-only `settings.json` (T2), `settings.local.json` cleanup (T11, T15 part) | 4 rounds | ✅ implemented `64b6e34`, live-tested | `Write` creating a protected file; "don't ask again" probe |
| [issue 2](issues/issue_2_skill_text.md) | status tool switch, untrusted stops, narrower Bash (T21, T22, T25 part) | 3 rounds | ✅ implemented `2515f2b` | live guard runs |
| [issue 3](issues/issue_3_agents.md) | 3 new agents, inline allow hooks, no bypass (T24, T26) | 2 rounds | ✅ implemented `3540718`; `commit-pusher` / `issue-approver` hooks live-tested | `issue-updater` run; one round per supervisor |
| [issue 4](issues/issue_4_init_mcp_file_access.md) | `init` writes `.mcp-file-access` and gitignores `.scratch/` in every repo; `verify` honours the rules (FU10, FU11) | 2 rounds | ✅ implemented `35e1f6c` | **task 0 before merge:** mcp-workspace ≥ f626cf8 on every Jenkins executor env |
| [issue 5](issues/issue_5_settings_layout.md) | allows to `settings.json`, untrack `settings.local.json` (T1, F8, FU3, FU5, FU6) | 1 round | **shelved** — `settings.local.json` stays shared | — |

## 4. Open questions (facts)

Design questions: [concept §5](design-concept.md#5-open-design-questions).

| # | Question |
|---|---|
| Q1 | ✅ `obsidian-wiki`: user scope, `~/.claude.json` (F12). `claude-artifacts`: in no local file — likely provided with Claude Code / the account (unverified, F13) |
| Q5 | ✅ Yes: every subagent inherits the parent's permission rules, and its mode unless `permissionMode` is set; skill `allowed-tools` carry-over not documented (docs: sub-agents) |
| Q6 | ✅ Closed, moot: R4 / T26 removed `bypassPermissions` everywhere ([issue 3](issues/issue_3_agents.md)) |
| Q7 | ✅ None (no `enabledPlugins`, `plugins/config.json` empty) |
| Q9 | ✅ No: Python commits (`commit_all_changes`) and creates the PR (`pr_manager.create_pull_request`) |
