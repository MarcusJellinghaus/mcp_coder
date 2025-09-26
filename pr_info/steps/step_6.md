# Step 6: Refactor execute_prompt to CLI Wrapper

## Goal
Convert the existing `execute_prompt` function into a lightweight CLI wrapper that maps argparse.Namespace parameters to the new `prompt_claude` function.

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Modify existing `execute_prompt` function

## WHAT
Transform `execute_prompt` into a simple wrapper:

### New Function Implementation
```python
def execute_prompt(args: argparse.Namespace) -> int:
    """Execute prompt command to ask Claude a question (CLI wrapper).
    
    This function handles the conversion from argparse.Namespace to explicit
    parameters and calls the core prompt_claude function.
    """
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
1. Extract prompt from args.prompt (required parameter)
2. Use getattr() to extract optional parameters with defaults
3. Map continue flag to continue_latest parameter
4. Call prompt_claude with all mapped parameters
5. Return result code directly from prompt_claude
```

## DATA

### Parameter Mapping Table
| CLI Argument | Function Parameter | Default Value | Extraction Method |
|--------------|-------------------|---------------|-------------------|
| `args.prompt` | `prompt` | N/A (required) | `args.prompt` |
| `args.verbosity` | `verbosity` | `"just-text"` | `getattr(args, "verbosity", "just-text")` |
| `args.timeout` | `timeout` | `30` | `getattr(args, "timeout", 30)` |
| `args.store_response` | `store_response` | `False` | `getattr(args, "store_response", False)` |
| `args.continue_from` | `continue_from` | `None` | `getattr(args, "continue_from", None)` |
| `args.continue` | `continue_latest` | `False` | `getattr(args, "continue", False)` |
| `args.save_conversation_md` | `save_conversation_md` | `None` | `getattr(args, "save_conversation_md", None)` |
| `args.save_conversation_full_json` | `save_conversation_full_json` | `None` | `getattr(args, "save_conversation_full_json", None)` |

### Return Value
- **Direct pass-through**: Return value from `prompt_claude()`
- **No additional processing**: CLI wrapper adds no extra logic

## Implementation Notes
- Remove all existing business logic from `execute_prompt`
- Preserve the original function signature and docstring intent
- Update docstring to reflect new role as CLI wrapper
- Maintain backward compatibility with existing CLI usage

## LLM Prompt for Implementation

```
Please implement Step 6 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Refactor the existing execute_prompt function in src/mcp_coder/cli/commands/prompt.py to become a simple CLI wrapper.

Replace all the current business logic with a single call to prompt_claude(), mapping the argparse.Namespace parameters appropriately.

The refactored function should:
1. Keep the same signature: execute_prompt(args: argparse.Namespace) -> int
2. Extract parameters from args using getattr() with appropriate defaults
3. Map args.continue to continue_latest parameter for prompt_claude
4. Call prompt_claude with all mapped parameters
5. Return the result directly from prompt_claude

Use these parameter mappings:
- prompt=args.prompt
- verbosity=getattr(args, "verbosity", "just-text")  
- timeout=getattr(args, "timeout", 30)
- store_response=getattr(args, "store_response", False)
- continue_from=getattr(args, "continue_from", None)
- continue_latest=getattr(args, "continue", False)
- save_conversation_md=getattr(args, "save_conversation_md", None)
- save_conversation_full_json=getattr(args, "save_conversation_full_json", None)

Update the docstring to reflect the function's new role as a CLI wrapper.
```
