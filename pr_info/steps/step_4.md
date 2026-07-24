# Step 4 — Refactor coordinator dispatch to data-driven `WORKFLOW_TEMPLATES` (pure refactor)

**Read `pr_info/steps/summary.md` first** (§3 Data-driven coordinator dispatch). This is a
**behavior-preserving refactor** of the existing 3 workflows. It replaces the two mirrored
`if/elif/else` template selectors in `dispatch_workflow` with a lookup table, so Step 5 can add
review workflows as one-line dict entries and the silent-fallthrough failure mode is removed
structurally. No new workflow is added here. Existing dispatch tests guard equivalence.

## WHERE
- Modify `src/mcp_coder/cli/commands/coordinator/command_templates.py` — add `WORKFLOW_TEMPLATES`.
- Modify `src/mcp_coder/cli/commands/coordinator/core.py` — replace the `core.py:434-461` selector
  block; update the import from `command_templates` to bring in `WORKFLOW_TEMPLATES`.
- Modify `src/mcp_coder/cli/commands/coordinator/__init__.py` — export `WORKFLOW_TEMPLATES`.
- Add coverage in `tests/cli/commands/coordinator/test_command_templates.py` (or `test_core.py`).

## WHAT
```python
# command_templates.py
WORKFLOW_TEMPLATES: dict[str, tuple[str, str]] = {
    # workflow name -> (linux_template, windows_template)
    "create-plan": (CREATE_PLAN_COMMAND_TEMPLATE, CREATE_PLAN_COMMAND_WINDOWS),
    "implement":   (IMPLEMENT_COMMAND_TEMPLATE,  IMPLEMENT_COMMAND_WINDOWS),
    "create-pr":   (CREATE_PR_COMMAND_TEMPLATE,  CREATE_PR_COMMAND_WINDOWS),
}
```

## HOW
- In `core.py`, import `WORKFLOW_TEMPLATES` (drop the now-unused individual template imports if
  they are only used by the selector; keep any still referenced).
- **The individual template constants must stay importable.** Even when `core.py` stops importing
  `CREATE_PLAN_COMMAND_TEMPLATE` / `IMPLEMENT_COMMAND_TEMPLATE` / `CREATE_PR_COMMAND_TEMPLATE` (+ the
  `*_WINDOWS` variants), they must remain module-level constants in `command_templates.py` **and**
  stay re-exported in `coordinator/__init__.py`'s `__all__`, because existing tests import them from
  there. The refactor must not break those imports (`vulture` won't flag them since
  `WORKFLOW_TEMPLATES` still references each).
- `str.format()` ignores extra kwargs, so pass `log_level`, `issue_number`, and `branch_name`
  uniformly. `branch_name` is already bound on every path before the selector (`"main"` for the
  create-plan strategy).

## ALGORITHM (replaces lines 431-461)
```
executor_os = repo_config.get("executor_os", "linux")
linux_tpl, windows_tpl = WORKFLOW_TEMPLATES[workflow_config["workflow"]]
template = windows_tpl if executor_os == "windows" else linux_tpl
command = template.format(
    log_level=log_level, issue_number=issue["number"], branch_name=branch_name
)
```

## DATA
- `WORKFLOW_TEMPLATES`: `dict[str, tuple[str, str]]` keyed by workflow name.
- `command`: formatted `str` (identical output to the previous if/elif for all 3 workflows).

## TESTS
1. Existing `test_core.py` dispatch tests must still pass unchanged (equivalence proof).
2. New invariant test: every `workflow` value in `WORKFLOW_MAPPING` has a `WORKFLOW_TEMPLATES` key
   (`{c["workflow"] for c in WORKFLOW_MAPPING.values()} <= set(WORKFLOW_TEMPLATES)`).
3. Optional: assert `WORKFLOW_TEMPLATES["create-plan"][0]` is `CREATE_PLAN_COMMAND_TEMPLATE`, etc.

## Commit
One commit: refactor + dict + export + coverage. Run pylint, pytest (`-n auto` unit exclusion),
mypy, `lint-imports`, `vulture` (ensure no template constant became dead — they remain referenced
via `WORKFLOW_TEMPLATES`).
