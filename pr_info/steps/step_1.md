# Step 1 — Approve via `set-status` in skill, agent, supervisor and docs

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`), plus
> `.claude/CLAUDE.md`. Implement Step 1 exactly: edit the six markdown files listed under
> WHERE so that `issue_approve` / `issue-approver` set the status with
> `mcp-coder gh-tool set-status` instead of commenting `/approve` and sleeping. Keep the
> outcome table only in the skill. Run the verification searches, then pylint, pytest
> (`-n auto`, fast unit markers) and mypy, then `run_format_code`, and make exactly one
> commit. Use MCP tools only.

## Precondition

Each edit below targets existing text (quoted). If a quoted anchor is not found in its file
(text drifted), write one line to `pr_info/.blocked.txt` naming the file and anchor, and stop.

## WHERE

- `.claude/skills/issue_approve/SKILL.md`
- `.claude/agents/issue-approver.md`
- `.claude/skills/issue_analyse_supervisor/SKILL.md`
- `docs/repository-setup/agent-permissions.md`
- `docs/repository-setup/README.md`
- `docs/processes-prompts/development-process.md`

## WHAT

No functions or signatures — the "interface" is the skill's instruction text and the
`set-status` CLI call:

```
mcp-coder gh-tool set-status <next> --from-status <current> --issue <N> --force
```

### 1. `.claude/skills/issue_approve/SKILL.md`

**Frontmatter `allowed-tools`** — final list:

```yaml
allowed-tools:
  - mcp__mcp-workspace__github_issue_view
  - mcp__mcp-workspace__git
  - "Bash(mcp-coder gh-tool set-status *)"
  - "Bash(gh issue view *)"
  - "Bash(MSYS_NO_PATHCONV=1 gh issue comment *)"
  - mcp__mcp-workspace__read_file
```

(`mcp__mcp-tools-py__sleep` removed.)

**"Cross-Repo Issues" section** — replace its body with:

- If `--repo owner/repo` was given, compare it with `origin` (`mcp__mcp-workspace__git`,
  command `ls_remote`, args `["--get-url", "origin"]`). Normalise both: accept
  `https://github.com/owner/repo` and `git@github.com:owner/repo` forms, drop a trailing
  `.git`, compare case-insensitively.
- Match → ignore `--repo` entirely; follow the normal (workspace) path.
- No match (or no `origin`) → cross-repo: add `--repo owner/repo` to `gh` commands only —
  **never** to `set-status`, which has no `--repo` flag. Fetch with
  `gh issue view <N> --repo owner/repo` via Bash (`github_issue_view` only reaches the
  current repository).

**Instructions** — keep step 1's fetch and step 2 (validation) unchanged in number and
content, except step 1's note becomes: "Note its status labels (labels prefixed `status-`) —
step 3 uses them for the promotable check and the `--from-status` value." Replace old steps
3–6 with:

3. **Promote.**

   | current | next |
   |---|---|
   | `status-01:created` | `status-02:awaiting-planning` |
   | `status-04:plan-review` | `status-05:plan-ready` |
   | `status-07:code-review` | `status-08:ready-pr` |

   - More than one status label → don't promote; report "nothing to approve (multiple
     status labels: X, Y)".
   - Current status not in the table (including no status label) → don't promote; report
     "nothing to approve".
   - Cross-repo → comment `/approve`
     (`MSYS_NO_PATHCONV=1 gh issue comment <N> --repo owner/repo --body "/approve"`) and
     report "approval requested, not confirmed". No polling.
   - Otherwise run from the project directory (no `--project-dir`, no output redirection —
     the result is printed on stderr):
     ```bash
     mcp-coder gh-tool set-status <next> --from-status <current> --issue <N> --force
     ```
     `--force` only skips the clean-tree check, irrelevant for a label change.
     Do **not** also comment `/approve` — the Action would race this call.

4. **Report** the issue number and the outcome:

   | `set-status` result | Report |
   |---|---|
   | exit 0, `Updated issue #N to <next>` | `<current> → <next>` |
   | exit 0, `Skipped set-status to '…': current label is 'X', expected 'Y'` | "not approved (current status X)" |
   | non-zero exit | "approval failed: <error output>" — stop; no retry, no `/approve` fallback |

   Not-called outcomes are reported as stated in step 3.

