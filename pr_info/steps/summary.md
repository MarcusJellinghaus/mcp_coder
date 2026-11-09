# Summary — #1145: Replace `gh` with the mcp-workspace GitHub tools in `.claude`

## Goal

Remove every remaining `gh` call from `.claude/` (skills, agents, `CLAUDE.md`) and use the
mcp-workspace GitHub tools instead. Update the three `docs/repository-setup/` files that
describe the agents' permissions and the mcp-workspace setup. **Scope is the replacement
only:** no type labels, no close, and no `implement_direct` frontmatter changes.

No Python code changes. Every edit is to markdown prompts, frontmatter or docs.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Issue writes (create/edit/comment) | `gh` through Bash, with `allowed-tools` grants such as `Bash(gh issue edit *)` | `github_issue_create` / `github_issue_edit` / `github_issue_comment` MCP tools |
| Cross-repo access | `gh … --repo owner/repo` plus the `MSYS_NO_PATHCONV=1` Git Bash workaround | `reference_name` on the MCP tools; the target must be a configured reference project; **no fallback** — any other repo stops |
| `issue-updater` agent | `Bash` under `bypassPermissions` (unrestricted shell) | **No `Bash`**, MCP tools only — a real narrowing of privilege |
| `issue-approver` agent | `Bash` for `gh` + `set-status` | `Bash` for `mcp-coder gh-tool set-status` only; the cross-repo `/approve` comment goes through `github_issue_comment` |
| `issue_update` read path | Rebuilds the body from a rendered view, unguarded | **Read guard:** stop without writing if the view failed, was truncated, or has an untrusted body; write back the body only |
| Failure detection | Implicit | Check for the success text in the tool result (`# #<n>: `, `Updated issue #`, `Added comment to issue #`); anything else is a failure |
| Main-session prompting | `gh issue edit` omitted from the allow list | The three issue write tools stay out of `.claude/settings.local.json` (unchanged file); the doc example no longer pre-approves them through a wildcard |

### Design principles applied

- **Tools and constraints, not method**, in `issue_update`. Inline `body` vs `body_file` is
  the LLM's choice, and the skill gives no example call. The method will change once
  mcp-workspace#251 adds a raw body read.
- **Positional/positive checks.** Truncation means the *last line* starts with
  `... truncated: showing`. An untrusted body means the *header line*
  `Contains text from untrusted authors:` lists `title/body`. Marker text quoted inside a
  body is not a signal.
- **Explain url resolution once.** The full reference-project `url` resolution rule lives only in
  `docs/repository-setup/claude-code.md`; other files state only what they need.
- **Wording constraint.** New text in `.claude/` must not contain `gh issue` or `gh pr`
  case-insensitively. Beware words ending in "gh": "through issue…", "although PR…" and
  "high issue…" all match.

### Reference strings (from mcp-workspace `github_operations/formatters.py` and `server.py`)

- View heading: `# #<number>: <title>`, or `# #<number>` alone for untrusted authors
- Truncation marker (last line): `... truncated: showing <n> of <total> lines.`
- Untrusted header line: `Contains text from untrusted authors: <parts>`
- Optional header line: `Linked branches: …`
- Empty body: `(no description)`
- Edit success: `Updated issue #<number> — <url> (state: <state>)`
- Comment success: `Added comment to issue #<number> — <url>`
- Failures are not always prefixed `Error:`; they can also read `GitHub rate limit …` or `GitHub request failed …`

## Files modified

```
.claude/CLAUDE.md                                   (step 1)
.claude/skills/issue_create/SKILL.md                (step 1)
.claude/skills/issue_update/SKILL.md                (step 1)
.claude/skills/issue_approve/SKILL.md               (step 1)
.claude/skills/issue_analyse_supervisor/SKILL.md    (step 1)
.claude/agents/issue-updater.md                     (step 1)
.claude/agents/issue-approver.md                    (step 1)
docs/repository-setup/agent-permissions.md          (step 2)
docs/repository-setup/README.md                     (step 2)
docs/repository-setup/claude-code.md                (step 2)
```

No files are created (besides these plan files) or deleted. `.claude/settings.local.json`
is deliberately **not** modified.

## Testing approach

TDD has no target here because no Python code changes. Each step is verified by searching
the files it edited (`mcp__mcp-workspace__search_files`) for the acceptance criteria. The
standard checks (format, pylint, pytest, mypy) then confirm nothing else broke. No new test
module: a content-scanning test of `.claude/` would add maintenance cost for a one-off
replacement, and the issue scopes the work to the replacement only.

## Steps

1. `step_1.md` — `.claude/`: skills, agents, `CLAUDE.md` (all acceptance criteria)
2. `step_2.md` — `docs/repository-setup/`: `agent-permissions.md`, `README.md`, `claude-code.md`
