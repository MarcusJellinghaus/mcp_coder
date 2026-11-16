# Step 3: docs for `check-sensitive-files`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only.
> Edit the two Markdown files as specified. Docs only, so no tests; still run pylint, mypy
> and pytest (`-n auto`, fast unit-test markers) to confirm green. One commit.

## Precondition

`docs/repository-setup/claude-permissions/design-concept.md` still mentions
`#1431` (the Related line near the top and the "planned CI warning" table cell), and
`docs/repository-setup/quality-and-security-checks.md` has the CI events table, the
Overview "Repo hygiene" row and the `## Repo hygiene` section. If any is missing, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `docs/repository-setup/quality-and-security-checks.md`
- `docs/repository-setup/claude-permissions/design-concept.md`

## WHAT

`quality-and-security-checks.md`:
1. **Overview table, "Repo hygiene" row:** extend the purpose with flagging sensitive-file
   changes, e.g. "Keep scratch files, URL deps and forbidden calls out; flag sensitive-file
   changes", and add `[`check_sensitive_files.py`](../../tools/check_sensitive_files.py)`
   to the references column.
2. **CI events table:** new row after `check-forbidden-folders`:
   `| check-sensitive-files | — | ✅ | — | Advisory, PR diff only: warns, never fails on findings |`
3. **`## Repo hygiene` section:** new bullet after `check-forbidden-folders`:
   - `check-sensitive-files` (PR-only, advisory, not required;
     [`check_sensitive_files.py`](../../tools/check_sensitive_files.py)): warns with
     annotations and a job-summary table when a PR changes a file that is `read-only` under
     the **base** branch's `.mcp-file-access`, the rules file itself, or a watch-list path
     (`pyproject.toml`, `.claude/agents/`, `.claude/skills/`, `.github/workflows/`, the
     script). Matching is case-insensitive; renames count for both paths; an invalid base
     rules file gives one warning and skips the read-only rule check. Run locally:
     `python tools/check_sensitive_files.py --base origin/main --head HEAD`.
   - Known limits, one short line each: a PR can suppress the check by editing `ci.yml`
     or the script (`pull_request` runs the head's workflow; possible follow-up
     `pull_request_target`), so it is an advisory signal, not a security control;
     canonical spellings (`.mcp.json.`, `:stream`) are not matched; Dependabot action bumps
     warn by design.

`design-concept.md`:
1. **Related line (near the top):** remove the `#1431 (CI warning)` entry from "Open
   work"; add a reference to the implemented check, e.g.
   `CI warning: [`check-sensitive-files`](../quality-and-security-checks.md#repo-hygiene).`
2. **Table row 2:** replace `planned CI warning: [#1431](…)` with
   `CI warning: [`check-sensitive-files`](../quality-and-security-checks.md#repo-hygiene)`;
   keep the `layout: #1433` part.

## HOW

Keep the existing table column counts and link style (relative links). No other sections.

## ALGORITHM / DATA

None (docs).

## Commit

`docs: document check-sensitive-files CI job (#1431)`
