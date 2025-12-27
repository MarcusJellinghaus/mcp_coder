# Step 1: Test Current CI Behavior and Create Test for New Matrix Structure

## LLM Prompt
```
Reference: pr_info/steps/summary.md - CI Pipeline Restructure

Implement Step 1: Test current CI behavior and create validation tests for the new matrix structure approach. The goal is to understand the current CI flow and establish tests that verify the matrix approach will work correctly.

Follow the requirements in this step document precisely.
```

## Objective
Create test infrastructure to validate current CI behavior and establish verification for the matrix-based approach.

## WHERE
- `tests/ci/test_github_actions_matrix.py` (new test file)
- `.github/workflows/` (analysis target)

## WHAT

### Main Functions
```python
def test_current_ci_structure_analysis():
    """Analyze current CI workflow structure and document behavior"""

def test_matrix_job_simulation():
    """Simulate matrix job behavior locally to validate approach"""
    
def test_matrix_job_naming():
    """Verify matrix job names will be correct in GitHub UI"""

def validate_continue_on_error_removal():
    """Confirm removing continue-on-error achieves proper failure status"""
```

## HOW

### Integration Points
- **pytest markers**: Use `@pytest.mark.ci_integration` for CI-specific tests
- **YAML parsing**: Import `yaml` for workflow file analysis
- **subprocess**: Simulate command execution for matrix validation

### Imports
```python
import yaml
import subprocess
import pytest
from pathlib import Path
```

## ALGORITHM

### Core Logic (test_matrix_job_simulation)
```
1. Load current CI workflow YAML structure
2. Extract check commands from existing steps
3. Simulate matrix job execution locally
4. Verify each command can run independently
5. Confirm failure propagation works correctly
6. Assert matrix approach maintains functionality
```

## DATA

### Return Values
```python
# Current CI analysis result
CurrentCIStructure = {
    'job_count': int,
    'check_steps': List[str],
    'has_continue_on_error': bool,
    'has_summarize_step': bool
}

# Matrix simulation result  
MatrixSimulation = {
    'matrix_jobs': List[str],
    'execution_success': bool,
    'failure_propagation': bool,
    'job_independence': bool
}
```

## Implementation Notes
- **TDD Approach**: Write tests first to validate current behavior
- **Minimal Risk**: Test infrastructure doesn't modify actual CI
- **Validation**: Ensure matrix approach maintains all existing functionality
- **Documentation**: Capture current CI behavior for comparison

## Success Criteria
- Tests pass and document current CI structure
- Matrix simulation validates independent job execution
- Failure propagation behavior confirmed
- Foundation established for Step 2 implementation