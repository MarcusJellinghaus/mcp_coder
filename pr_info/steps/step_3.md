# Step 3: Verify architectural boundary tools

## Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md before starting.

The file move and import updates are complete (steps 1-2).
Now update the architectural boundary config files and verify all tools pass.

Tasks:

1. Update `tach.toml` — these changes are required:
   - Add `"tools"` to the `layers` list between `"application"` and `"domain"`.
   - Add a new `[[modules]]` entry for `mcp_coder.checks` at the `tools` layer
     with depends_on = [workflow_utils, utils, config, constants].
   - Add `{ path = "mcp_coder.checks" }` to the `depends_on` list of `mcp_coder.cli`.
   - Add `{ path = "mcp_coder.checks" }` to the `depends_on` list of `mcp_coder.workflows`.
   - Add `{ path = "mcp_coder.checks" }` to the `depends_on` list of `tests`.
   - Then run `tach check` to verify no violations remain.

2. Update `.importlinter` — these changes are required:
   - In the `layered_architecture` contract, insert `mcp_coder.checks` as a new
     layer between `mcp_coder.workflows` and `mcp_coder.workflow_utils`.
   - Add `tests.checks` to the `test_module_independence` contract.
   - Then run `lint-imports` to verify no violations remain.

3. Run the full test suite one final time to confirm everything is green.
```

---

## WHERE
| File | Change type |
|---|---|
| `tach.toml` | Add `tools` layer; add `[[modules]]` entry for `mcp_coder.checks`; update `depends_on` for `cli`, `workflows`, `tests` |
| `.importlinter` | Insert `mcp_coder.checks` as new layer; add `tests.checks` to independence contract |

## WHAT

### `tach.toml` — required changes:

Add `"tools"` to the `layers` list (between `"application"` and `"domain"`):
```toml
layers = [
    "presentation",
    "application",
    "tools",           # ← new: high-level modules backing CLI subcommands
    "domain",
    "infrastructure",
    "foundation"
]
```

Add a new `[[modules]]` entry for `mcp_coder.checks`:
```toml
[[modules]]
path = "mcp_coder.checks"
layer = "tools"
# High-level check modules backing CLI subcommands. Reusable by cli and workflows.
depends_on = [
    { path = "mcp_coder.workflow_utils" },
    { path = "mcp_coder.utils" },
    { path = "mcp_coder.config" },
    { path = "mcp_coder.constants" },
]
```

Add `{ path = "mcp_coder.checks" }` to the `depends_on` lists of `mcp_coder.cli`,
`mcp_coder.workflows`, and `tests`.

### `.importlinter` — required changes:

Insert `mcp_coder.checks` as a new layer between `mcp_coder.workflows` and
`mcp_coder.workflow_utils` in the `layered_architecture` contract:
```ini
[importlinter:contract:layered_architecture]
layers =
    mcp_coder.cli
    mcp_coder.workflows
    mcp_coder.checks          # ← new layer: below workflows, above workflow_utils
    mcp_coder.workflow_utils
    mcp_coder.llm | mcp_coder.formatters | mcp_coder.prompt_manager
    mcp_coder.utils | mcp_coder.mcp_code_checker
    mcp_coder.config | mcp_coder.constants
```

Add `tests.checks` to the `test_module_independence` contract:
```ini
[importlinter:contract:test_module_independence]
modules =
    tests.cli
    tests.llm
    tests.utils
    tests.workflows
    tests.formatters
    tests.workflow_utils
    tests.checks              # ← add this
```

## HOW
Both config files require updates after the move — `mcp_coder.checks` is not registered
in either `tach.toml` or `.importlinter` today. Apply the changes described above, then
run the tools to verify no violations remain.

The `tools` layer sits between `application` (workflows) and `domain` (llm/formatters)
in tach, reflecting that `mcp_coder.checks` is a high-level module that:
- Is consumed by both `cli` and `workflows` (layers above)
- Imports from `workflow_utils` and `utils` (layers below)

## ALGORITHM
```
# tach.toml
add "tools" to layers list
add [[modules]] entry for mcp_coder.checks at tools layer
add { path = "mcp_coder.checks" } to depends_on for cli, workflows, tests
run tach check → assert passes

# .importlinter
insert mcp_coder.checks layer between workflows and workflow_utils
add tests.checks to test_module_independence contract
run lint-imports → assert passes

run full pytest suite
assert all tests pass
```

## DATA
No code changes. Config-only edits.

## Verification
```
tach check
lint-imports
pytest tests/ -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"
```
All three must pass with zero errors.
