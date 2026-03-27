# Step 5: CLI flag + command wiring

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step adds the `--from-github` CLI argument and wires it through the
> coordinator commands to the workflow layer.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 5.

Add `--from-github` argument to the vscodeclaude launch subparser in parsers.py.
Wire `args.from_github` through `execute_coordinator_vscodeclaude()` and
`_handle_intervention_mode()` in commands.py. Write tests first (TDD), then
implement. Run all three code quality checks.
```

## Files to Modify

### Tests (write first)

**`tests/cli/commands/coordinator/test_vscodeclaude_cli.py`** — Add tests:

- `test_vscodeclaude_launch_from_github_flag`:
  Parse `["vscodeclaude", "launch", "--from-github"]`. Assert
  `args.from_github is True`.

- `test_vscodeclaude_launch_no_from_github_flag`:
  Parse `["vscodeclaude", "launch"]`. Assert `args.from_github is False`.

- `test_vscodeclaude_launch_from_github_with_repo`:
  Parse `["vscodeclaude", "launch", "--from-github", "--repo", "mcp_coder"]`.
  Assert both `args.from_github is True` and `args.repo == "mcp_coder"`.

**`tests/cli/commands/coordinator/test_commands.py`** — Add tests:

- `test_execute_coordinator_vscodeclaude_passes_from_github`:
  Mock `process_eligible_issues`. Create args with `from_github=True`.
  Call `execute_coordinator_vscodeclaude(args)`.
  Assert `process_eligible_issues` was called with `from_github=True`.

- `test_handle_intervention_mode_passes_from_github`:
  Mock `prepare_and_launch_session`. Create args with `from_github=True`.
  Call `_handle_intervention_mode(args, config)`.
  Assert `prepare_and_launch_session` was called with `from_github=True`.

### Implementation

**`src/mcp_coder/cli/parsers.py`**

- WHERE: `add_vscodeclaude_parsers()`, inside the `launch_parser` section
- WHAT: Add `--from-github` argument
- HOW: Single `add_argument` call

```python
launch_parser.add_argument(
    "--from-github",
    action="store_true",
    help="Install MCP packages from GitHub repos instead of PyPI (latest main)",
)
```

**`src/mcp_coder/cli/commands/coordinator/commands.py`**

- WHERE: `execute_coordinator_vscodeclaude()` and `_handle_intervention_mode()`
- WHAT: Read `args.from_github` and pass to workflow functions
- HOW: Pass as keyword argument

```python
# In execute_coordinator_vscodeclaude():
from_github = getattr(args, "from_github", False)
...
started = process_eligible_issues(
    ...,
    from_github=from_github,
)

# In _handle_intervention_mode():
from_github = getattr(args, "from_github", False)
session = prepare_and_launch_session(
    ...,
    from_github=from_github,
)
```

Note: Use `getattr(args, "from_github", False)` for safety, since the attribute
only exists on the launch subparser.

## Data

- CLI: `--from-github` → `args.from_github: bool` (default `False`)
- Flows to: `process_eligible_issues(from_github=...)` and
  `prepare_and_launch_session(from_github=...)`

## Verification

- `mcp-coder vscodeclaude launch --from-github` parses correctly
- `mcp-coder vscodeclaude launch` still works (default False)
- Flag is correctly passed through to workflow functions
- pylint, mypy, pytest all green
