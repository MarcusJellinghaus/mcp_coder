# Step 4: Implement CLI Command

## LLM Prompt
```
Based on the summary document and this step, implement the main CLI command for branch status checking.

Create `src/mcp_coder/cli/commands/check_branch_status.py` with the `execute_check_branch_status()` function that handles both read-only analysis and auto-fix modes. Write comprehensive tests first, then implement the command logic.

Reference the summary document for command modes, flag handling, and integration with existing CI fix logic from the implement workflow.
```

## WHERE
- **New File**: `src/mcp_coder/cli/commands/check_branch_status.py`
- **Test File**: `tests/cli/commands/test_check_branch_status.py`

## WHAT

### Main Command Function
```python
def execute_check_branch_status(args: argparse.Namespace) -> int:
    """Execute branch status check command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
```

### Core Logic Functions
```python
def _run_status_check(project_dir: Path, llm_truncate: bool) -> BranchStatusReport:
    """Run status collection and return report."""

def _run_auto_fixes(
    project_dir: Path, 
    report: BranchStatusReport,
    provider: str,
    method: str,
    mcp_config: Optional[str],
    execution_dir: Optional[Path]
) -> bool:
    """Attempt automatic fixes based on status report."""

def _prompt_for_major_operations(report: BranchStatusReport) -> bool:
    """Prompt user for permission on risky operations."""
```

### Test Functions
```python
def test_execute_check_branch_status_read_only()
def test_execute_check_branch_status_with_fixes()
def test_execute_check_branch_status_llm_mode()
def test_run_auto_fixes_ci_only()
def test_run_auto_fixes_with_rebase()
def test_prompt_for_major_operations()
```

## HOW

### Integration Points
```python
# Import existing utilities
from ...utils.branch_status import collect_branch_status, BranchStatusReport
from ...workflows.implement.core import check_and_fix_ci
from ...utils.git_operations.remotes import rebase_onto_branch
from ...utils.github_operations.labels_manager import LabelsManager
from ...llm.env import prepare_llm_environment
```

### Command Line Arguments
```python
# Expected args structure:
args.project_dir: Optional[str]
args.fix: bool                    # --fix flag
args.llm_truncate: bool          # --llm-truncate flag  
args.llm_method: str             # --llm-method flag
args.mcp_config: Optional[str]   # --mcp-config flag
args.execution_dir: Optional[str] # --execution-dir flag
```

### Algorithm (execute_check_branch_status)
```
1. Validate project directory and setup logging
2. Collect branch status using collect_branch_status()
3. Print status report (human or LLM format)
4. If --fix flag: attempt auto-fixes with user prompts
5. Return appropriate exit code based on results
```

## DATA

### Auto-Fix Decision Logic
```python
# Fix priority and safety:
1. CI Failures: Auto-fix (reuse existing check_and_fix_ci)
2. Task Completion: Informational only (no auto-fix)
3. Clean Rebase: Prompt user for confirmation
4. Conflicted Rebase: Warn user, suggest manual resolution
5. GitHub Labels: Suggest appropriate transitions
```

### User Interaction Patterns
```python
# Safe operations (no prompt needed):
- Fix CI failures
- Format code
- Run quality checks

# Risky operations (prompt required):
- Rebase with potential conflicts
- Update GitHub labels
- Force push operations
```

### Exit Code Strategy
```python
# Exit codes:
0: Success (status clean or fixes applied successfully)
1: Error (validation failed, fixes failed, user declined)

# Special cases:
# - API failures in read-only mode: exit 0 (graceful degradation)
# - Partial fix success: exit 0 with warnings
```

## Implementation Notes
- **User Experience**: Clear progress indicators during fixes
- **Error Recovery**: Graceful handling of partial fix failures  
- **Logging Strategy**: Use INFO for status, WARNING for issues requiring attention
- **Dry Run Logic**: Show what would be fixed without --fix flag
- **Modularity**: Each fix type is independent and can succeed/fail separately
- **Existing Patterns**: Follow same structure as `implement.py` command