# Step 2 — Document ruleset-aware branch protection checks

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/Decisions.md`, then implement
> `pr_info/steps/step_2.md` exactly. Check the precondition first. Edit only
> `docs/repository-setup/github.md`. Run pylint, pytest (`-n auto`, fast unit-test
> marker filter from CLAUDE.md) and mypy; all must pass. Then make exactly one commit.

## Precondition

The installed mcp-workspace contains the ruleset support. Check with
`search_library_files(scope="mcp_workspace", pattern="require_pull_request")`.
If there are no matches, write one line to `pr_info/.blocked.txt`
("mcp-workspace#350 not installed; reinstall/upgrade environment") and stop.

## WHERE

- `docs/repository-setup/github.md`, section "GitHub Token Configuration"
  (the "not verifiable" note, ~L36-37)

## WHAT

1. **"Not verifiable" note (~L36-37):** reword it to state:
   - branch protection is read from both classic protection and rulesets; a
     protection found by either source counts;
   - a row shows "not configured" only when both sources answered;
   - if either source can't be read, the row shows `[WARN] not verifiable`. This
     includes classic showing no protection while rulesets can't be read (previously
     `[ERR] not configured`);
   - not an error; the exit code is unaffected.
2. **Add one sentence** after that note: effective rules do not expose bypass actors,
   so "protected" does not mean "nobody can bypass".

Do **not** state which token permission the ruleset endpoints need (unverified,
Decision 4). The permission list (~L30) and the security-rows cross-reference
(~L69-71) stay unchanged.

## HOW

Docs only. Follow the existing style: short bullets or sentences, no new sections, no
example output block.

## ALGORITHM

None.

## DATA

None.

## Commit

`docs(verify): document ruleset-aware branch protection checks (#1294)`
