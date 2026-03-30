# Step 2: Add commands to error statuses in labels.json

## Context

See `pr_info/steps/summary.md` for full issue context (Issue #643).

## Problem

Five error statuses have `vscodeclaude` config (emoji, display_name, stage_short) but no `commands` key. When the startup script is generated for these statuses, `commands` defaults to `[]`, producing a bare script that exits after environment setup — no Claude session is launched.

## WHERE

- **Modify**: `src/mcp_coder/config/labels.json` — five error status entries
- **Modify**: `tests/workflows/test_label_config.py` — add test for error status commands

## WHAT

Add `"commands": ["/check_branch_status"]` to the `vscodeclaude` block of these five statuses:

1. `status-03f:planning-failed` (internal_id: `planning_failed`)
2. `status-06f:implementing-failed` (internal_id: `implementing_failed`)
3. `status-06f-ci:ci-fix-needed` (internal_id: `ci_fix_needed`)
4. `status-06f-timeout:llm-timeout` (internal_id: `llm_timeout`)
5. `status-09f:pr-creating-failed` (internal_id: `pr_creating_failed`)

**Not changed**: `status-10:pr-created` — intentionally left without commands.

## HOW

Edit JSON directly. No code logic changes. The existing `workspace.py` `create_startup_script` function already handles single-command flows via `INTERACTIVE_ONLY_SECTION_WINDOWS`.

## ALGORITHM

```
For each of the 5 error statuses in labels.json:
    Add "commands": ["/check_branch_status"] to its "vscodeclaude" block
```

## DATA

Each modified entry gains:
```json
"commands": ["/check_branch_status"]
```

The resulting startup script for these statuses will use `INTERACTIVE_ONLY_SECTION_WINDOWS`, generating: `claude "/check_branch_status {issue_number}"`

## Test Plan

### Test: Error statuses have commands configured (TDD — write first)

**File**: `tests/workflows/test_label_config.py`

**Function**: `test_error_statuses_have_vscodeclaude_commands()`

**Logic**: Use `@pytest.mark.parametrize` over the 5 error status internal_ids for clearer per-status failure messages. For each, assert that `vscodeclaude.commands` equals `["/check_branch_status"]`. Also test (as a separate case or negative parametrize) that `status-10:pr-created` (internal_id: `pr_created`) does NOT have commands (intentional).

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement Step 2: Add commands to error statuses in labels.json.

1. First, add a test to tests/workflows/test_label_config.py:
   - test_error_statuses_have_vscodeclaude_commands: use @pytest.mark.parametrize over the 5 internal_ids
     (planning_failed, implementing_failed, ci_fix_needed, llm_timeout, pr_creating_failed).
     For each, assert vscodeclaude.commands equals ["/check_branch_status"].
   - Also verify status-10:pr-created (internal_id: pr_created) does NOT have commands

2. Then edit src/mcp_coder/config/labels.json:
   - Add "commands": ["/check_branch_status"] to the vscodeclaude block of all 5 error statuses listed above

3. Run all three code quality checks (pylint, pytest, mypy). Fix any issues.
```
