# Step 4: Update All Command Handler Callers

> **Summary**: [pr_info/steps/summary.md](summary.md)
> **Covers**: Propagating Step 2's return type and parameter changes to all callers
> **Depends on**: Step 2

## LLM Prompt

```
Implement Step 4 of issue #528: Update all command handlers that call resolve_llm_method() 
and resolve_mcp_config_path() to use the new signatures from Step 2.

Read pr_info/steps/summary.md for full context, then read this step file for details.

resolve_llm_method() now returns tuple[str, str] instead of str.
resolve_mcp_config_path() now accepts project_dir parameter.

Update 5 command handlers: prompt.py, implement.py, create_plan.py, create_pr.py, check_branch_status.py.
Each needs: provider, _ = resolve_llm_method(...) and passing project_dir to resolve_mcp_config_path().

Update tests first (TDD), then the implementation. Run all three code quality checks after.
```

## WHERE

- **Source**: `src/mcp_coder/cli/commands/prompt.py`
- **Source**: `src/mcp_coder/cli/commands/implement.py`
- **Source**: `src/mcp_coder/cli/commands/create_plan.py`
- **Source**: `src/mcp_coder/cli/commands/create_pr.py`
- **Source**: `src/mcp_coder/cli/commands/check_branch_status.py`
- **Tests**: Corresponding test files in `tests/cli/commands/`

## WHAT

No new functions. Mechanical caller updates only.

## HOW

Each command handler follows the same pattern. Apply this transformation:

```python
# BEFORE:
llm_method = resolve_llm_method(args.llm_method)
provider = parse_llm_method_from_args(llm_method)

# AFTER:
llm_method, _ = resolve_llm_method(args.llm_method)
provider = parse_llm_method_from_args(llm_method)
```

And for `resolve_mcp_config_path()`:

```python
# BEFORE:
mcp_config = resolve_mcp_config_path(getattr(args, "mcp_config", None))

# AFTER:
mcp_config = resolve_mcp_config_path(
    getattr(args, "mcp_config", None),
    project_dir=args.project_dir,
)
```

## ALGORITHM

No new logic — mechanical destructuring at each call site.

```
1. Find resolve_llm_method() call
2. Change `result =` to `result, _ =`
3. Find resolve_mcp_config_path() call
4. Add project_dir=args.project_dir parameter
5. Repeat for each command handler
```

## DATA

No data structure changes. The `provider` variable type is unchanged (`str`) at each call site.

## Test Cases

For each of the 5 command handler test files, update mocks of `resolve_llm_method` to return a tuple:

```python
# BEFORE (in test mocks):
mock_resolve.return_value = "claude"

# AFTER:
mock_resolve.return_value = ("claude", "default")
```

And update mocks of `resolve_mcp_config_path` to accept the new `project_dir` parameter where relevant.

### Files to update:
- `tests/cli/commands/test_prompt.py`
- `tests/cli/commands/test_implement.py`
- `tests/cli/commands/test_create_plan.py`
- `tests/cli/commands/test_create_pr.py`
- `tests/cli/commands/test_check_branch_status.py`
