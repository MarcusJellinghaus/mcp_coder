# Step 1: Add `color` field to `labels.json` and test fixtures

> **Context**: See [summary.md](summary.md) for full issue context (#797).

## Goal

Add the `"color"` field to all vscodeclaude entries in `labels.json` that have `commands`, and update the mock configs in `conftest.py` to match.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/config/labels.json` | Modify — add `"color"` field |
| `tests/workflows/vscodeclaude/conftest.py` | Modify — add `"color"` to mock configs |

## WHAT

No new functions. Data-only changes to JSON config and Python dict literals.

### `labels.json` changes

Add `"color": "<value>"` to each vscodeclaude object that has a `commands` array:

| Entry | Color value |
|-------|-------------|
| `status-01:created` | `"green"` |
| `status-04:plan-review` | `"blue"` |
| `status-07:code-review` | `"yellow"` |
| `status-03f-timeout:planning-llm-timeout` | `"red"` |
| `status-03f-prereq:planning-prereq-failed` | `"red"` |
| `status-03f:planning-failed` | `"red"` |
| `status-06f:implementing-failed` | `"red"` |
| `status-06f-prep:task-tracker-prep-failed` | `"red"` |
| `status-06f-ci:ci-fix-needed` | `"red"` |
| `status-06f-timeout:llm-timeout` | `"red"` |
| `status-06f-nochange:no-changes-after-retries` | `"red"` |
| `status-09f:pr-creating-failed` | `"red"` |

**Skip**: `status-10:pr-created` (no `commands` field — would be dead config).

Place `"color"` as the last key inside each `"vscodeclaude"` object, after `"commands"`.

### `conftest.py` changes

Add `"color"` to the three mock configs that have `"commands"`:

```python
"status-01:created": {
    ...
    "commands": ["/issue_analyse", "/discuss"],
    "color": "green",
},
"status-04:plan-review": {
    ...
    "commands": ["/plan_review", "/discuss"],
    "color": "blue",
},
"status-07:code-review": {
    ...
    "commands": ["/implementation_review_supervisor"],
    "color": "yellow",
},
```

`status-10:pr-created` stays unchanged (no commands, no color).

## HOW

No integration points — pure data edits.

## ALGORITHM

N/A — data-only step.

## DATA

The `color` field is a plain string (`"green"`, `"blue"`, `"yellow"`, `"red"`). It is read later via `config.get("color")` which returns `None` when absent.

## Verification

1. Run `mcp__tools-py__run_pytest_check` with unit test exclusions — all existing tests must still pass (the `color` field is ignored until Step 2 adds the reading logic).
2. Run `mcp__tools-py__run_pylint_check` and `mcp__tools-py__run_mypy_check`.

## Commit

```
feat(vscodeclaude): add color field to labels.json and test fixtures (#797)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md, then implement Step 1.

Add the "color" field to all vscodeclaude entries in labels.json that have "commands" (skip status-10:pr-created which has no commands). Use the color mapping from the step file. Then update the mock configs in tests/workflows/vscodeclaude/conftest.py to include matching "color" fields.

Run all three code quality checks after making changes. Commit with the message from the step file.
```
