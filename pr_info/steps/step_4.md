# Step 4 — `status-06f-blocked:implementation-blocked` label

Config + tests only. Must land **before** Step 5, which maps a failure reason onto this
label's `internal_id`.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/config/labels.json` | new entry in `workflow_labels` |
| `tests/config/test_label_config.py` | add to `ERROR_STATUS_IDS` (`:176`) |
| `tests/cli/commands/test_define_labels.py` | add to `expected_names` (`:128` area) |

## WHAT

Insert directly **after** the `no_changes_after_retries` entry (`labels.json:243-257`), so
the whole `status-06f-*` block stays contiguous:

```json
{
  "internal_id": "implementation_blocked",
  "name": "status-06f-blocked:implementation-blocked",
  "color": "d93f0b",
  "description": "Agent reported it was blocked and could not verify the work",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "🚧",
    "display_name": "IMPLEMENTATION BLOCKED",
    "stage_short": "blocked",
    "commands": ["/check_branch_status"],
    "color": "red"
  }
}
```

## HOW

Two `color` keys mean different things — do not conflate them:

- top-level `color` is a **6-char hex**, format-asserted at
  `tests/config/test_label_config.py:132-136`. `d93f0b` matches the other `06f`
  human-action labels (`ci_fix_needed`, `no_changes_after_retries`).
- nested `vscodeclaude.color` is the literal string `"red"` for every failure label.

Only `emoji` and `stage_short` are genuinely free; everything else follows the siblings.

`tests/cli/commands/test_define_labels.py:148-150` asserts
`actual_names == expected_names` and is **order-sensitive** — insert the new name at the
same index in both `labels.json` and the expected list (i.e. after
`"status-06f-nochange:no-changes-after-retries"`).

`blocked` already exists in `labels.json` as an *ignore* label
(`ignore_labels: ["Overview", "blocked", "wait"]`) meaning "human says don't touch".
`get_matching_ignore_label` matches exactly, so there is no functional collision — leave
`ignore_labels` untouched and keep the display name distinct.

## ALGORITHM

None — declarative config.

## DATA

`internal_id: "implementation_blocked"` is the string Step 5's
`FAILURE_LABELS["blocked"]` resolves to.

## TESTS (write first)

1. `tests/config/test_label_config.py` — add `"implementation_blocked"` to
   `ERROR_STATUS_IDS`. The existing parametrized
   `test_error_statuses_have_vscodeclaude_commands` then asserts
   `commands == ["/check_branch_status"]` for it.
2. `tests/cli/commands/test_define_labels.py` — add
   `"status-06f-blocked:implementation-blocked"` to `expected_names` at the matching index.
3. The existing structural tests (required keys, valid category, unique id/name, 6-char hex
   colour, `vscodeclaude` required keys) cover the rest automatically — no new test needed.

Both test edits should fail before the `labels.json` change and pass after.

## COMMIT

`Add status-06f-blocked:implementation-blocked label`

## LLM PROMPT

```
Read pr_info/steps/summary.md (section 8) and pr_info/steps/step_4.md, then implement
Step 4 only.

This step is config + tests only: define the new implementation_blocked label. Do not
touch any workflow source file — wiring the reason to this label is Step 5.

Work test-first: add the two test entries, watch them fail, then add the labels.json entry.

Two traps:
- tests/cli/commands/test_define_labels.py compares the full name list with == and is
  order-sensitive. Insert at the same index in both places.
- The top-level "color" is a 6-char hex (format-asserted); the nested
  vscodeclaude.color is the string "red". They are different fields.

Leave the existing ignore_labels entry "blocked" alone — it is an unrelated
"human says don't touch" label and matches exactly, so there is no collision.

Use MCP tools for all file operations. When done, run all three checks and fix everything
they report:
  mcp__tools-py__run_pylint_check
  mcp__tools-py__run_mypy_check
  mcp__tools-py__run_pytest_check with
    extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and
    not claude_api_integration and not formatter_integration and not github_integration
    and not langchain_integration"]

Then run ./tools/format_all.sh and make exactly one commit.
```
