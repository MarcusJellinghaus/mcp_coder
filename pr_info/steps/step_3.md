# Step 3: Add CLI Flags for Label Update Feature

## Context
Core functionality is complete (Step 2). Now we expose it to users via CLI flags. Following the opt-in design, we add `--update-labels` to three workflow commands while maintaining backward compatibility.

**Reference**: See `pr_info/steps/summary.md` for architectural overview.

## Objective
Add `--update-labels` CLI argument to three workflow parsers and thread the flag through command handlers to workflow functions. No change to default behavior (opt-in only).

## WHERE: Files to Modify

```
src/mcp_coder/cli/main.py                     (MODIFY - 3 parsers)
src/mcp_coder/cli/commands/implement.py       (MODIFY - pass flag)
src/mcp_coder/cli/commands/create_plan.py     (MODIFY - pass flag)
src/mcp_coder/cli/commands/create_pr.py       (MODIFY - pass flag)
```

## WHAT: Changes Required

### 1. Add Argument to Parsers (main.py)

**Location**: After existing arguments in each parser

```python
# implement_parser (around line 160)
implement_parser.add_argument(
    "--update-labels",
    action="store_true",
    help="Automatically update GitHub issue labels on successful completion",
)

# create_plan_parser (around line 195)
create_plan_parser.add_argument(
    "--update-labels",
    action="store_true",
    help="Automatically update GitHub issue labels on successful completion",
)

# create_pr_parser (around line 215)
create_pr_parser.add_argument(
    "--update-labels",
    action="store_true",
    help="Automatically update GitHub issue labels on successful completion",
)
```

### 2. Update Command Handlers

**File**: `src/mcp_coder/cli/commands/implement.py`
```python
# Modify execute_implement() function signature (around line 25)
def execute_implement(args: argparse.Namespace) -> int:
    # ... existing code ...
    
    # Pass update_labels to workflow (add after existing arguments)
    return run_implement_workflow(
        project_dir=project_dir,
        provider=provider,
        method=method,
        mcp_config=args.mcp_config,
        update_labels=args.update_labels,  # ADD THIS LINE
    )
```

**File**: `src/mcp_coder/cli/commands/create_plan.py`
```python
# Modify execute_create_plan() function (around line 25)
def execute_create_plan(args: argparse.Namespace) -> int:
    # ... existing code ...
    
    # Pass update_labels to workflow
    return run_create_plan_workflow(
        issue_number=args.issue_number,
        project_dir=project_dir,
        provider=provider,
        method=method,
        mcp_config=args.mcp_config,
        update_labels=args.update_labels,  # ADD THIS LINE
    )
```

**File**: `src/mcp_coder/cli/commands/create_pr.py`
```python
# Modify execute_create_pr() function (around line 25)
def execute_create_pr(args: argparse.Namespace) -> int:
    # ... existing code ...
    
    # Pass update_labels to workflow
    return run_create_pr_workflow(
        project_dir=project_dir,
        provider=provider,
        method=method,
        mcp_config=args.mcp_config,
        update_labels=args.update_labels,  # ADD THIS LINE
    )
```

### 3. Update Workflow Function Signatures

**File**: `src/mcp_coder/workflows/implement/core.py`
```python
# Modify function signature (around line 200)
def run_implement_workflow(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    update_labels: bool = False,  # ADD THIS PARAMETER
) -> int:
    """Main workflow orchestration function.
    
    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        update_labels: If True, update GitHub issue labels on success
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
```

**File**: `src/mcp_coder/workflows/create_plan.py`
```python
# Modify function signature (around line 280)
def run_create_plan_workflow(
    issue_number: int,
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    update_labels: bool = False,  # ADD THIS PARAMETER
) -> int:
    """Main workflow orchestration function.
    
    Args:
        issue_number: GitHub issue number to create plan for
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        update_labels: If True, update GitHub issue labels on success
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
```

**File**: `src/mcp_coder/workflows/create_pr/core.py`
```python
# Modify function signature (around line 270)
def run_create_pr_workflow(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: str | None = None,
    update_labels: bool = False,  # ADD THIS PARAMETER
) -> int:
    """Main workflow orchestration function.
    
    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        update_labels: If True, update GitHub issue labels on success
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
```

## HOW: Integration Points

### No New Imports Required
All changes use existing `argparse.Namespace` and function parameters.

