# Step 5: Update CLI layer — replace flag, wire through commands

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

Replace `--install-from-github` with `--no-install-from-github` in the CLI parser. Wire the new flag through `commands.py` as `skip_github_install`.

## LLM Prompt
> Implement Step 5 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_5.md`). Replace `--install-from-github` with `--no-install-from-github` in parsers.py. Update commands.py to read the new flag and pass as `skip_github_install`. Update tests first (TDD), then source. Run all three code quality checks.

## WHERE
- `src/mcp_coder/cli/parsers.py`
- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`
- `tests/cli/commands/coordinator/test_commands.py`

## WHAT

### `parsers.py` — `add_vscodeclaude_parsers()`

Replace:
```python
launch_parser.add_argument(
    "--install-from-github",
    action="store_true",
    help="Install MCP packages from GitHub repos instead of PyPI (latest main)",
)
```

With:
```python
launch_parser.add_argument(
    "--no-install-from-github",
    action="store_true",
    help="Skip installing packages from GitHub even when configured in pyproject.toml",
)
```

### `commands.py` — `execute_coordinator_vscodeclaude()`

The call-site kwargs were already renamed from `install_from_github=` to `skip_github_install=` in Step 3. Now rename the variable itself:

Replace:
```python
install_from_github = getattr(args, "install_from_github", False)
```

With:
```python
skip_github_install = getattr(args, "no_install_from_github", False)
```

The `skip_github_install=skip_github_install` call to `process_eligible_issues()` is already correct from Step 3 (it was `skip_github_install=install_from_github` — now update to `skip_github_install=skip_github_install`).

### `commands.py` — `_handle_intervention_mode()`

Same as above — the kwarg was already renamed in Step 3. Now rename the variable:

Replace:
```python
install_from_github = getattr(args, "install_from_github", False)
```

With:
```python
skip_github_install = getattr(args, "no_install_from_github", False)
```

The `skip_github_install=skip_github_install` call to `prepare_and_launch_session()` is already correct from Step 3.

## ALGORITHM
```
1. CLI parses --no-install-from-github → args.no_install_from_github (bool)
2. commands.py reads it as skip_github_install
3. Passes skip_github_install to process_eligible_issues / prepare_and_launch_session
4. These pass it to create_startup_script (from step 3)
5. create_startup_script skips _build_github_install_section if True (from step 2)
```

## Test changes

### `test_vscodeclaude_cli.py`
Three existing tests at lines 336-365 reference `--install-from-github` / `install_from_github`. Update all three to use `--no-install-from-github` / `no_install_from_github` and adjust assertions to match the new opt-out semantics.

### `test_commands.py`
This file has ~9 references that test `install_from_github` parameter threading through `process_eligible_issues()` and `_handle_intervention_mode()`. Update these to use `skip_github_install` / `no_install_from_github` to match the renamed parameter and new CLI flag. Key changes:
- Replace `install_from_github=` keyword args with `skip_github_install=`
- Update mock assertions that verify the parameter is passed through
- Update `getattr(args, "install_from_github", ...)` references to `getattr(args, "no_install_from_github", ...)`

## Commit message
```
fix(vscodeclaude): replace --install-from-github with --no-install-from-github (#885)

GitHub packages are now auto-detected from pyproject.toml.
The new --no-install-from-github flag is an opt-out escape hatch
that skips GitHub installs even when configured.
```
