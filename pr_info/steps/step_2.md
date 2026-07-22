# Step 2 — Label definitions in `labels.json`

> References `pr_info/steps/summary.md` (Label section). Defines the review labels only;
> pickup/mapping is #1073.

## WHERE
- `src/mcp_coder/config/labels.json` (modify — **append** to `workflow_labels`)
- `tests/config/test_label_config.py` (modify — add assertions)

## WHAT (append at the **end** of `workflow_labels`, in this order)
| internal_id | name | category | extra |
|---|---|---|---|
| `plan_review_bot` | `status-14:plan-review-bot` | `bot_pickup` | — |
| `plan_reviewing` | `status-14i:plan-reviewing` | `bot_busy` | `stale_timeout_minutes` |
| `code_review_bot` | `status-17:code-review-bot` | `bot_pickup` | — |
| `code_reviewing` | `status-17i:code-reviewing` | `bot_busy` | `stale_timeout_minutes` |
| `plan_review_failed` | `status-14f:plan-review-failed` | `human_action` | `failure:true` |
| `plan_review_rounds` | `status-14f-rounds:plan-review-rounds-exhausted` | `human_action` | `failure:true` |
| `plan_review_timeout` | `status-14f-timeout:plan-review-llm-timeout` | `human_action` | `failure:true` |
| `plan_review_mcp` | `status-14f-mcp:plan-review-mcp-unavailable` | `human_action` | `failure:true` |
| `code_review_failed` | `status-17f:code-review-failed` | `human_action` | `failure:true` |
| `code_review_ci` | `status-17f-ci:code-review-ci-fix-needed` | `human_action` | `failure:true` |
| `code_review_rounds` | `status-17f-rounds:code-review-rounds-exhausted` | `human_action` | `failure:true` |
| `code_review_timeout` | `status-17f-timeout:code-review-llm-timeout` | `human_action` | `failure:true` |
| `code_review_mcp` | `status-17f-mcp:code-review-mcp-unavailable` | `human_action` | `failure:true` |

## HOW
- Every entry needs `color`, `description`, `category`. Failure entries add
  `"failure": true` and `"vscodeclaude": {"commands": ["/check_branch_status"], ...}`.
- `14f-*` entries **omit** `requires_branch`; the two `bot_busy` entries include
  `"stale_timeout_minutes"` (mirror `code_review` = 120 for `code_reviewing`; a smaller value
  for `plan_reviewing`, e.g. 30).
- **Appending at end is load-bearing** (`label_config.py:validate_labels_config`): no
  `promotable` label may be immediately followed by a `failure` label, and
  `build_promotions` derives promotion targets from list adjacency. Do **not** insert near
  `04`/`07`.

## DATA
- Pure JSON additions; no schema change.

## TDD / checks
- Test first: extend `tests/config/test_label_config.py` to
  `load_labels_config` + `validate_labels_config` the bundled config and assert:
  the 13 new `internal_id`s exist, `build_label_lookups` maps them, and `validate_labels_config`
  raises nothing.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","label"])`, then pylint + mypy.

## LLM prompt for this step
> Implement Step 2 of `pr_info/steps/summary.md`. First add failing assertions to
> `tests/config/test_label_config.py` for the 13 new review labels (ids/names/categories in the
> Step 2 table) and that `validate_labels_config` still passes. Then append the 13 label objects
> to the **end** of `workflow_labels` in `src/mcp_coder/config/labels.json`, following the
> existing entries' shape (color/description/category, `failure:true` +
> `vscodeclaude.commands:["/check_branch_status"]` for `*f*`, `stale_timeout_minutes` on the two
> `bot_busy` labels, no `requires_branch` on `14f-*`). Keep them at the list end so the
> promotable→failure adjacency rule holds. Run the label tests, pylint, mypy.
