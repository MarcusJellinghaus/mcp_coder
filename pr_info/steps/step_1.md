# Step 1 — Add the `status-91:pr-review-comments` label

See `pr_info/steps/summary.md` for full context. This step only adds the new
workflow label to `labels.json` and a regression test for it. No Python
behavior changes — `update_workflow_label()` and `build_label_lookups()`
already handle arbitrary entries generically.

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_1.md` exactly as written. Follow TDD: write the failing
> test first, then add the label entry, then confirm all quality checks pass.
> Produce exactly one commit for this step.

## WHERE

- `tests/config/test_label_config.py` — add one test function.
- `src/mcp_coder/config/labels.json` — add one entry to `workflow_labels`.

## WHAT

Test (write first, confirm it fails):

```python
def test_pr_review_comments_label_definition() -> None:
    """status-91:pr-review-comments exists with the expected shape."""
```

No new production functions — this step is data-only.

## HOW

1. In `tests/config/test_label_config.py`, add
   `test_pr_review_comments_label_definition()` near
   `test_bundled_labels_schema_validation()`. Load the bundled config the same
   way that test does (`load_labels_config(get_labels_config_path(None))`),
   then find the entry with `internal_id == "pr_review_comments"` and assert:
   - `name == "status-91:pr-review-comments"`
   - `category == "human_action"`
   - it has **no** `failure` key and **no** `promotable` key (matches the
     `pr_created` precedent — this is an escalation, not a terminal failure)
   - `vscodeclaude["commands"] == ["/pr_comment_triage"]`
   - `vscodeclaude["requires_branch"] is True`
2. Run this test — it must fail (label doesn't exist yet).
3. Add the label to `src/mcp_coder/config/labels.json`, inside
   `workflow_labels`, positioned after the `status-84:pr-ci-failed` entry
   (end of the PR-health decade group):

```json
{
  "internal_id": "pr_review_comments",
  "name": "status-91:pr-review-comments",
  "color": "b60205",
  "description": "PR has new review comments, unresolved threads, or a changes-requested review",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "💬",
    "display_name": "PR REVIEW COMMENTS",
    "stage_short": "pr-comments",
    "commands": ["/pr_comment_triage"],
    "requires_branch": true
  }
}
```

4. Re-run the new test plus the existing
   `test_bundled_labels_schema_validation()` — both must pass.

## ALGORITHM

N/A — static config addition.

## DATA

No new return values or data structures. The entry becomes visible through the
existing `build_label_lookups()` output (`id_to_name["pr_review_comments"] ==
"status-91:pr-review-comments"`), used by later steps.

## Quality checks

Run `mcp__mcp-tools-py__run_pytest_check` (fast unit markers),
`mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_mypy_check`. All
must pass before committing.

## Precondition

None — `labels.json` and `validate_labels_config()`'s schema are stable and
already confirmed to support this shape (mirrors `status-10:pr-created`).
