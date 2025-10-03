# Step 4: Implement Core Workflow Orchestration with Tests

## Objective
Create the main workflow orchestration module that coordinates prerequisites, task tracker preparation, and task processing loops.

## LLM Prompt
```
Implement Step 4 from the summary (pr_info/steps/summary.md): Create core workflow orchestration with comprehensive tests.

Extract main workflow logic from workflows/implement.py and create:
- tests/workflows/implement/test_core.py (test-first approach)  
- src/mcp_coder/workflows/implement/core.py

Mock all dependencies including modules from steps 2-3. Focus on workflow orchestration and progress tracking.

Reference the summary document for architecture and ensure main workflow loop is preserved.
```

## Implementation Details

### WHERE
- `tests/workflows/implement/test_core.py`
- `src/mcp_coder/workflows/implement/core.py`

### WHAT
**Main functions:**
```python
def prepare_task_tracker(project_dir: Path, llm_method: str) -> bool
def log_progress_summary(project_dir: Path) -> None
def run_implement_workflow(project_dir: Path, llm_method: str) -> int
def resolve_project_dir(project_dir_arg: Optional[str]) -> Path
```

### HOW
- Mock prerequisite and task processing modules
- Mock task tracker operations and LLM calls
- Test workflow orchestration logic
- Preserve progress tracking functionality

### ALGORITHM
```
1. Test-first: Mock all workflow dependencies
2. Extract main orchestration logic from original script
3. Coordinate prerequisites → task tracker → task processing loop
4. Maintain progress summaries and completion tracking
5. Return appropriate exit codes
```

### DATA
**Return values:**
- `int` - exit codes (0=success, 1=error)
- `bool` - operation success/failure
- `None` - logging/side-effect functions
- Uses `Path` objects and existing data structures

## Files Created
- `tests/workflows/implement/test_core.py`
- `src/mcp_coder/workflows/implement/core.py`

## Success Criteria
- Core workflow orchestration fully tested
- 95%+ test coverage with comprehensive mocking
- Main workflow loop logic preserved
- Progress tracking functionality maintained
