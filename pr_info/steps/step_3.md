# Step 3: Implement Task Processing Module with Tests

## Objective
Create the task processing module handling individual task execution, LLM integration, mypy fixes, formatting, and git operations.

## LLM Prompt
```
Implement Step 3 from the summary (pr_info/steps/summary.md): Create task processing module with comprehensive tests.

Extract task processing logic from workflows/implement.py and create:
- tests/workflows/implement/test_task_processing.py (test-first approach)
- src/mcp_coder/workflows/implement/task_processing.py

Mock all LLM calls, git operations, formatters, and file I/O. Follow existing test patterns.

Reference the summary document for architecture and ensure all task processing features are preserved.
```

## Implementation Details

### WHERE
- `tests/workflows/implement/test_task_processing.py`
- `src/mcp_coder/workflows/implement/task_processing.py`

### WHAT
**Main functions:**
```python
def get_next_task(project_dir: Path) -> Optional[str]
def save_conversation_comprehensive(project_dir: Path, content: str, step_num: int, ...) -> None
def check_and_fix_mypy(project_dir: Path, step_num: int, llm_method: str) -> bool
def run_formatters(project_dir: Path) -> bool
def commit_changes(project_dir: Path) -> bool
def push_changes(project_dir: Path) -> bool
def process_single_task(project_dir: Path, llm_method: str) -> bool
```

### HOW
- Mock `ask_llm`, `format_code`, git operations, file I/O
- Use `@patch` decorators for external dependencies
- Test both success and failure scenarios
- Preserve conversation saving functionality

### ALGORITHM
```
1. Test-first: Mock all external dependencies
2. Extract task processing functions from original script
3. Maintain LLM integration with comprehensive data capture
4. Preserve mypy retry logic with conversation saving
5. Integrate with existing formatters and git modules
```

### DATA
**Return values:**
- `bool` for success/failure operations
- `Optional[str]` for task retrieval
- `None` for side-effect functions (save operations)
- Uses existing `Path`, conversation data structures

## Files Created
- `tests/workflows/implement/test_task_processing.py`
- `src/mcp_coder/workflows/implement/task_processing.py`

## Success Criteria
- Core task processing functions tested with mocks
- 80% test coverage focused on critical workflow paths
- No real LLM/git/file operations in tests
- Basic conversation saving (deferred: complex mypy retry logic)
