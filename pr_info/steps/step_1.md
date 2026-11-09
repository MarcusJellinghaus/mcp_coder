# Step 1 — Replace `gh` in `.claude/` (skills, agents, CLAUDE.md)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Edit only the seven `.claude/` files listed under WHERE, using the MCP file tools. Do not
> touch `docs/`, `.claude/settings.local.json` or `pr_info/TASK_TRACKER.md`. Run the
> verification and the quality checks listed below, then produce exactly one commit.

## Precondition

The mcp-workspace output strings in `summary.md` ("Reference strings") must still match the
installed mcp-workspace. Search reference project `mcp-workspace`
(`src/mcp_workspace/github_operations/formatters.py`, `src/mcp_workspace/server.py`) for
`truncated: showing`, `Contains text from untrusted authors`, `Updated issue #` and
`Added comment to issue #`. Also confirm that `github_issue_comment`, `github_issue_edit`
and `github_issue_create` accept `reference_name`, and that create/edit/comment accept
`body_file`. If any of this is missing, write one line to `pr_info/.blocked.txt` naming the
missing item and stop.

## WHERE

```
.claude/skills/issue_create/SKILL.md
.claude/skills/issue_update/SKILL.md
.claude/skills/issue_approve/SKILL.md
.claude/skills/issue_analyse_supervisor/SKILL.md
.claude/agents/issue-updater.md
.claude/agents/issue-approver.md
.claude/CLAUDE.md
```

## WHAT / HOW (per file)

### `skills/issue_create/SKILL.md`
- `allowed-tools`: replace `"Bash(gh issue create *)"` with `mcp__mcp-workspace__github_issue_create`.
- Replace the "Create the issue using" bash block with a call to
  `mcp__mcp-workspace__github_issue_create` with `title` and `body`.

### `skills/issue_update/SKILL.md`
- `allowed-tools`: drop `"Bash(gh issue edit *)"`. Add `mcp__mcp-workspace__github_issue_edit`
  and `mcp__mcp-workspace__edit_file`. Keep `github_issue_view`, `save_file`,
  `delete_this_file`, `read_file`, `list_directory` and `search_files`.
- Replace steps 2 and 4–6 with tools and constraints, as short bullets. Do **not** add an
  example call, and do **not** prescribe inline `body` vs `body_file`.
  - **Fetch:** `github_issue_view` with `include_comments=false` and a large `max_lines`
    (e.g. 5000).
  - **Header:** a title line, a `State:` line, and optionally a
    `Contains text from untrusted authors:` line and a `Linked branches:` line. Write back
    the body only, never header lines. A body rendered as `(no description)` is empty.
  - **Stop without writing** (report the reason) if:
    - the output does not start with `# #<number>: ` — any other output is a failure,
      including `GitHub rate limit …` / `GitHub request failed …`;
    - the last line of the output starts with `... truncated: showing`;
    - the `Contains text from untrusted authors:` header line lists `title/body`.

    Marker or fence text quoted *inside* the body is not a signal.
  - **Write:** `github_issue_edit(number=…, title=…, body=… | body_file=…)`. The result must
    start with `Updated issue #`; anything else → report failure.
  - **Temp files:** delete anything written to `.scratch/` afterwards.
- Leave the Base Branch section and "The updated issue should include" list unchanged.

### `skills/issue_approve/SKILL.md`
- `allowed-tools`: remove `"Bash(gh issue view *)"` and
  `"Bash(MSYS_NO_PATHCONV=1 gh issue comment *)"`. Add
  `mcp__mcp-workspace__github_issue_comment` and `mcp__mcp-workspace__get_reference_projects`.
- **Cross-Repo Issues** section: keep the `origin` comparison and normalisation. Replace the
  "No match" bullet with:
  - No match (or no `origin`) → cross-repo. Call `get_reference_projects()` and pick the
    entry whose `url` normalises (as above) to `owner/repo`. Use its `name` as
    `reference_name` on every GitHub tool call. Entries with a null `url` never match.
  - No matching entry → stop and report "not a reference project". There is no other route.
  - **Never** pass a repo to `set-status`.
  - Delete the sentence that `github_issue_view` "only reaches the current repository".
- Step 1: call `github_issue_view` with the issue number, plus `reference_name` for
  cross-repo. Success: the output starts with `# #<number>: `, or is `# #<number>` followed
  by a newline (untrusted author; proceed normally). Anything else → "approval failed:
  <result>".
