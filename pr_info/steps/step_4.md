# Step 4: `status-91` label and PR-health docs

## LLM prompt

> Read `pr_info/steps/summary.md` and this file, and GitHub issue #1342 §5. Implement this step
> with TDD for the label: write the test first, then change `labels.json`, then the docs. Run
> `run_format_code`, pylint, mypy, ruff and pytest (`-n auto`, unit-test markers); all must pass.
> Produce exactly one commit. Do not edit `pr_info/TASK_TRACKER.md`.

## WHERE

- `src/mcp_coder/config/labels.json`
- `tests/config/test_label_config.py`
- Docs listed under HOW

## WHAT

`status-91` `description` becomes exactly:

`PR has review comments, unresolved threads, changes requested, or code-scanning alerts`

## HOW

The order everywhere is: merge conflict → failing CI → alerts → review comments.

| File | Edit |
|---|---|
| `docs/processes-prompts/processes/71-pr-follow-up.md` | Intro sentence; ASCII diagram (add alerts → `status-91`); "Detection order" line; "Order matters … Review comments come last"; `/pr_comment_triage` row of the slash-commands table; "Review feedback rules": remove "Code-scanning alerts are excluded" and add alerts as a live-state trigger; "Trusted authors only": alerts have no author, only the PR-author check applies; "Triage session": alert handling, and no `status-10` while an alert is open |
| `docs/coordinator-vscodeclaude.md` | Numbered list: alerts step 3, review feedback step 4; document `untrusted PR author @x — review comments and alerts not checked` |
| `docs/getting-started/label-setup.md` | Intro order sentence; `status-91` row |
| `docs/cli-reference.md` | Coordinator paragraph (line 335) |
| `docs/architecture/architecture.md` | PR health bullet |
| `docs/processes-prompts/claude_cheat_sheet.md` | PR follow-up list (line 77) and `/pr_comment_triage` row (line 32) |
| `docs/processes-prompts/processes/10-pr-merge.md` | "Failure exits" sentence |
| `docs/repository-setup/claude-code.md` | `/pr_comment_triage` row |
| `docs/processes-prompts/github_Issue_Workflow_Matrix.html` | `status-10` card (line 640); row 7 label (line 777); `status-91` card description (line 785), matching `labels.json` exactly |

## ALGORITHM

None.

## DATA

`validate_labels_config` limits label descriptions to 100 characters. The new text is within it.

## Tests (write first)

In `tests/config/test_label_config.py`, next to the existing `status-91` test (around line 176):
load the packaged `labels.json`, assert it passes `validate_labels_config`, and assert the
`pr_review_comments` description contains "code-scanning alerts".
