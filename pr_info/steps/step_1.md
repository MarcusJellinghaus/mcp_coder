# Step 1 — Rename the `status-17f-ci-unknown` label

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Replace the old label name with the new one in the listed files only, run the
> code quality checks from CLAUDE.md, and produce one commit.

## WHERE

- `src/mcp_coder/config/labels.json` (line ~578)
- `tests/cli/commands/test_define_labels.py` (line ~152)
- `tests/config/test_label_config.py` (line ~248)
- `docs/processes-prompts/development-process.md` (line ~1147)
- `docs/processes-prompts/github_Issue_Workflow_Matrix.html` (line ~633)
- `docs/cli-reference.md` (line ~499)

## WHAT

Replace the literal

```
status-17f-ci-unknown:code-review-ci-undeterminable
```

with

```
status-17f-ci-unknown:code-review-ci-unknown
```

in each file above. No functions change.

## HOW

- `labels.json`: change only the `name` field. Keep `internal_id`
  (`code_review_ci_unknown`), `display_name` (`CODE REVIEW CI UNDETERMINABLE`),
  `stage_short` (`code-review-ci-unknown`) and all other fields as they are.
- Tests: the two test files list expected label names; update the literal only.
  This is a data rename, so the "test" is the existing tests updated to the new name.
- Docs: replace the literal only. Leave `development-process.md:1157` (prefix only)
  and the HTML CSS class `status-code-review-ci-unknown` untouched.

## ALGORITHM

```
for file in WHERE:
    replace old literal with new literal
search repo (excluding pr_info/) for "code-review-ci-undeterminable" -> expect 0 matches
```

Precondition: each file contains the old literal. If one does not, write one line
to `pr_info/.blocked.txt` and stop.

## DATA

The `labels.json` entry keeps its shape; only `"name"` changes to the new 44-char value.

## Checks

- `mcp__mcp-workspace__search_files(pattern="code-review-ci-undeterminable")` → 0 matches
  outside `pr_info/` (the plan files quote the old name themselves; ignore those hits).
  The `display_name` uses spaces and upper case, so it does not match.
- pylint, pytest (fast unit set, `-n auto`), mypy — all pass.
- Commit: `fix(labels): shorten status-17f-ci-unknown name to fit GitHub limit`
