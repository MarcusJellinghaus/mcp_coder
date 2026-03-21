# Step 3: Fix HTML Matrix Label Names

**Reference:** See `pr_info/steps/summary.md` for full context.

## LLM Prompt

> Implement Step 3 from `pr_info/steps/summary.md`.
> Update `docs/processes-prompts/github_Issue_Workflow_Matrix.html` so that the failure label names in the "Failed" column match the actual `labels.json` naming convention (`status-03f:planning-failed` not `status:planning-failed`).
> After making changes, run pylint, pytest (unit tests only), and mypy checks.

## WHERE

- `docs/processes-prompts/github_Issue_Workflow_Matrix.html` — update label-name text in the Failed column cards

## WHAT

Fix the `.label-name` text content in 5 failure label cards:

| Current (HTML) | Correct (matches labels.json) |
|----------------|-------------------------------|
| `status:planning-failed` | `status-03f:planning-failed` |
| `status:implementing-failed` | `status-06f:implementing-failed` |
| `status:ci-fix-needed` | `status-06f-ci:ci-fix-needed` |
| `status:llm-timeout` | `status-06f-timeout:llm-timeout` |
| `status:pr-creating-failed` | `status-09f:pr-creating-failed` |

## HOW

- Find each `<div class="label-name">status:...-failed</div>` in the Failed column
- Replace the text content with the correct `status-{N}f[-subtype]:` prefixed name
- No CSS or structural changes needed — the styling already works

## ALGORITHM

```
1. Read the HTML file
2. Find the 5 failure label-name divs
3. Replace text content with correct label names
4. Save file
5. Run quality checks (no Python changes expected)
```

## DATA

No data structures. Text-only replacements in HTML.