- Step 3, cross-repo bullet: call
  `github_issue_comment(number=…, reference_name=…, body="/approve")` and report "approval
  requested, not confirmed". No polling. Remove the `MSYS_NO_PATHCONV` bash block.
- Step 4 report table: add the cross-repo rows — a comment result starting with
  `Added comment to issue #` → "approval requested, not confirmed"; anything else →
  "approval failed: <result>", no retry.
- The same-repo path (`set-status`, never comment `/approve`) stays unchanged.

### `skills/issue_analyse_supervisor/SKILL.md`
- In Finalize, replace "The agent sets the status synchronously via
  `mcp-coder gh-tool set-status` and reports the outcome." with: for same-repo issues the
  agent sets the status synchronously via `mcp-coder gh-tool set-status`; for cross-repo
  issues it comments `/approve` and reports "approval requested, not confirmed".

### `agents/issue-updater.md`
- `tools:`: remove `Bash` and add `mcp__mcp-workspace__github_issue_edit`. Keep the others.
- Body: delete the `- **Shell** — \`gh\` commands only.` bullet.

### `agents/issue-approver.md`
- `tools:`: add `mcp__mcp-workspace__github_issue_comment` and
  `mcp__mcp-workspace__get_reference_projects`. Keep `Bash`.
- Intro: change "(cross-repo issues: by commenting `/approve`)" to "(cross-repo issues: by
  commenting `/approve` with `mcp__mcp-workspace__github_issue_comment`)".
- Shell bullet → `- **Shell** — \`mcp-coder gh-tool set-status\` only.`

### `CLAUDE.md`
- Justify-native-tool line: "the approved git/gh commands under Git operations" → "the
  approved commands under Git operations".
- Mapping table: rename the left-column entries
  - `gh issue view` → View GitHub issue
  - `gh issue list` → List GitHub issues
  - `gh pr view` → View GitHub PR
  - `gh search` → Search GitHub issues/PRs

  Then add rows: Create GitHub issue → `github_issue_create`; Edit GitHub issue →
  `github_issue_edit`; Comment on GitHub issue → `github_issue_comment`; Create GitHub PR →
  `github_pr_create`; List GitHub labels → `github_label_list` (all `mcp__mcp-workspace__`).
- "Sibling repos are readable…" line: append that the GitHub issue/PR read tools and the
  issue write tools take `reference_name` for reference projects. That is the only
  cross-repo route; for repos that aren't reference projects, stop and report.
- Git operations allowlist block: remove the lines `gh issue create / edit / comment …`,
  `gh issue view (cross-repo only …)` and `gh pr create`. Keep the git lines and
  `mcp-coder gh-tool set-status <label>`.
- **Status labels** line → "`github_issue_create` and `github_issue_edit` reject `status-*`
  labels; use `mcp-coder gh-tool set-status` to change issue workflow status."
- Delete the **Slash-prefixed `gh` arguments** (`MSYS_NO_PATHCONV=1`) paragraph.
- **Privileged agents** paragraph:
  - "skip the prompts these commands normally trigger" → "skip the prompts these commands
    and the MCP issue write tools normally trigger".
  - Add that `issue-updater` has no `Bash`, so "`Bash` is unrestricted inside them" applies
    to `commit-pusher` and `issue-approver` only.

**Wording rule:** no new text may contain `gh issue` or `gh pr` case-insensitively. Avoid
words ending in "gh" before "issue"/"PR" (through, although, high, enough).

## ALGORITHM (verification)

```
hits = search_files(pattern="(?i)gh issue|gh pr|MSYS_NO_PATHCONV", glob=".claude/**")
assert hits == []                                  # acceptance 1
fm = read_file(".claude/agents/issue-updater.md")
assert "  - Bash" not in fm.tools                  # acceptance 2
skill = read_file(".claude/skills/issue_update/SKILL.md")
assert "... truncated: showing" in skill           # acceptance 3: truncation stop rule present
```

## DATA

No code data structures. The skill rules rely on the tool return strings listed in
`summary.md` → "Reference strings".

## Checks and commit

- Run `run_format_code`, `run_pylint_check`, `run_mypy_check` and `run_pytest_check` (fast
  unit-test marker set, `-n auto`). All must pass. No Python changed, so a failure here is
  pre-existing: write one line to `pr_info/.blocked.txt` and stop.
- One commit, e.g. `chore(claude): replace gh with mcp-workspace GitHub tools (#1145)`.
