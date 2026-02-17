# Step 3: Verify architectural boundary tools

## Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md before starting.

The file move and import updates are complete (steps 1-2).
Now verify that architectural boundary tools still pass, and fix only what breaks.

Tasks:

1. Run tach check (tools/tach_check.bat or `tach check`)
   - If it reports a violation involving `mcp_coder.checks`, add
     `{ path = "mcp_coder.checks" }` to the `depends_on` list of the
     `mcp_coder.cli` module entry in `tach.toml`.
   - If `mcp_coder.workflows` also shows a violation, add it there too.
   - If `tests` module shows a violation, add `{ path = "mcp_coder.checks" }` there too.
   - If tach passes with no changes needed, do not touch tach.toml.

2. Run lint-imports (tools/lint_imports.bat or `lint-imports`)
   - If it reports a layered_architecture violation involving `mcp_coder.checks`,
     add `mcp_coder.checks` to the appropriate layer in the `layered_architecture`
     contract in `.importlinter` (same layer as `mcp_coder.workflow_utils`).
   - If lint-imports passes with no changes needed, do not touch .importlinter.

3. Run the full test suite one final time to confirm everything is green.

Do NOT make any changes unless the tools actually report a violation.
```

---

## WHERE
| File | Change type |
|---|---|
| `tach.toml` | Add `mcp_coder.checks` to depends_on entries (only if tach check fails) |
| `.importlinter` | Add `mcp_coder.checks` to layered contract (only if lint-imports fails) |

## WHAT

### `tach.toml` — conditional addition to `mcp_coder.cli` module:
```toml
[[modules]]
path = "mcp_coder.cli"
layer = "presentation"
depends_on = [
    ...existing entries...
    { path = "mcp_coder.checks" },   # ← add only if tach check reports violation
]
```

Same pattern for `mcp_coder.workflows` and `tests` if they also report violations.

### `.importlinter` — conditional addition to layered_architecture contract:
```ini
[importlinter:contract:layered_architecture]
layers =
    mcp_coder.cli
    mcp_coder.workflows
    mcp_coder.workflow_utils | mcp_coder.checks   # ← add checks at same level as workflow_utils
    mcp_coder.llm | mcp_coder.formatters | mcp_coder.prompt_manager
    mcp_coder.utils | mcp_coder.mcp_code_checker
    mcp_coder.config | mcp_coder.constants
```

## HOW
Both tools use `exact = false` / non-strict mode, so they may pass without changes.
Only edit config files when a tool explicitly reports `mcp_coder.checks` as a violation.

## ALGORITHM
```
run tach check
if violation mentions mcp_coder.checks:
    add { path = "mcp_coder.checks" } to affected module depends_on in tach.toml

run lint-imports
if violation mentions mcp_coder.checks in layered_architecture:
    add mcp_coder.checks at workflow_utils layer in .importlinter

run full pytest suite
assert all tests pass
```

## DATA
No code changes. Config-only edits, and only if tools require them.

## Verification
```
tach check
lint-imports
pytest tests/ -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"
```
All three must pass with zero errors.
