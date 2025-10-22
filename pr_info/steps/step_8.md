# Step 8: Add CLI Smoke Test

## Context
See `pr_info/steps/summary.md` for full architectural context.

This step adds a minimal smoke test to verify CLI command integration works correctly.

## Objective
Add lightweight test confirming `mcp-coder create-pr` command is properly wired and accessible.

---

## WHERE
**File to modify:** `tests/cli/commands/test_create_pr.py`

**Location:** Add new test class at end of file

---

## WHAT - Test to Add

### Test Class: CLI Integration Smoke Test

```python
class TestCreatePrCliIntegration:
    """Smoke tests for CLI integration."""
    
    def test_create_pr_command_registered(self):
        """Test that create-pr command is registered in CLI."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        
        # Parse with create-pr command
        args = parser.parse_args(['create-pr', '--help'])
        
        # Should not raise exception
        assert args.command == 'create-pr'
    
    def test_create_pr_command_has_required_arguments(self):
        """Test that create-pr command has expected arguments."""
        from mcp_coder.cli.main import create_parser
        
        parser = create_parser()
        args = parser.parse_args(['create-pr'])
        
        # Check arguments exist
        assert hasattr(args, 'project_dir')
        assert hasattr(args, 'llm_method')
        
        # Check defaults
        assert args.project_dir is None
        assert args.llm_method == 'claude_code_cli'
```

---

## HOW - Implementation Details

### Test Strategy
- **Minimal scope:** Just verify command is registered
- **No mocking:** Real parser, real arguments
- **Fast execution:** No subprocess calls, no I/O
- **Integration check:** Confirms main.py wiring works

### What We're Testing
1. **Command registration:** `create-pr` exists in subparsers
2. **Argument parsing:** `--project-dir` and `--llm-method` work
3. **Default values:** Arguments have correct defaults

### What We're NOT Testing
- Actual workflow execution (covered by unit tests)
- Error handling (covered by unit tests)
- End-to-end functionality (would require subprocess)

---

## ALGORITHM - Test Flow

```
Test 1 - Command Registered:
1. Import create_parser from main.py
2. Create parser instance
3. Parse ['create-pr', '--help']
4. Verify args.command == 'create-pr'

Test 2 - Arguments Exist:
1. Import create_parser from main.py
2. Create parser instance  
3. Parse ['create-pr'] (minimal args)
4. Verify args has 'project_dir' attribute
5. Verify args has 'llm_method' attribute
6. Verify defaults are correct
```

---

## VALIDATION

### Test Execution
```bash
# Run just the new smoke tests
pytest tests/cli/commands/test_create_pr.py::TestCreatePrCliIntegration -v

# Expected: 2 tests PASS in < 1 second
```

### Full Test Suite
```bash
# Run all create-pr tests
pytest tests/cli/commands/test_create_pr.py -v

# Expected: All tests PASS (existing + new smoke tests)
```

### Code Quality
```bash
# Pylint check
pylint tests/cli/commands/test_create_pr.py

# Mypy check
mypy tests/cli/commands/test_create_pr.py
```

---

## LLM Prompt for This Step

```
I'm implementing Step 8 of the create_PR to CLI command conversion.

Context: See pr_info/steps/summary.md for architecture.

Task: Add CLI smoke test for integration verification.

Step 8 Details: Read pr_info/steps/step_8.md

Instructions:
1. Open tests/cli/commands/test_create_pr.py
2. Add TestCreatePrCliIntegration class at end of file
3. Implement 2 smoke tests as specified
4. Run tests: pytest tests/cli/commands/test_create_pr.py::TestCreatePrCliIntegration -v
5. Run code quality checks
6. Commit with message: "Add CLI smoke tests for create-pr command"

Very lightweight tests - just verify CLI wiring works.
```

---

## Verification Checklist

- [ ] Test class `TestCreatePrCliIntegration` added
- [ ] Test 1: `test_create_pr_command_registered` implemented
- [ ] Test 2: `test_create_pr_command_has_required_arguments` implemented
- [ ] Smoke tests pass: `pytest tests/cli/commands/test_create_pr.py::TestCreatePrCliIntegration -v`
- [ ] All CLI tests pass: `pytest tests/cli/commands/test_create_pr.py -v`
- [ ] Pylint passes
- [ ] Mypy passes
- [ ] Commit created

---

## Dependencies

### Required Before This Step
- ✅ Step 3 completed (CLI integration exists)
- ✅ `create-pr` command registered in main.py

### Blocks
- Step 10 (final validation)

---

## Notes

- **Very lightweight:** No subprocess, no I/O, runs in milliseconds
- **Integration verification:** Confirms main.py wiring is correct
- **Not end-to-end:** Doesn't actually run workflow
- **Quick to implement:** Should take ~15 minutes
