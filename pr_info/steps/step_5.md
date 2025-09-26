# Step 5: Refactor execute_prompt to CLI Wrapper

## Goal
Convert `execute_prompt` into a lightweight CLI wrapper that maps argparse.Namespace parameters to the new `prompt_claude` function.

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Modify existing `execute_prompt` function

## WHAT
Replace business logic with parameter mapping and function call:

### New Implementation
```python
def execute_prompt(args: argparse.Namespace) -> int:
    """Execute prompt command to ask Claude a question (CLI wrapper)."""
    return prompt_claude(
        prompt=args.prompt,
        verbosity=getattr(args, "verbosity", "just-text"),
        timeout=getattr(args, "timeout", 30),
        store_response=getattr(args, "store_response", False),
        continue_from=getattr(args, "continue_from", None),
        continue_latest=getattr(args, "continue", False),
        save_conversation_md=getattr(args, "save_conversation_md", None),
        save_conversation_full_json=getattr(args, "save_conversation_full_json", None)
    )
```

## HOW
- **Replace Logic**: Remove all business logic from `execute_prompt`
- **Parameter Mapping**: Use `getattr()` for optional CLI parameters  
- **Preserve Interface**: Maintain same function signature for CLI compatibility

## ALGORITHM
```
1. Extract prompt from args.prompt (required)
2. Use getattr() to extract optional parameters with defaults
3. Map args.continue to continue_latest parameter
4. Call prompt_claude with all mapped parameters
5. Return result directly
```

## DATA

### Parameter Mapping
| CLI Argument | Function Parameter | Default | Extraction |
|--------------|-------------------|---------|------------|
| `args.prompt` | `prompt` | N/A | `args.prompt` |
| `args.verbosity` | `verbosity` | `"just-text"` | `getattr(args, "verbosity", "just-text")` |
| `args.timeout` | `timeout` | `30` | `getattr(args, "timeout", 30)` |
| `args.store_response` | `store_response` | `False` | `getattr(args, "store_response", False)` |
| `args.continue_from` | `continue_from` | `None` | `getattr(args, "continue_from", None)` |
| `args.continue` | `continue_latest` | `False` | `getattr(args, "continue", False)` |

## Implementation Notes
- Remove all existing business logic from `execute_prompt`
- Update docstring to reflect new role as CLI wrapper
- Maintain backward compatibility with existing CLI usage
- All existing tests should still pass

## LLM Prompt for Implementation

```
Please implement Step 5 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Replace the business logic in execute_prompt with a simple CLI wrapper that calls prompt_claude.

The refactored function should:
1. Keep same signature: execute_prompt(args: argparse.Namespace) -> int
2. Extract parameters from args using getattr() with defaults
3. Map args.continue to continue_latest parameter
4. Call prompt_claude with all mapped parameters
5. Return the result directly

Parameter mapping:
- prompt=args.prompt
- verbosity=getattr(args, "verbosity", "just-text")
- timeout=getattr(args, "timeout", 30)
- store_response=getattr(args, "store_response", False)
- continue_from=getattr(args, "continue_from", None)
- continue_latest=getattr(args, "continue", False)
- save_conversation_md=getattr(args, "save_conversation_md", None)
- save_conversation_full_json=getattr(args, "save_conversation_full_json", None)

Update the docstring to reflect the new role as a CLI wrapper. All existing tests should continue to pass.
```
