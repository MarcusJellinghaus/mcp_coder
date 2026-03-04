# Step 1: Add --committed-only Flag to Parser

## Context
Read `pr_info/steps/summary.md` for full context. This step adds the CLI flag to opt-out of showing uncommitted changes.

## Objective
Add `--committed-only` boolean flag to the `compact-diff` subcommand parser. This flag will default to `False` (show uncommitted changes by default).

## Location
**File**: `src/mcp_coder/cli/parsers.py`
**Function**: `add_git_tool_parsers()`

## Changes Required

### WHERE: File Path
```
src/mcp_coder/cli/parsers.py
└── add_git_tool_parsers() function
    └── compact-diff parser definition
```

### WHAT: Add Argument

**Function signature** (existing, no change):
```python
def add_git_tool_parsers(subparsers: Any) -> None:
    """Add git-tool command parsers."""
```

**New argument** (add after existing `--exclude` argument):
```python
compact_diff_parser.add_argument(
    "--committed-only",
    action="store_true",
    help="Show only committed changes (exclude uncommitted changes from output)",
)
```

### HOW: Integration

**Location in file**: Find the section that creates `compact_diff_parser` (around line 730):
```python
compact_diff_parser = git_tool_subparsers.add_parser(
    "compact-diff",
    help="Generate compact diff suppressing moved-code blocks",
    formatter_class=WideHelpFormatter,
    epilog="""...""",
)
```

**Add the new argument** after the existing arguments (base-branch, project-dir, exclude).

### DATA: Argument Properties

**Namespace attribute**: `args.committed_only`
**Type**: `bool`
**Default**: `False` (via `action="store_true"`)
**Effect**: When flag present → `True`, when absent → `False`

## Test Requirements

### Test File
**Path**: `tests/cli/commands/test_git_tool.py`

### Test Class
Add to existing file or create new test class:
```python
class TestCompactDiffCommittedOnlyFlag:
    """Test --committed-only flag parsing."""
```

### Test Cases

**Test 1: Flag absent (default behavior)**
```python
def test_committed_only_flag_absent_defaults_to_false(self) -> None:
    """Test that args.committed_only defaults to False when flag is absent."""
    from mcp_coder.cli.main import create_parser
    
    parser = create_parser()
    args = parser.parse_args(["git-tool", "compact-diff"])
    
    assert args.committed_only is False
```

**Test 2: Flag present**
```python
def test_committed_only_flag_present_sets_to_true(self) -> None:
    """Test that args.committed_only is True when --committed-only flag is used."""
    from mcp_coder.cli.main import create_parser
    
    parser = create_parser()
    args = parser.parse_args(["git-tool", "compact-diff", "--committed-only"])
    
    assert args.committed_only is True
```

**Test 3: Flag works with other arguments**
```python
def test_committed_only_flag_with_other_arguments(self) -> None:
    """Test that --committed-only works alongside --exclude and --base-branch."""
    from mcp_coder.cli.main import create_parser
    
    parser = create_parser()
    args = parser.parse_args([
        "git-tool", "compact-diff",
        "--committed-only",
        "--base-branch", "main",
        "--exclude", "*.log"
    ])
    
    assert args.committed_only is True
    assert args.base_branch == "main"
    assert args.exclude == ["*.log"]
```

## Validation

### Manual Testing
```bash
# Parse help text
mcp-coder git-tool compact-diff --help
# Should show: --committed-only flag in output

# Run command (no error expected, even though logic not implemented yet)
mcp-coder git-tool compact-diff --committed-only
```

### Expected Behavior (After This Step)
- Parser accepts `--committed-only` flag without error
- `args.committed_only` is `False` by default
- `args.committed_only` is `True` when flag provided
- Command still works (even though flag has no effect yet)

## Definition of Done
- [ ] `--committed-only` argument added to `parsers.py`
- [ ] Flag defaults to `False` when absent
- [ ] Flag sets to `True` when present
- [ ] All 3 test cases pass
- [ ] `mcp-coder git-tool compact-diff --help` shows new flag
- [ ] No existing tests broken

## LLM Implementation Prompt

```
You are implementing Step 1 of the compact-diff uncommitted changes feature.

Read pr_info/steps/summary.md for full context.

Task: Add --committed-only flag to the compact-diff subcommand parser.

File to modify: src/mcp_coder/cli/parsers.py
Function: add_git_tool_parsers()

Add this argument to the compact_diff_parser (after existing arguments):

compact_diff_parser.add_argument(
    "--committed-only",
    action="store_true",
    help="Show only committed changes (exclude uncommitted changes from output)",
)

Then create tests in tests/cli/commands/test_git_tool.py:

1. Test flag defaults to False when absent
2. Test flag is True when present  
3. Test flag works with other arguments (--exclude, --base-branch)

Use the test structure from existing TestCompactDiffArguments class as a reference.

Follow TDD: Write the tests first, then add the parser argument to make them pass.

Verify:
- Run: pytest tests/cli/commands/test_git_tool.py::TestCompactDiffCommittedOnlyFlag -v
- All tests should pass
- Run: mcp-coder git-tool compact-diff --help
- Should show --committed-only in help text
```

## Next Step
Proceed to `pr_info/steps/step_2.md` - Write tests for uncommitted changes display logic.
