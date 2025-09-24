# Step 2: Replace Print Statements with Structured Logging

## Objective
Replace all `print()` statements in `workflows/implement.py` with proper logging calls while maintaining the same visual output format and behavior.

## WHERE
- **File**: `workflows/implement.py`
- **Functions to Modify**: `log_step()`, `check_prerequisites()`, `get_next_task()`, `save_conversation()`, `run_formatters()`, `commit_changes()`, `push_changes()`, `process_single_task()`

## WHAT
### Main Functions with Signatures
```python
def log_step(message: str) -> None:
    """Log step with structured logging instead of print."""  # Modified internal implementation
    
# All other function signatures remain UNCHANGED
```

### Manual Verification
- Run workflow and verify same visual output with timestamps
- Run `python workflows/implement.py --log-level DEBUG` for detailed output
- Test error scenarios to ensure logger.error calls work correctly

## HOW
### Integration Points
- **Import**: `import logging`
- **Add**: `logger = logging.getLogger(__name__)` after imports
- **Modify**: Internal implementation of `log_step()` function only
- **Replace**: All `print(f"Error: ...")` → `logger.error(...)`

### Logging Level Mapping
- Error messages → `logger.error()`
- Progress/status messages → `logger.info()` 
- The `log_step()` function → `logger.info()` internally

## ALGORITHM
```
1. Add logger = logging.getLogger(__name__) after imports
2. Replace log_step() print() with logger.info(message)
3. Find all print(f"Error: ...") statements
4. Replace with logger.error(...) calls
5. Remove timestamp formatting from log_step (handled by logging system)
6. Preserve all message content and logic flow
```

## DATA
### Modified Functions Internal Changes
```python
# Before
def log_step(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# After  
def log_step(message: str) -> None:
    logger.info(message)
```

### Print Statement Replacements
```python
# Error cases: print(f"Error: ...") → logger.error("...")
# No return value changes - all functions maintain existing signatures
```

## LLM Prompt for Implementation

```
Based on the summary in pr_info/steps/summary.md, implement Step 2: Replace print statements with structured logging in workflows/implement.py.

REQUIREMENTS:
1. Add logger = logging.getLogger(__name__) after imports
2. Modify log_step() function to use logger.info() instead of print()
3. Replace all print(f"Error: ...") with logger.error(...) 
4. Keep ALL function signatures unchanged
5. Preserve exact message content and workflow logic
6. Use standard logging format (let logging system handle timestamps)

DELIVERABLES:
- Modify log_step() internal implementation only
- Replace error print statements with logger.error calls
- Ensure workflow behavior is identical except for logging mechanism
- Manual verification of logging output

CONSTRAINTS:
- Do NOT change any function signatures except internal implementation
- Do NOT modify workflow logic, error handling, or control flow
- Do NOT change message content - only the output mechanism
- Remove timestamp formatting from log_step (logging system handles it)

VERIFICATION:
- All existing functionality works identically
- Log messages appear with proper timestamps via logging system
- Error messages still appear and stop workflow appropriately
```

## Verification Steps
1. Run `python workflows/implement.py` and verify similar visual output with proper timestamps
2. Run `python workflows/implement.py --log-level DEBUG` and see additional details
3. Test error scenarios still work (missing files, git issues, etc.)
4. Verify workflow completes successfully with structured logging
5. Compare output format with previous version (should have standard logging timestamps)
