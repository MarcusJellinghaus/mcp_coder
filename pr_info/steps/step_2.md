# Step 2 — Link the hub page from the existing docs

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`). Add the
> README *Detail Documentation* row and the four identical pointer lines described below.
> Change nothing else in those files (their stale facts are #1351). Check the links by
> hand, then format and commit as one commit.

## Precondition

`docs/repository-setup/quality-and-security-checks.md` exists (step 1), and all four target
headings listed below exist. If either does not hold, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `docs/repository-setup/README.md` — the *Detail Documentation* table
- `docs/repository-setup/python.md` — `## Architecture Enforcement`, `## CI Workflow for Python`
- `docs/repository-setup/github.md` — `## Repo Security Configuration Checks`, `## Code Quality CI`

## WHAT

README row, inserted directly above the `internal.md` row:

```
| Quality and security checks: which automated checks run, and why | [quality-and-security-checks.md](quality-and-security-checks.md) | Not for downstream use |
```

Pointer line, identical in all four places, as the first line after each heading (followed by a blank line):

```
> Overview: see [quality-and-security-checks.md](quality-and-security-checks.md).
```

## ALGORITHM

```
insert README row above the internal.md row
for heading in the four target headings:
    insert pointer line + blank line directly below the heading
confirm the link target exists
run_format_code; commit "docs: link quality and security checks overview (#1181)"
```

## DATA

No data structures. Result: 1 new table row and 4 identical one-line blockquotes.

## Verification

- `search_files` for `quality-and-security-checks.md` under `docs/repository-setup/`
  returns exactly 5 hits (1 README, 2 python.md, 2 github.md).
- `mcp__mcp-workspace__check_file_size` passes.
