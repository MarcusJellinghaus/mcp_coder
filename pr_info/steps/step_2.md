# Step 2 — Document ruleset-aware branch protection checks

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/Decisions.md`, then implement
> `pr_info/steps/step_2.md` exactly. Edit only `docs/repository-setup/github.md`.
> Run pylint, pytest (`-n auto`, fast unit-test marker filter from CLAUDE.md) and
> mypy; all must pass. Then make exactly one commit.

## WHERE

- `docs/repository-setup/github.md`, section "GitHub Token Configuration"
  (the "not verifiable" note, ~L36-37)

## WHAT

1. **"Not verifiable" note (~L36-37):** replace the unconditional opening
   sentence ("Without `Administration: Read`, `verify` shows branch protection as
   `[WARN] not verifiable`") — it no longer holds when rulesets protect the branch.
   Keep one qualified sentence: classic protection needs `Administration: Read`;
   without it, the protection rows rely on rulesets alone. The reworded
   note states:
   - branch protection is read from both classic protection and rulesets; a
     protection found by either source counts and shows `[OK]`;
   - a row shows "not configured" only when both sources answered;
   - if one source can't be read and the other doesn't show the protection, the
     row shows `[WARN] not verifiable`. This includes classic showing no protection
     while rulesets can't be read (previously `[ERR] not configured`);
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
