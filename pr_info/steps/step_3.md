# Step 3 — Document range keys and the unlisted-`0` rule

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> Docs only: edit `docs/configuration/toolkits.md` as described. Do not touch
> the npm example (#1451 edits it). If the Defaults table has no `exit_codes`
> row, write one line to `pr_info/.blocked.txt` and stop. Run pytest (`-n auto`,
> unit markers as in CLAUDE.md) to confirm nothing broke, run the formatter,
> then make exactly one commit.

## WHERE

`docs/configuration/toolkits.md`, section "Config reference":

- "Defaults" table, row `exit_codes`
- "Step fields" table, row `exit_codes`
- "Step fields" → "Rules" list: one new bullet

## WHAT

1. **Defaults row `exit_codes`** — replace "An unmapped code is `error`" with
   content covering:
   - keys are single codes or inclusive ranges `N-M`, e.g.
     `{ 0 = "ok", 1-125 = "findings" }`; two keys may not share a code;
   - a code no key matches is `ok` if it is `0`, else `error`;
   - exit codes are 8-bit on POSIX, so a count of 256 wraps to `0`; on Windows
     it stays 256 and falls outside `1-125`; Windows crash codes (`0xC…`) are
     written in decimal.
   Keep the row short; move detail into the Rules list below the table if the
   cell gets long.
2. **Step-fields row `exit_codes`** — "Replaces the default table — no merge;
   an unlisted `0` is still `ok`".
3. **Step-fields Rules bullet** — dependency-cruiser:
   ```toml
   { argv = ["npm", "run", "arch"], exit_codes = { 0 = "ok", 1-125 = "findings" } }
   ```
   with the notes: dependency-cruiser exits with its error count (plus stale
   baseline entries whose severity is `error`) only with the `err`,
   `err-long`, `null`, `teamcity` and `azure-devops` reporters; it also exits
   `1` when it crashes, so `1` cannot tell a crash from one finding.

## HOW / ALGORITHM / DATA

No code. Match the page's existing style (tables, short bullets).

## Done when

The three edits are in place, the npm example is unchanged, pytest still
passes, one commit, e.g. `docs(toolkits): document exit_codes ranges`.
