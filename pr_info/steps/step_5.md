# Step 5 — Coordinator dispatch wiring

See [summary.md](./summary.md) for full context. Depends on Step 4 (the
`fix-ci` CLI verb must exist for the templates to invoke it) and Step 1
(the `status-81`/`status-82`/`status-83` label names used in the mapping
and templates).

## WHERE

- `src/mcp_coder/cli/commands/coordinator/workflow_constants.py` (modify)
- `src/mcp_coder/cli/commands/coordinator/command_templates.py` (modify)
- `src/mcp_coder/cli/commands/coordinator/__init__.py` (modify)
- `tests/cli/commands/coordinator/test_command_templates.py` (modify)

## WHAT

No new functions — two new module-level string constants plus two
dict-entry additions:

```python
# command_templates.py
FIX_CI_COMMAND_TEMPLATE: str = "..."    # Linux
FIX_CI_COMMAND_WINDOWS: str = r"..."    # Windows
```

## HOW

- `workflow_constants.py`: add to `WORKFLOW_MAPPING`, right after the
  existing `"status-71:merge-conflict"` entry:
  ```python
  "status-81:failing-ci": {
      "workflow": "fix-ci",
      "branch_strategy": "from_issue",
      "next_label": "status-82:fixing-ci",
  },
  ```
- `command_templates.py`: `FIX_CI_COMMAND_TEMPLATE` is
  `IMPLEMENT_COMMAND_TEMPLATE` verbatim with `implement` → `fix-ci` and the
  watchdog line changed to
  `mcp-coder gh-tool set-status status-83:ci-fix-failed --from-status status-82:fixing-ci --project-dir /workspace/repo --force || true`.
  `FIX_CI_COMMAND_WINDOWS` is `IMPLEMENT_COMMAND_WINDOWS` verbatim with the
  same two substitutions (windows watchdog line drops `|| true`, matching
  the existing Windows convention). Both keep `--mcp-config .mcp.json` and
  the `claude --version` check (CI fixing calls the LLM, unlike
  `fix-conflict`). Add one `WORKFLOW_TEMPLATES` entry:
  ```python
  "fix-ci": (FIX_CI_COMMAND_TEMPLATE, FIX_CI_COMMAND_WINDOWS),
  ```
- `coordinator/__init__.py`: add `FIX_CI_COMMAND_TEMPLATE` and
  `FIX_CI_COMMAND_WINDOWS` to both the `from .command_templates import (...)`
  block and the `__all__` list, next to the `FIX_CONFLICT_COMMAND_*` entries.

Do **not** add `"status-81:failing-ci"` to `PRIORITY_ORDER` —
`"status-71:merge-conflict"` isn't in it either; both fall through to the
lowest-priority default, which is the existing, accepted behavior this
mirrors.

## ALGORITHM

N/A — pure data/config; `coordinator/core.py`'s existing data-driven
`dispatch_workflow` (template lookup by `workflow_config["workflow"]`, see
`WORKFLOW_TEMPLATES[workflow_config["workflow"]]`) needs no changes.

## DATA

N/A (constants only).

## Test-first steps

In `tests/cli/commands/coordinator/test_command_templates.py`:
1. Add `WORKFLOW_TEMPLATES["fix-ci"] == (FIX_CI_COMMAND_TEMPLATE, FIX_CI_COMMAND_WINDOWS)`
   to `test_templates_map_to_expected_constants` (new assertion, plus the
   import of both constants at the top of the test module).
2. `test_every_mapping_workflow_has_template` and
   `test_all_templates_format_uniformly_with_all_kwargs` already iterate
   `WORKFLOW_MAPPING`/`WORKFLOW_TEMPLATES` generically — no new test needed,
   but confirm both pass after the change (they'll fail first since
   `"fix-ci"` is referenced in the new assertion but the constant doesn't
   exist yet).

Run — confirm red (import error). Implement the changes above. Re-run —
confirm green.

## Checks

`run_pytest_check`, `run_pylint_check`, `run_mypy_check` — all pass. Then
`run_format_code`, then commit.

## Commit

One commit: `feat(coordinator): dispatch status-81:failing-ci to fix-ci`.

## LLM Prompt

> Implement Step 5 of the plan in `pr_info/steps/summary.md`. Read that
> summary first, then follow `pr_info/steps/step_5.md` exactly: update
> `tests/cli/commands/coordinator/test_command_templates.py` first (red),
> then add the `WORKFLOW_MAPPING` entry, the `FIX_CI_COMMAND_TEMPLATE`/
> `FIX_CI_COMMAND_WINDOWS` constants, the `WORKFLOW_TEMPLATES` entry, and
> the `coordinator/__init__.py` exports exactly as specified (green). Run
> pytest/pylint/mypy, format, and produce exactly one commit.
