# Step 1: Update `labels.json` schema + `test_types.py`

> **Context**: Read `pr_info/steps/summary.md` for the full design. This step updates the data schema and its validation tests.

## TDD: Update tests first, then schema

### 1a. Update `tests/workflows/vscodeclaude/test_types.py`

**WHERE**: `tests/workflows/vscodeclaude/test_types.py` — class `TestLabelsJsonVscodeclaudeMetadata`

**WHAT**: Update two test methods:

1. `test_human_action_labels_have_vscodeclaude_metadata()`:
   - Change `required_fields` from `{"emoji", "display_name", "stage_short", "initial_command", "followup_command"}` to `{"emoji", "display_name", "stage_short"}` (base fields all labels must have)
   - Add assertion: for labels with commands, `commands` must be a list of strings
   - For labels without commands (pr-created), assert `commands` key is absent

2. `test_pr_created_has_null_commands()`:
   - Rename to `test_pr_created_has_no_commands()`
   - Change from asserting `initial_command is None` and `followup_command is None` to asserting `"commands" not in pr_created["vscodeclaude"]`

**ALGORITHM** (test_human_action_labels_have_vscodeclaude_metadata):
```python
base_fields = {"emoji", "display_name", "stage_short"}
for label in human_action_labels:
    assert "vscodeclaude" in label
    assert base_fields.issubset(set(vscodeclaude.keys()))
    if "commands" in vscodeclaude:
        assert isinstance(vscodeclaude["commands"], list)
        assert all(isinstance(cmd, str) for cmd in vscodeclaude["commands"])
```

**DATA**: No new data structures. Tests validate the JSON schema shape.

### 1b. Update `src/mcp_coder/config/labels.json`

**WHERE**: `src/mcp_coder/config/labels.json`

**WHAT**: In each `vscodeclaude` block, replace `initial_command`/`followup_command` with `commands`:

| Status | Old | New |
|--------|-----|-----|
| `status-01:created` | `initial_command: "/issue_analyse", followup_command: "/discuss"` | `"commands": ["/issue_analyse", "/discuss"]` |
| `status-04:plan-review` | `initial_command: "/plan_review", followup_command: "/discuss"` | `"commands": ["/plan_review", "/discuss"]` |
| `status-07:code-review` | `initial_command: "/implementation_review_supervisor", followup_command: null` | `"commands": ["/implementation_review_supervisor"]` |
| `status-10:pr-created` | `initial_command: null, followup_command: null` | Remove both fields (keep only `emoji`, `display_name`, `stage_short`) |

### 1c. Add `src/mcp_coder/config/labels_schema.md`

**WHERE**: `src/mcp_coder/config/labels_schema.md` (new file)

**WHAT**: Concise schema reference for `labels.json`. Document:
- Top-level structure (`workflow_labels` array, `ignore_labels` array)
- Per-label fields: `internal_id`, `name`, `color`, `description`, `category`, `stale_timeout_minutes`
- `vscodeclaude` block: `emoji`, `display_name`, `stage_short`, `commands`
- `commands` field: list of strings (slash commands), optional. Absent = display-only (no session). Empty list = bare environment. Examples for 1-command and 2-command flows.

Keep it short — field table + one example block.

### Verification

Run `test_types.py` to confirm schema validation passes:
```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-k", "test_types"])
```

**Note:** After this step, `test_issues.py::TestIsStatusEligibleForSession` will fail because `is_status_eligible_for_session()` still reads `initial_command` from the updated `labels.json`. This is expected — Step 2 fixes it by updating `issues.py`.
