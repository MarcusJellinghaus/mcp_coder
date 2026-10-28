# Step 7 — Add `enforcement.md` links to the #1181 hub

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md` exactly.
> Minimal edits: add links, keep the existing `python.md` / `repo.md` links, change nothing
> else. Make one commit.

## Precondition
`docs/repository-setup/quality-and-security-checks.md` exists. If it does not, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE
`docs/repository-setup/quality-and-security-checks.md`

## HOW
Link target from this file: `../architecture/enforcement.md`.
- **Overview table**, *Links* column: append `[`enforcement.md`](../architecture/enforcement.md)` to the
  rows *Architecture*, *File size* and *Dependencies*.
- **`## Architecture`:** append `Why: [`enforcement.md`](../architecture/enforcement.md).` after the
  existing `python.md` link sentence.
- **`## File size`:** append the same `Why:` link after the `repo.md` sentence.
- **`## Dependencies`:** append the same `Why:` link after the `dependabot.yml` sentence.
- **`## Repo hygiene`, `forbidden-calls` bullet:** append
  `Why: [`enforcement.md`](../architecture/enforcement.md#shim-boundary).` If the bullet no
  longer matches `RULES` in `tools/check_forbidden_calls.py` (#1350 landed), correct its wording to
  the current `RULES`.

## ALGORITHM
None.

## DATA
None.

## Checks
- `search_files(pattern="enforcement.md", glob="docs/repository-setup/quality-and-security-checks.md")`:
  7 hits (3 table rows, 4 sections).
- The anchor `#shim-boundary` exists in `docs/architecture/enforcement.md`.
- Final sweep: `search_files(pattern="docs/architecture/(pydeps_graph|dependency_)")`
  finds hits only in `.claude/settings.local.json` (out of scope) and `pr_info/`.

## Commit
`docs(repository-setup): link quality checks hub to enforcement.md`
