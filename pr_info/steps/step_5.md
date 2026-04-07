# Step 5: CLI help text + docs verification

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## Goal
Update CLI help text for create-plan to mention failure handling. Verify docs/configuration/config.md is accurate for `update_issue_labels` and `post_issue_comments`.

## WHERE

### Modified files
- `src/mcp_coder/cli/parsers.py` — update `add_create_plan_parser()` help text

### Verified files (read-only check)
- `docs/configuration/config.md` — verify `update_issue_labels` and `post_issue_comments` rows are accurate

## WHAT

### `parsers.py` — update create-plan command help
Change the `help` parameter of `add_parser("create-plan", ...)` from:
```python
help="Generate implementation plan for a GitHub issue"
```
to:
```python
help="Generate implementation plan for a GitHub issue (sets failure labels and posts comments on error)"
```

### `docs/configuration/config.md` — verification only
Verify the `[coordinator.repos.*]` table contains accurate rows for:
- `update_issue_labels` — should mention workflow success/failure label transitions
- `post_issue_comments` — should mention workflow failure comments

Currently the table says:
```
| `update_issue_labels` | boolean | Update GitHub issue labels on workflow success/failure | No | `false` |
| `post_issue_comments` | boolean | Post GitHub comments on workflow failure | No | `false` |
```

These are already accurate for the create-plan workflow's behavior. No docs change needed.

## HOW

### CLI help text change
Single line change in `add_create_plan_parser()`. The description is intentionally brief — it acknowledges the feature exists without enumerating labels.

## ALGORITHM
```
1. Update help text string in parsers.py
2. Read docs/configuration/config.md to verify accuracy
3. Run pylint/mypy/pytest to confirm nothing breaks
```

## DATA
No new data structures.

## Tests
No new tests needed. Existing CLI parser tests (if any) would catch help text changes only if they assert exact strings. The `test_create_plan.py` CLI command tests mock the execute function, so they won't be affected.

## Commit message
```
docs(create_plan): update CLI help text for failure handling

Update create-plan command help to mention failure label and
comment behavior. Verify docs/configuration/config.md accuracy
for update_issue_labels and post_issue_comments flags.
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_5.md.

Key points:
- Update the help text for create-plan in src/mcp_coder/cli/parsers.py (one-liner change)
- Read docs/configuration/config.md and verify the update_issue_labels and post_issue_comments rows are accurate
- If docs need changes, make them; if they're already accurate, no change needed
- Run all quality checks (pylint, pytest, mypy) and fix any issues
```
