# Step 1: Update CLI Parser for New Parameters (TDD)

## Objective
Add `--ci-timeout` parameter and enhance `--fix` to accept optional integer argument, following test-driven development.

## Context
Read `pr_info/steps/summary.md` first for full context.

This step modifies the argument parser to support:
- `--ci-timeout SECONDS` - Wait for CI completion (default: 0 = no wait)
- `--fix [N]` - Fix with optional retry count (default: not provided = 0)

## WHERE: File Locations

### Tests
```
tests/cli/commands/test_check_branch_status.py
  - Add new test class: TestCheckBranchStatusParserEnhancements
```

### Implementation
```
src/mcp_coder/cli/parsers.py
  - Function: add_check_parsers()
  - Subparser: branch_status_parser (under check command)
```

## WHAT: Functions and Signatures

### Tests (Write First)
```python
class TestCheckBranchStatusParserEnhancements:
    """Test new parser parameters for CI waiting and fix retry."""
    
    def test_ci_timeout_parameter_defaults_to_zero()
    def test_ci_timeout_accepts_integer_value()
    def test_fix_without_argument_defaults_to_one()
    def test_fix_with_integer_argument()
    def test_fix_not_provided_defaults_to_zero()
    def test_all_parameters_together()
```

### Implementation (Write After Tests Pass)
```python
def add_check_parsers(subparsers: Any) -> None:
    """Add check command parsers (branch-status, file-size).
    
    Modifications:
    - Add --ci-timeout parameter to branch-status
    - Change --fix from action="store_true" to nargs="?", type=int
    """
```

## HOW: Integration Points

### Parser Structure
```
mcp-coder check branch-status [OPTIONS]

New/Modified Arguments:
  --ci-timeout SECONDS     Wait up to N seconds for CI completion (default: 0)
  --fix [N]               Fix issues, optionally retry N times (default: 0)
```

### Argument Namespace Result
```python
args.ci_timeout: int  # 0 (no wait), or positive integer
args.fix: int         # 0 (no fix), 1 (fix once), or N (retry N times)
```

## ALGORITHM: Implementation Logic

### Parser Configuration
```
1. Locate branch_status_parser in add_check_parsers()
2. Add --ci-timeout argument:
   - type=int
   - default=0
   - help text with default mentioned
3. Modify --fix argument:
   - Remove action="store_true"
   - Add nargs="?" (optional argument)
   - Add type=int
   - Add const=1 (value when flag used without argument)
   - Add default=0 (value when flag not used)
   - Update help text
```

## DATA: Return Values and Structures

### Input (Command Line)
```bash
# No fix, no wait (current behavior)
mcp-coder check branch-status

# Wait for CI, no fix
mcp-coder check branch-status --ci-timeout 180

# Fix once (current behavior preserved)
mcp-coder check branch-status --fix

# Fix with retry
mcp-coder check branch-status --ci-timeout 180 --fix 3
```

### Output (Namespace Object)
```python
# No parameters
Namespace(ci_timeout=0, fix=0, ...)

# --ci-timeout 180
Namespace(ci_timeout=180, fix=0, ...)

# --fix
Namespace(ci_timeout=0, fix=1, ...)

# --fix 3
Namespace(ci_timeout=0, fix=3, ...)

# --ci-timeout 180 --fix 2
Namespace(ci_timeout=180, fix=2, ...)
```

## Test Implementation Details

### Test File Location
`tests/cli/commands/test_check_branch_status.py`

### New Test Class
```python
class TestCheckBranchStatusParserEnhancements:
    """Test new parser parameters for CI waiting and fix retry."""

    def test_ci_timeout_parameter_defaults_to_zero(self) -> None:
        """Test --ci-timeout parameter defaults to 0."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status"])
        
        assert args.ci_timeout == 0

    def test_ci_timeout_accepts_integer_value(self) -> None:
        """Test --ci-timeout accepts integer values."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--ci-timeout", "180"])
        
        assert args.ci_timeout == 180

    def test_fix_without_argument_defaults_to_one(self) -> None:
        """Test --fix without argument equals 1 (fix once)."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix"])
        
        assert args.fix == 1

    def test_fix_with_integer_argument(self) -> None:
        """Test --fix with integer argument."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix", "3"])
        
        assert args.fix == 3

    def test_fix_not_provided_defaults_to_zero(self) -> None:
        """Test --fix not provided defaults to 0 (no fix)."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status"])
        
        assert args.fix == 0

    def test_all_parameters_together(self) -> None:
        """Test --ci-timeout and --fix together."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        args = parser.parse_args([
            "check", "branch-status",
            "--ci-timeout", "300",
            "--fix", "2",
            "--llm-truncate"
        ])
        
        assert args.ci_timeout == 300
        assert args.fix == 2
        assert args.llm_truncate is True
```

## Implementation Details

### File: `src/mcp_coder/cli/parsers.py`

### Location: Function `add_check_parsers()`

Find the section:
```python
branch_status_parser.add_argument(
    "--fix",
    action="store_true",
    help="Attempt to automatically fix issues found",
)
```

Replace with:
```python
branch_status_parser.add_argument(
    "--ci-timeout",
    type=int,
    default=0,
    metavar="SECONDS",
    help="Wait up to N seconds for CI completion (default: 0 = no wait)",
)
branch_status_parser.add_argument(
    "--fix",
    nargs="?",
    type=int,
    const=1,
    default=0,
    metavar="N",
    help="Fix issues up to N times (default: 0 = no fix, --fix alone = 1)",
)
```

## Validation Criteria

### Tests Must Pass
- ✅ All 6 new parser tests pass
- ✅ All existing tests continue to pass (backward compatibility)

### Manual Verification
```bash
# Verify help text
mcp-coder check branch-status --help

# Should show:
#   --ci-timeout SECONDS  Wait up to N seconds for CI completion (default: 0 = no wait)
#   --fix [N]            Fix issues up to N times (default: 0 = no fix, --fix alone = 1)
```

## LLM Implementation Prompt

```
Please read pr_info/steps/summary.md for full context.

Implement Step 1: Update CLI Parser for New Parameters (TDD)

STEP 1 - WRITE TESTS FIRST:
1. Read tests/cli/commands/test_check_branch_status.py
2. Add new test class TestCheckBranchStatusParserEnhancements with 6 tests:
   - test_ci_timeout_parameter_defaults_to_zero
   - test_ci_timeout_accepts_integer_value
   - test_fix_without_argument_defaults_to_one
   - test_fix_with_integer_argument
   - test_fix_not_provided_defaults_to_zero
   - test_all_parameters_together
3. Follow the test implementation details in pr_info/steps/step_1.md
4. Run tests - they should FAIL (code not implemented yet)

STEP 2 - IMPLEMENT TO MAKE TESTS PASS:
1. Read src/mcp_coder/cli/parsers.py
2. Locate add_check_parsers() function
3. Find branch_status_parser section
4. Add --ci-timeout parameter (type=int, default=0)
5. Modify --fix from action="store_true" to nargs="?", type=int, const=1, default=0
6. Follow implementation details in pr_info/steps/step_1.md
7. Run tests - they should PASS

STEP 3 - VERIFY:
1. Run all tests in test_check_branch_status.py
2. Verify backward compatibility (existing tests still pass)
3. Manually test: mcp-coder check branch-status --help

Success criteria:
- All 6 new tests pass
- All existing tests pass
- Help text shows new parameters correctly
```

## Dependencies
- None (standalone parser changes)

## Next Step
After this step completes successfully, proceed to Step 2: Add CI Waiting Logic.
