# Step 1: Add Argument Parsing and Basic Logging Setup

## Objective
Implement command-line argument parsing for `--log-level` parameter and basic logging initialization in `workflows/implement.py`.

## WHERE
- **File**: `workflows/implement.py`
- **Module**: Root workflow script

## WHAT
### Main Functions with Signatures
```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including log level."""
    
def main() -> None:
    """Modified main function with argument parsing and logging setup."""
```

### Manual Verification
- Run `python workflows/implement.py --help` to verify argument appears
- Run `python workflows/implement.py --log-level DEBUG` to test parsing
- Run `python workflows/implement.py --log-level INVALID` to test argparse error handling

## HOW
### Integration Points
- **Import**: `import argparse`, `from mcp_coder.utils.log_utils import setup_logging`
- **Modify**: `main()` function to parse args before any other operations
- **Add**: `parse_arguments()` function before `main()`

### Dependencies
- Standard library: `argparse`
- Existing utility: `mcp_coder.utils.log_utils.setup_logging`

## ALGORITHM
```
1. Create argument parser with description
2. Add --log-level argument with choices [DEBUG, INFO, WARNING, ERROR, CRITICAL]
3. Set default to "INFO"
4. Parse arguments in main()
5. Call setup_logging(args.log_level)
6. Continue with existing workflow logic
```

## DATA
### Input Parameters
- `--log-level`: String from ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

### Return Values
- `parse_arguments()`: `argparse.Namespace` with `log_level` attribute
- `main()`: `None` (unchanged)

### Data Structures
```python
# argparse.Namespace object structure
args.log_level: str  # The selected log level
```

## LLM Prompt for Implementation

```
Based on the summary in pr_info/steps/summary.md, implement Step 1: Add argument parsing and logging setup to workflows/implement.py.

REQUIREMENTS:
1. Add argparse for --log-level parameter (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL, default: INFO)  
2. Modify main() to parse arguments and call setup_logging() early
3. Keep all existing functionality unchanged
4. Use existing mcp_coder.utils.log_utils.setup_logging()
5. Let argparse handle invalid arguments automatically

DELIVERABLES:
- Add parse_arguments() function to workflows/implement.py  
- Modify main() in workflows/implement.py to use argument parsing
- Ensure all existing workflow logic remains intact
- Manual verification of functionality

CONSTRAINTS:
- Minimal code changes
- No modification to existing function signatures except main()
- Preserve all current error handling and workflow behavior
```

## Verification Steps
1. Run `python workflows/implement.py --help` to see new parameter
2. Run `python workflows/implement.py --log-level DEBUG` to verify parsing
3. Run `python workflows/implement.py --log-level INVALID` to verify argparse error handling
4. Verify existing workflow still functions normally
