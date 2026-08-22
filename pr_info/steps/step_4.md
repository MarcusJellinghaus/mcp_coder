# Step 4 — `status-06f-blocked:implementation-blocked` label

Config + tests only. Must land **before** Step 5, which maps a failure reason onto this
label's `internal_id`.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/config/labels.json` | new entry in `workflow_labels` |
| `tests/config/test_label_config.py` | add to `ERROR_STATUS_IDS` (`:176`) |
| `tests/cli/commands/test_define_labels.py` | add to `expected_names` (`:128` area) **and bump the label count `36` → `37` (`:69-72`)** |
| `tests/cli/commands/test_define_labels_label_changes.py` | bump the three derived counts `35` → `36` (`:308`, `:311`, `:366`) |
| `tests/workflows/vscodeclaude/test_types.py` | bump the human_action count `26` → `27` (`:309`) |

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

The same file also hard-asserts the label **count** at `:69-72`:

```python
assert (
    len(labels_config["workflow_labels"]) == 36
), "Config should contain exactly 36 workflow labels"
```

Bump both the number and the message to `37`. Missing this leaves Step 4 red even though
the name list matches.

**Two further test files carry counts derived from the bundled config, and break the same
way.** Both build their expectations from the real `labels.json`, so a 37th label shifts
them by one:

- `tests/cli/commands/test_define_labels_label_changes.py:308,311,366` —
  `assert len(result["created"]) == 35  # 35 new labels (36 total - 1 existing)` and
  `assert mock_labels_manager.create_label.call_count == 35` in
  `test_apply_labels_success_flow`, plus a third `assert len(result["created"]) == 35` in
  `test_apply_labels_dry_run_mode` at `:366`. All three become `36`; update the trailing
  comment's arithmetic at `:308` to `37 total - 1 existing` too. Both tests build their
  expectation from the real `labels.json` via the `labels_config_path` fixture
  (`tests/conftest.py`), so both break.
- `tests/workflows/vscodeclaude/test_types.py:309` —
  `assert len(human_action_labels) == 26`. The new label is `category: human_action`, so
  this becomes `27`.

Neither file is mentioned in the issue's "five places to touch"; both fail immediately
without the bump.

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
   `"status-06f-blocked:implementation-blocked"` to `expected_names` at the matching index,
   **and** change the count assertion at `:69-72` from `36` to `37` (message text too).
3. `tests/cli/commands/test_define_labels_label_changes.py` — change `35` to `36` at all
   three sites: `:308`, `:311` (and the inline comment's arithmetic) and `:366`.
4. `tests/workflows/vscodeclaude/test_types.py` — change `26` to `27` at `:309`.
5. The existing structural tests (required keys, valid category, unique id/name, 6-char hex
   colour, `vscodeclaude` required keys) cover the rest automatically — no new test needed.

All four test edits should fail before the `labels.json` change and pass after.

## COMMIT

`Add status-06f-blocked:implementation-blocked label`

## LLM PROMPT

```
Read pr_info/steps/summary.md (section 8) and pr_info/steps/step_4.md, then implement
Step 4 only.

This step is config + tests only: define the new implementation_blocked label. Do not
touch any workflow source file — wiring the reason to this label is Step 5.

Work test-first: add the four test entries, watch them fail, then add the labels.json entry.

Traps:
- tests/cli/commands/test_define_labels.py compares the full name list with == and is
  order-sensitive. Insert at the same index in both places.
- The same file also asserts len(workflow_labels) == 36 at lines 69-72. Bump it to 37
  (and the assertion message with it), or the step lands red.
- Four more hard-coded counts derive from the bundled labels.json and break the same way:
  tests/cli/commands/test_define_labels_label_changes.py:308, :311 and :366 (35 -> 36,
  plus the inline comment's arithmetic at :308 — :366 is a third occurrence in
  test_apply_labels_dry_run_mode, easy to miss) and
  tests/workflows/vscodeclaude/test_types.py:309 (26 -> 27, because the new label is
  category: human_action).
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
