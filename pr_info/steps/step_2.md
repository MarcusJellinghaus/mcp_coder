# Step 2 — Document ruleset support and token permissions

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Check the preconditions first. Edit only `docs/repository-setup/github.md`. Run
> pylint, pytest (`-n auto`, fast unit-test marker filter from CLAUDE.md) and mypy
> against the upgraded environment; all must pass. Then make exactly one commit.

## Preconditions

1. The installed mcp-workspace contains the ruleset support. Check with
   `search_library_files(scope="mcp_workspace", pattern="require_pull_request")`.
   If there are no matches, write one line to `pr_info/.blocked.txt`
   ("mcp-workspace#350 not installed; reinstall/upgrade environment") and stop.
2. mcp-workspace#350 (or its PR / its docs) records which fine-grained token
   permission `GET /rules/branches/{branch}` and `GET /rulesets` need. Look it up with
   `github_issue_view(350, reference_name="mcp-workspace")` and search the
   mcp-workspace reference project. This precondition gates only edit 1, edit 4 and
   the permission sentence in edit 2. If the finding is not recorded: apply edit 2
   (without the permission sentence) and edit 3, run the checks, commit, then write
   one line to `pr_info/.blocked.txt` ("ruleset endpoint permissions not yet verified
   upstream; edit 1, edit 4 and the edit 2 permission sentence pending") and stop.

## WHERE

- `docs/repository-setup/github.md` (section "GitHub Token Configuration", and
  section "Repo Security Configuration Checks")

## WHAT

1. **Permission list (~L30):** today it reads `Administration: Read` (branch
   protection). Reword it to cover classic branch protection. If the ruleset
   endpoints need a different permission, add that permission as its own bullet,
   labelled "(rulesets)". If the needed permission is already in the list, add
   "(rulesets)" to that existing bullet instead.
2. **"Not verifiable" note (~L36-37):** state that branch protection is read from
   both classic protection and rulesets, and the strictest result wins.
   `[WARN] not verifiable` appears only when classic protection can't be read and
   rulesets show no protection. The exit code stays unaffected.
   *Permission sentence (gated by precondition 2):* if `/rules/branches/{branch}`
   needs no permission beyond those listed, state that a ruleset-protected branch
   shows OK even without `Administration: Read`. If it also needs
   `Administration: Read`, state that without it both sources are unreadable and the
   row shows `[WARN] not verifiable`.
3. **Add one sentence** after that note: effective rules do not expose bypass actors,
   so "protected" does not mean "nobody can bypass".
4. **Security rows (~L69-70):** the text says `Administration: Read` is "the same
   permission already listed ... above". Keep it accurate after edit 1, adjusting the
   wording only if the cross-reference changed.

## HOW

Docs only. Follow the existing style: short bullets, no new sections, no example
output block.

## ALGORITHM

None.

## DATA

None.

## Commit

`docs(verify): document ruleset-aware branch protection checks (#1294)`
