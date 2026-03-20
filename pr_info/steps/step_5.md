# Step 5: CLI Command Consistency — Verify and Commit Auto

> **Summary**: [pr_info/steps/summary.md](summary.md)
> **Covers**: Sub-task 8 (CLI command consistency fixes)
> **Depends on**: Step 2 (resolve_llm_method return type)

## LLM Prompt

```
Implement Step 5 of issue #528: CLI command consistency fixes for verify and commit auto.

Read pr_info/steps/summary.md for full context, then read this step file for details.

Two command changes:
1. verify.py — add --llm-method support, delete _resolve_active_provider(), use shared resolve_llm_method()
2. commit.py — remove --mcp-config handling, add explanatory comment
Also update parsers.py for both commands.

Update tests first (TDD), then the implementation. Run all three code quality checks after.
```

## WHERE

- **Source**: `src/mcp_coder/cli/commands/verify.py`
- **Source**: `src/mcp_coder/cli/commands/commit.py`
- **Source**: `src/mcp_coder/cli/parsers.py` (already touched in Step 3 for help text)
- **Tests**: `tests/cli/commands/test_verify.py` and related verify test files
- **Tests**: `tests/cli/commands/test_commit.py`

## WHAT

### verify.py changes

**Delete**: `_resolve_active_provider()` function and `_VALID_PROVIDERS` constant.

**Modify**: `execute_verify()` to use shared function:

```python
# BEFORE:
active_provider, source = _resolve_active_provider()

# AFTER:
from ..utils import resolve_llm_method
active_provider, source = resolve_llm_method(getattr(args, "llm_method", None))
```

**Remove import**: `os` (no longer needed after deleting `_resolve_active_provider()`)
**Remove import**: `get_config_values` (no longer needed)

### commit.py changes

**Remove**: `resolve_mcp_config_path` import and any `mcp_config` usage.

**Modify**: `execute_commit_auto()`:

```python
# BEFORE:
llm_method = resolve_llm_method(args.llm_method)

# AFTER:
llm_method, _ = resolve_llm_method(args.llm_method)
# Commit message generation is text-in/text-out — no MCP tools needed.
```

### parsers.py changes (commit auto)

```python
# REMOVE from auto_parser:
auto_parser.add_argument(
    "--mcp-config",
    type=str,
    default=None,
    help="Path to MCP configuration file (e.g., .mcp.linux.json)",
)
```

### parsers.py changes (verify)

```python
# ADD to verify_parser:
verify_parser.add_argument(
    "--llm-method",
    choices=["claude", "langchain"],
    default=None,
    metavar="METHOD",
    help="LLM method override. If omitted, uses config default_provider or claude",
)
```

## HOW

`verify.py` removes its private `_resolve_active_provider()` and imports the shared `resolve_llm_method()` from `..utils`. Since `resolve_llm_method()` now returns `(provider, source)`, the existing `active_provider, source = ...` destructuring works as-is.

## ALGORITHM — verify change

```
1. Delete _resolve_active_provider() and _VALID_PROVIDERS
2. Import resolve_llm_method from ..utils (add to existing import)
3. Replace call: active_provider, source = resolve_llm_method(args.llm_method)
4. Remove unused imports (os, get_config_values)
```

## ALGORITHM — commit auto change

```
1. Remove resolve_mcp_config_path from imports
2. Change resolve_llm_method call to destructure tuple
3. Remove the "mcp_config support" TODO comment
4. Add comment explaining why no MCP needed
```

## DATA

No data structure changes.

## Test Cases

### `tests/cli/commands/test_verify.py` (and related)

1. `test_verify_uses_llm_method_arg` — pass `--llm-method langchain`, verify it's used as active provider
2. `test_verify_defaults_to_config` — no `--llm-method`, mock config `default_provider = langchain`, verify
3. `test_verify_defaults_to_claude` — no arg, no config → claude
4. Update existing tests that mock `_resolve_active_provider` to mock `resolve_llm_method` instead

### `tests/cli/commands/test_commit.py`

1. `test_commit_auto_no_mcp_config_arg` — verify `--mcp-config` is not accepted (argparse error)
2. Update existing tests: mock `resolve_llm_method` to return tuple
