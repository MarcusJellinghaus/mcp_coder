# chore(permissions): committed .claude/settings.json with protected-file deny

> **Reversed 2026-11-16:** the deny-only `.claude/settings.json` was removed — no deny rules ([implementation T2](../implementation.md#31-decisions--config)). The rest of this issue stands: the `.mcp-file-access` rules, the `settings.local.json` cleanup, and the stop-and-hand-off rule for protected files.

Add a committed `.claude/settings.json` that denies native writes to the protected config files, and clean dead and redundant entries out of `.claude/settings.local.json`. The settings layout itself (allows moving to `settings.json`, untracking `settings.local.json`) is **not** part of this issue.

**Manual / interactive issue — not for `mcp-coder implement`:** headless runs have native Write/Edit off, and `.mcp-file-access` makes both settings files and itself read-only for MCP tools. Once the deny is active, Claude's native `Edit`/`Write` and MCP tools can no longer change the protected files — edit them in an editor (also in later issues; the built-in `update-config` / `fewer-permission-prompts` skills are locked out too). Intended — headless runs (`mcp-coder rebase` / `fix-conflict` / `implement`) included. Side effect: in a rebase conflict inside a protected file Claude can still pick one side (`git checkout --ours/--theirs`, pre-approved in the `rebase` skill), but can't merge the content — that's an editor job.

## Dependencies / references

- **Read first:** `docs/repository-setup/claude-permissions/implementation.md` §3.1 T1, T2, T11, T15, T18; §1.5 F11
- Concept: `docs/repository-setup/claude-permissions/design-concept.md` §2 (Tier 2), §3
- Before issue 4: this repo's `.mcp-file-access` is extended here; issue 4's `init` template is a subset (no `.mcp.linux/macos.json`)
- Follow-up (separate issue): settings layout — allows to `settings.json`, untrack `settings.local.json`, Copilot (FU3), init (FU5), docs
- Not in scope: T3 (`WebFetch` domain list), T5 / `gh-tool` narrowing (issue 2 removes `set-status` first), T20 (Jenkins scripts — no Jenkins allow is added or changed beyond dropping `.bat`), user `~/.claude/settings.json` (cleaned by hand)

## Decisions

- `settings.json` holds only `permissions.deny` — deny wins over the allows in `settings.local.json` and the user file
- `settings.local.json` stays tracked; its allows stay; `resolve_claude_settings_path` keeps passing it via `--settings`
- `Bash(mcp-coder gh-tool:*)` stays until issue 2 has replaced `set-status`
- `git_*` write tools (`git_branch`, `git_branch_delete`, `git_commit`, `git_push`, `git_push_force`) stay out of every allow-list (T18) — already true in `settings.local.json`
- Exact tool names only, no server wildcards (`tools/mlflow/_source_transcripts.py::was_allowlisted` matches exact names; Copilot's `convert_settings_to_copilot_tools` passes entries through literally)
- Known limits — the deny covers Claude Code's native file tools and the Bash file commands it recognises (`cat`, `sed`, `tee`, redirections; Claude Code docs):
  - Arbitrary subprocesses are not covered; `cp`, `mv`, `Set-Content`, `Copy-Item`, `find -exec` are undocumented
  - `acceptEdits` auto-approves `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` in the working directory; protected paths (`.claude/`, `.mcp.json`) still prompt, but `.mcp-file-access`, `.mcp.linux.json`, `.mcp.macos.json` are not protected paths — whether the `Edit` deny checks `cp`/`mv` targets is undocumented, so `cp`/`mv` onto them may run unprompted (`sed` is covered — recognised command)
  - Sessions started in a subfolder don't load `<repo>/.claude/settings.json` (no parent fallback) — start at the repo root
  - Copilot (`--allow-all-tools`) doesn't read `.claude/settings.json`; iCoder's own layer reads `.icoder/` only
- On refusal Claude stops and hands off — it must not fall back to Bash/PowerShell writes (CLAUDE.md's "If no MCP equivalent exists, use Bash" would otherwise point there)
- `jenkins_classify_logs.sh` keeps prompting (not allow-listed; T20)

## Tasks

Order: step 1 before step 4 (the path form depends on it). Steps 2–4 are editor edits.

### 1. Verify deny syntax (throwaway `git init` repo outside this one, Windows)
- [x] `Write(path)` is a valid rule name; whether `Edit(...)` alone also blocks `Write` — `Write(path)` matches nothing; `Edit` covers `Write`, `NotebookEdit`, `MultiEdit` (docs)
- [x] What a `/path` rule resolves against (project root vs `.claude/`); fallback forms if needed (`//` absolute, `**/name`) — session's primary working directory (docs)
- [x] Session started in a subfolder: is `<root>/.claude/settings.json` loaded at all? If not: record as a known limit and correct `docs/repository-setup/claude-code.md` ("Pinning the settings file") and `docs/environments/environments.md` ("The Working Directory Selects the Agent's Rules") — not loaded; known limit, both docs corrected
- [ ] Case (`.MCP.json`) and backslash paths — backslashes normalised to POSIX (docs); case sensitivity on Windows undocumented, not tested
- [x] Under `acceptEdits`: does the deny stop `cp`/`mv`/`touch` and PowerShell writes to a protected file? Record the result as a known limit — recognised Bash file commands only; `cp`, `mv`, `Set-Content` undocumented → known limit (docs, not tested by hand). `acceptEdits` auto-approves `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` in the working directory; protected paths (`.claude/`, `.mcp.json`) still prompt, but `.mcp-file-access`, `.mcp.linux.json`, `.mcp.macos.json` are not protected paths — whether the `Edit` deny checks `cp`/`mv` targets is undocumented, so `cp`/`mv` onto them may run unprompted (`sed` is covered — recognised command)
- [ ] Does a "don't ask again" answer still write to the denied `settings.local.json`? — open, needs a hand test after restart
- [x] Record the results in `implementation.md` (T2)

### 2. `.mcp-file-access` (editor)
- [x] Add `read-only /.mcp.linux.json` and `read-only /.mcp.macos.json`
- [x] Check right after: MCP `save_file` to `.scratch/x` still works (a malformed file refuses every MCP write) — also: MCP `edit_file` on `.mcp.linux.json` now refused

### 3. `settings.local.json` cleanup (editor; T15, this repo only)
- [x] Drop `Bash(start docs/architecture/dependency_graph.html)` (path doesn't exist; human action)
- [x] Drop the `.bat` Jenkins entries — agent-facing instructions (CLAUDE.md, `tools/jenkins_status_check.md`, `tools/jenkins_issue_analysis.md`) use only `.sh`; the `.bat` files stay for humans
- [x] Add `mcp__mcp-tools-py__run_deptry_check`, `mcp__mcp-workspace__github_subissue_list` (T11, read-only)

### 4. `.claude/settings.json` (editor, last)
- [x] `permissions.deny` for native writes on `.mcp.json`, `.mcp.linux.json`, `.mcp.macos.json`, `.claude/settings.json`, `.claude/settings.local.json`, `.mcp-file-access` — one `Edit(/<path>)` rule per file (`Edit` covers all native write tools; `Write(path)` rules match nothing)
- [x] Restart; `/permissions` lists the project deny rules and no settings error appears (an invalid rule may be dropped silently) — 2026-11-16: all 6 listed, no warning

### 5. Stop-and-hand-off rule (MCP tools)
- [x] CLAUDE.md (MCP Tools section): "Protected files (`.mcp*.json`, `.claude/settings*.json`, `.mcp-file-access`): if MCP refuses or a native write is denied, stop and ask the user to edit the file — never write it via Bash or PowerShell."
- [x] `.claude/skills/rebase/SKILL.md` conflict table, config-files row: same rule for protected files (pick a side with `checkout --ours/--theirs`, or stop and hand off)

### 6. Test (MCP tools)
- [x] Unit test reading the real repo files (`REPO_ROOT` pattern) — `tests/docs/test_claude_settings.py`:
  - [x] `settings.json`: a deny rule for each of the six files (rule set per step 1); no `allow` key
  - [x] `settings.local.json`: none of the five `git_*` write tools; the two T11 entries present; the dropped `start …html` and `.bat` entries absent (this part moves to issue 5 when the file is untracked)

### 7. Docs (MCP tools)
- [x] `implementation.md`: T2 done (incl. `.mcp.linux/macos.json`), FU9 wording likewise; T11 done; T1, T15 partly (layout and user-file parts open); §1.1 row 4 (`settings.json` exists, deny only), "Effective today" (`permissions.deny`, "Headless `--settings`" row: deny merged via cwd); §1.4 "Settings" row; F1 (deny exists); F10 (deny also binds bypass agents for these files); §2.2 Tier 2 row
- [x] `tool-inventory.md` §6: the `tools/jenkins_*` and `start …html` entries in both the "Allow-lists" and "Bash left" tables; column `A` = `L` for `run_deptry_check`, `github_subissue_list`

## Acceptance

- [x] Interactive session (restart after the change), started at the root: native `Edit` and `Write` on all six protected files are blocked without a prompt (test with identical content, so a failed deny changes nothing) — 2026-11-16: native `Write` refused on `.mcp-file-access` and `.mcp.json` ("denied by your permission settings"); the other four use the same rule form, listed in `/permissions`
- [x] Subfolder session: blocked too, or the limit is documented (step 1) — documented: subfolder sessions don't load the root `settings.json`
- [ ] `Write` creating a protected file is blocked (e.g. `.mcp.macos.json` after a temporary rename by hand)
- [x] MCP `edit_file` on `.mcp.linux.json` and `.mcp.macos.json` is refused
- [x] MCP read and file tools, `run_deptry_check`, `github_subissue_list` run without prompts
- [ ] `mcp-coder verify`: the MCP edit smoke test passes
- [x] pylint, pytest, mypy pass (known pre-existing failures only)
