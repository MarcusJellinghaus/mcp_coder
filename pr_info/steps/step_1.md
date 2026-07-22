# Step 1 — Scaffold the `workflow_steps` layer

**Goal:** Create the empty `mcp_coder.workflow_steps` package and register it in both
architectural enforcers, so later steps can move code into it without a RED contract.
No workflow code moves yet.

## WHERE

Create:
- `src/mcp_coder/workflow_steps/__init__.py` (empty package docstring only)
- `src/mcp_coder/workflow_steps/py.typed` (empty file; mirrors `workflow_utils/py.typed`)
- `tests/workflow_steps/__init__.py`
- `tests/workflow_steps/test_scaffold.py`

Modify:
- `.importlinter`
- `tach.toml`

## WHAT

No functions. This step is package scaffolding + config edits.

## HOW (config edits)

**`.importlinter` → `[importlinter:contract:layered_architecture]` `layers`:** insert a
new line between `mcp_coder.workflows` and `mcp_coder.services | mcp_coder.checks`:

```
    mcp_coder.workflows
    mcp_coder.workflow_steps          # <-- NEW
    mcp_coder.services | mcp_coder.checks
```

**`.importlinter` → `[importlinter:contract:test_module_independence]` `modules`:** add
`    tests.workflow_steps`.

**`tach.toml` → new `[[modules]]` (place in the APPLICATION layer section):**

```toml
[[modules]]
path = "mcp_coder.workflow_steps"
layer = "application"
depends_on = [
    { path = "mcp_coder.checks" },
    { path = "mcp_coder.workflow_utils" },
    { path = "mcp_coder.llm" },
    { path = "mcp_coder.prompt_manager" },
    { path = "mcp_coder.mcp_tools_py" },
    { path = "mcp_coder.mcp_workspace_git" },
    { path = "mcp_coder.mcp_workspace_github" },
    { path = "mcp_coder.utils" },
    { path = "mcp_coder.constants" },
]
```

**`tach.toml` → `mcp_coder.workflows` `depends_on`:** add `{ path = "mcp_coder.workflow_steps" }`.
**`tach.toml` → `tests` `depends_on`:** add `{ path = "mcp_coder.workflow_steps" }`.

## ALGORITHM

None (declarative config + empty package).

## DATA

`src/mcp_coder/workflow_steps/__init__.py`:
```python
"""Shared, workflow-agnostic composed steps (the middle tier between
workflows and workflow_utils/checks primitives)."""
```

## TDD

Write `tests/workflow_steps/test_scaffold.py` first:
- `test_package_importable` — `import mcp_coder.workflow_steps` succeeds.
- `test_py_typed_present` — `importlib.resources`/path check that `py.typed` exists
  next to `__init__.py`.

Then create the package files so the tests pass.

## Checks / commit

Run `run_lint_imports_check` and `run_tach_check` (both must confirm the new layer is
recognized and green) plus pylint / pytest / mypy. One commit:
`refactor(workflow_steps): scaffold workflow_steps layer + register enforcers`.

## LLM prompt

> Read `pr_info/steps/summary.md` (sections "A new middle tier" and "Dual boundary
> enforcement") and `pr_info/steps/step_1.md`. Create the empty
> `mcp_coder.workflow_steps` package with `__init__.py` and `py.typed`, create the
> `tests/workflow_steps/` package with the scaffold tests described, and register the
> new layer in **both** `.importlinter` (add the layer between `workflows` and
> `services | checks`, and add `tests.workflow_steps` to the test-independence
> contract) and `tach.toml` (new `[[modules]]` entry in the application layer with the
> exact `depends_on` list, plus add `workflow_steps` to the `workflows` and `tests`
> `depends_on`). Do not move any workflow code. Verify `run_lint_imports_check`,
> `run_tach_check`, pylint, pytest, and mypy are all green, then produce one commit.