Keep the closing `disable-model-invocation` note unchanged.

### 2. `.claude/agents/issue-approver.md`

- `tools:` — remove `mcp__mcp-tools-py__sleep`; add `mcp__mcp-workspace__git`.
- Anchor "You approve issues by commenting `/approve` on them,\nwhich triggers a GitHub Action
  to promote the issue status." → "You approve issues by setting their next workflow status
  with `mcp-coder gh-tool set-status` (cross-repo issues: by commenting `/approve`)."
- Anchor "The rest of\nthe file applies to you unchanged, including the post-approval wait
  and the transition check." → "The rest of the file applies to you unchanged."
- Keep "This replaces the skill's step 2" (step 2 is still validation).
- Anchor "**Shell** — `gh` commands only." → "**Shell** — `gh` and
  `mcp-coder gh-tool set-status` commands only."
- Anchor "**Report** the issue number and the status transition." → "**Report** the issue
  number and the outcome, as the skill's report step defines it."

### 3. `.claude/skills/issue_analyse_supervisor/SKILL.md` (L51 bullet)

Replace "The agent will approve, wait 5 seconds for the GitHub Action, then confirm the
transition landed. **Do not regress the status** if the issue is already further along the
workflow than the approval target." with:

"The agent sets the status synchronously via `mcp-coder gh-tool set-status` and reports the
outcome. An issue already further along than the approval target is not regressed — the
agent reports it as not approved."

### 4. Docs

- `docs/repository-setup/agent-permissions.md` L36–39: anchor "the agent had\ngrown the
  post-approval sleep and cross-repo handling" … "The sleep and `--repo` handling moved into
  the skill," → "the agent had grown cross-repo handling …" and "The `--repo` handling moved
  into the skill,". Rest of the paragraph unchanged.
- `docs/repository-setup/README.md` L58: "Requires `approve-command.yml` and the status
  labels" → "Requires `mcp-coder` on PATH and the status labels; `approve-command.yml` only
  for cross-repo approval".
- `docs/processes-prompts/development-process.md` L254: "Comments `/approve` on the issue to
  trigger status promotion via GitHub Actions." → "Sets the next status directly via
  `mcp-coder gh-tool set-status`."

Do not touch README ~L121, development-process ~L186/428/878 or `github.md` (manual
`/approve` path).

## HOW

- Integration point is the agent reading `.claude/skills/issue_approve/SKILL.md` at runtime;
  the agent's stated deltas (frontmatter, "Resolve Issue Number", step 2) must still match
  the skill after editing.
- Permissions: the skill's `allowed-tools` entry mirrors `plan_approve` /
  `implementation_approve` (`"Bash(mcp-coder gh-tool set-status *)"`); the agent runs with
  `bypassPermissions`.

## ALGORITHM (skill step 3, as written in prose)

```
labels = status-* labels of the issue
if len(labels) > 1: report "nothing to approve (multiple status labels: …)"; stop
if labels[0] not in PROMOTE (or none): report "nothing to approve"; stop
if cross_repo: gh issue comment --repo … "/approve"; report "requested, not confirmed"; stop
run set-status PROMOTE[cur] --from-status cur --issue N --force
map exit code + "Updated"/"Skipped" line to the report table
```

## DATA

- Input: issue number, optional `--repo owner/repo`.
- Output: one report line — `<current> → <next>` | "not approved (current status X)" |
  "approval failed: <error output>" | "nothing to approve[ (multiple status labels: …)]" |
  "approval requested, not confirmed".

## Tests / verification

No unit tests apply (markdown only). Verify with `mcp__mcp-workspace__search_files`:

- `sleep` in `.claude/skills/issue_approve/SKILL.md` and `.claude/agents/issue-approver.md`
  → no matches.
- `post-approval|wait 5 seconds` under `.claude/` and in `agent-permissions.md`
  → no matches.
- `set-status` in all three `.claude` files → present.
- `--repo` never appears on a `set-status` line in the skill.

Then run pylint, pytest
(`-n auto`, `-m "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"`)
and mypy; all must pass. Run `run_format_code`, then commit:

```
docs(skills): approve via set-status instead of /approve polling (#1252)
```
