# Step 1 — E741: rename `l` → `label` in `define_labels.py`

See `pr_info/steps/summary.md` for the overall goal and rationale.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E741"]` and
`extra_args=["--preview"]`. If it does not report **exactly one** `E741`
finding at `src/mcp_coder/cli/commands/define_labels.py` on the line
containing `(l for l in labels_config["workflow_labels"] if l.get("default"))`,
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`src/mcp_coder/cli/commands/define_labels.py`, inside `execute_define_labels`
(around line 582), the `default_label` lookup:

```python
default_label = next(
    (l for l in labels_config["workflow_labels"] if l.get("default")),
    None,
)
```

## WHAT

No function signatures change. Rename the generator-expression loop variable
`l` to `label` in this one `next(...)` call. `l` holds a label dict (a
`workflow_labels` entry), so `label` states what it is.

## HOW

Direct in-place edit of the generator expression — no imports, no decorators,
no call-site changes (the variable is local to the expression).

## ALGORITHM

```
for label in labels_config["workflow_labels"]:
    if label.get("default"):
        yield label
default_label = first result or None
```

## DATA

No change to return values or data structures — `default_label` is still
either a label dict or `None`.

## Test-first note

This is a pure rename of a local variable with no behavioral change, so there
is no new test to write. Verification is: existing tests covering
`execute_define_labels` / the default-label lookup still pass unchanged.

## Steps

1. Edit the generator expression: `(l for l in ... if l.get("default"))` →
   `(label for label in ... if label.get("default"))`.
2. Run `mcp__mcp-tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`.
3. Run `mcp__mcp-tools-py__run_pylint_check` and `mcp__mcp-tools-py__run_mypy_check`.
4. Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E741"]`,
   `extra_args=["--preview"]` — must report 0 findings in this file.
5. Run `mcp__mcp-tools-py__run_format_code`.
6. Commit: `fix(lint): rename ambiguous l to label in define_labels.py`.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_1.md`: rename the ambiguous loop variable `l` to
> `label` in the `default_label` lookup in
> `src/mcp_coder/cli/commands/define_labels.py`. Follow the precondition
> check first — if it fails, write one line to `pr_info/.blocked.txt` and
> stop. Otherwise make the rename, run the checks listed in the step, format
> the code, and produce exactly one commit with the given message.