### Backward Compatibility
```python
# Default value is False - existing behavior unchanged
update_labels: bool = False

# Flag only affects behavior when explicitly set by user:
# mcp-coder implement --update-labels
```

### Type Hints
All function signatures use proper type hints:
- `update_labels: bool = False`
- Compatible with existing type checking

## ALGORITHM: No Complex Logic

This step is pure plumbing - threading a boolean flag through layers:
```
CLI Parser → Command Handler → Workflow Function
   ↓              ↓                  ↓
args.update_labels → args.update_labels → update_labels parameter
```

## DATA: Argument Structure

### argparse Namespace (after parsing)
```python
args.update_labels: bool = False  # Default
args.update_labels: bool = True   # When --update-labels passed
```

### Function Parameters
```python
def run_implement_workflow(..., update_labels: bool = False)
def run_create_plan_workflow(..., update_labels: bool = False)
def run_create_pr_workflow(..., update_labels: bool = False)
```

## Implementation Details

### Help Text Convention
Use consistent help text across all three commands:
```python
help="Automatically update GitHub issue labels on successful completion"
```

### Action Type
```python
action="store_true"  # Boolean flag, no argument value
# Usage: mcp-coder implement --update-labels
# Not: mcp-coder implement --update-labels true
```

### Parameter Order
Place `update_labels` as last parameter in workflow functions (after `mcp_config`):
```python
def run_workflow(
    ...,
    mcp_config: Optional[str] = None,
    update_labels: bool = False,  # Last parameter
) -> int:
```

## Validation Checklist
- [ ] `--update-labels` added to implement_parser
- [ ] `--update-labels` added to create_plan_parser
- [ ] `--update-labels` added to create_pr_parser
- [ ] All three have identical help text
- [ ] All three use `action="store_true"`
- [ ] execute_implement() passes args.update_labels
- [ ] execute_create_plan() passes args.update_labels
- [ ] execute_create_pr() passes args.update_labels
- [ ] run_implement_workflow() signature updated
- [ ] run_create_plan_workflow() signature updated
- [ ] run_create_pr_workflow() signature updated
- [ ] All docstrings updated with new parameter
- [ ] Default value is False (backward compatible)
- [ ] Type hints correct (bool = False)

## Testing Commands

### Manual CLI Testing
```bash
# Test help text displays correctly
mcp-coder implement --help | grep "update-labels"
mcp-coder create-plan --help | grep "update-labels"
mcp-coder create-pr --help | grep "update-labels"

# Test flag parsing (won't execute, just validates parsing)
mcp-coder implement --update-labels --help
```

### Code Quality Checks
```bash
# Type checking
mcp__code-checker__run_mypy_check()

# Code quality
mcp__code-checker__run_pylint_check()

# Run fast unit tests to ensure no breakage
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
```

## Next Step Preview
**Step 4** will integrate the label update calls into the three workflow functions, connecting the flag to the actual functionality.

---

## LLM Prompt for This Step

```
You are implementing Step 3 of the auto-label update feature for mcp-coder.

CONTEXT:
Read pr_info/steps/summary.md for architectural overview.
Core functionality is complete (Step 2), now expose via CLI flags.

TASK:
Add --update-labels CLI flag to three commands and thread through to workflows.

FILES TO MODIFY:
1. src/mcp_coder/cli/main.py
   - Add --update-labels to implement_parser
   - Add --update-labels to create_plan_parser
   - Add --update-labels to create_pr_parser

2. src/mcp_coder/cli/commands/implement.py
   - Pass args.update_labels to run_implement_workflow()

3. src/mcp_coder/cli/commands/create_plan.py
   - Pass args.update_labels to run_create_plan_workflow()

4. src/mcp_coder/cli/commands/create_pr.py
   - Pass args.update_labels to run_create_pr_workflow()

5. Update workflow function signatures:
   - src/mcp_coder/workflows/implement/core.py
   - src/mcp_coder/workflows/create_plan.py
   - src/mcp_coder/workflows/create_pr/core.py

REQUIREMENTS:
- Use action="store_true" for boolean flag
- Consistent help text across all commands
- Default value: False (backward compatible)
- Update docstrings with new parameter
- Proper type hints: update_labels: bool = False

REFERENCE THIS STEP:
pr_info/steps/step_3.md (contains exact code snippets and locations)

After implementation, run code quality checks:
1. mcp__code-checker__run_mypy_check
2. mcp__code-checker__run_pylint_check
3. mcp__code-checker__run_pytest_check (fast unit tests only)
```
