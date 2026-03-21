# Summary: Add Workflow Failure Status Labels (Infrastructure)

**Issue:** #272

## What This Changes

Add 5 failure status labels to `labels.json` so automated workflows can distinguish between "in progress" and "failed" states. Update documentation and HTML matrix to reflect the new labels.

## Design Decisions

- **No code changes required.** All label processing (`set-status`, `define-labels`, coordinator, vscodeclaude) reads from `labels.json` dynamically. Adding entries to the JSON is sufficient.
- **Category = `human_action`** (not a new "failed" category). Failure labels require human review before retry.
- **`vscodeclaude` config** with `initial_command: null` — opens a session for manual investigation.
- **No `stale_timeout_minutes`** — there's no bot process to go stale on a failed label.
- **Naming pattern:** `status-{N}f[-subtype]:{description}` — the `f` suffix distinguishes failures from their parent statuses. All names start with `status-` so existing deletion/validation logic works unchanged.

## Architectural Impact

**None.** This is a pure data/config change. The existing architecture already supports arbitrary labels in `labels.json`. Validation is set-membership based (`label in valid_labels`), label removal uses `name.startswith("status-")`, and vscodeclaude config lookup is by label name from config.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/config/labels.json` | Add 5 failure label entries |
| `tests/cli/commands/test_set_status.py` | Update hardcoded count `10` → `15` and add failure labels to `VALID_STATUS_LABELS` |
| `tests/cli/commands/test_define_labels.py` | Update hardcoded count `10` → `15` |
| `tests/cli/commands/test_define_labels_label_changes.py` | Update `created` count `9` → `14` and `call_count` `9` → `14` (two tests) |
| `docs/processes-prompts/development-process.md` | Add failure handling section |
| `docs/processes-prompts/github_Issue_Workflow_Matrix.html` | Fix label names to match `labels.json` naming convention; differentiate step-number badges (`6f`, `6f-ci`, `6f-t`) |

## New Labels

| Label Name | `internal_id` | Color | Parent |
|------------|---------------|-------|--------|
| `status-03f:planning-failed` | `planning_failed` | `b60205` (red) | status-03 |
| `status-06f:implementing-failed` | `implementing_failed` | `b60205` (red) | status-06 |
| `status-06f-ci:ci-fix-needed` | `ci_fix_needed` | `d93f0b` (orange-red) | status-06 |
| `status-06f-timeout:llm-timeout` | `llm_timeout` | `e99695` (light red) | status-06 |
| `status-09f:pr-creating-failed` | `pr_creating_failed` | `b60205` (red) | status-09 |

## Implementation Steps

1. **Step 1** — Add 5 failure labels to `labels.json` + update test expectations
2. **Step 2** — Update development-process.md with failure handling documentation
3. **Step 3** — Fix HTML matrix label names to match `labels.json`
