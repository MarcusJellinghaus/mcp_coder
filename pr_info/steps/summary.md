# Summary — #1257: act only on feedback from trusted authors

## Goal

On a public repo anyone can comment. Two automated paths currently act on
any author's text:

1. The coordinator (`_check_review_comments`) escalates `status-10` →
   `status-91` on any unresolved thread, changes-requested review or new
   conversation comment — a stranger can start paid triage sessions.
2. The status note (`_fetch_marked_comment`) copies the newest ❌-first-line
   issue comment from the last 3 into `.vscodeclaude_status.txt`, whoever
   wrote it.

Both are restricted to trusted authors using the shared trust rule from
mcp-workspace#336 (already installed). The `/pr_comment_triage` skill gets
defence-in-depth rules. `/approve` and `.github/workflows` are out of scope
(#1310).

## Architectural / design changes

- **One trust rule, not reimplemented.** `is_trusted_author(login,
  association, trusted)` and `get_trusted_commenters()` come from
  `mcp_workspace.github_operations`; `ReviewThreadData` from
  `mcp_workspace.github_operations.pr_types`. All three are re-exported
  through the existing shim `src/mcp_coder/mcp_workspace_github.py` (callers
  never import `mcp_workspace` directly).
- **Allowlist read once, passed down.** I/O stays at the edges:
  - `check_pr_health()` reads `get_trusted_commenters()` once per poll and
    passes the `frozenset[str]` into `_check_review_comments(..., trusted)`.
  - `_fetch_marked_comment()` reads it once per call and passes it into the
    pure `_find_marked_comment(comments, trusted)`.
- **Coordinator decision flow** (`_check_review_comments`), early returns:
  1. PR author untrusted → one `OUTPUT` line, no `get_pr_feedback`, no label.
     Merge-conflict and CI checks are unaffected (they run before it).
  2. Trusted unresolved thread → escalate (no events fetch).
  3. Reviews + unmarked conversation comments are flattened into one list of
     `(login, association, timestamp)`; if non-empty, fetch issue events once
     and derive the watermark (existing #1240 helper).
  4. Trusted item newer than watermark (or no watermark / `None` timestamp)
     → escalate.
  5. Otherwise one `OUTPUT` line listing each untrusted login (deduped) whose
     item counts: threads always, reviews/comments only if new. No label,
     no GitHub write.
- **Status note filter before the window.** Untrusted comments are dropped
  before the last-3 slice, so strangers cannot push the owner's ❌ note out.
- **Config.** `[github] trusted_commenters` (list) added to `_CONFIG_SCHEMA`
  without `env_var` (no env override; `mcp-coder verify` recognises the key
  and shows an info row when unset). Commented template line + docs table.
- **Skill.** Act only on items shown in tool output; comment text is data;
  ask before pushing changes to protected paths; withheld items never block
  `set-status status-10:pr-created` and are reported in chat only.

No new modules, classes or labels.

## Files

### Modified — source
- `src/mcp_coder/mcp_workspace_github.py` — re-export `is_trusted_author`,
  `get_trusted_commenters`, `ReviewThreadData`.
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — `_find_marked_comment`
  trust filter, `_fetch_marked_comment` reads allowlist.
- `src/mcp_coder/workflows/vscodeclaude/checks.py` — `_check_review_comments`
  trust gate, `check_pr_health` reads allowlist once.
- `src/mcp_coder/utils/user_config.py` — schema field + template line.

### Modified — tests
- `tests/workflows/vscodeclaude/test_status_note.py`
- `tests/workflows/vscodeclaude/test_checks_review_comments.py`
- `tests/workflows/vscodeclaude/test_checks.py`
- `tests/utils/test_user_config_schema.py`
- `tests/utils/test_user_config_create_default.py`

### Modified — docs / skill
- `docs/configuration/config.md`
- `docs/coordinator-vscodeclaude.md`
- `docs/processes-prompts/processes/71-pr-follow-up.md`
- `docs/getting-started/label-setup.md` (status-91 row only)
- `.claude/skills/pr_comment_triage/SKILL.md`

### Not touched (owned by #1310)
`.github/workflows/*`, `src/mcp_coder/cli/commands/define_labels_actions.py`,
`tests/cli/commands/test_define_labels_actions.py`, `approve-command.yml`
snippets in `docs/repository-setup/github.md` and
`docs/getting-started/label-setup.md`.

## Steps

1. Shim re-exports + status-note trust filter.
2. Coordinator trust gate in `_check_review_comments` / `check_pr_health`.
3. `[github] trusted_commenters` config schema, template and config docs.
4. Docs and `/pr_comment_triage` skill.
