# Step 5: Standardize Error Handling and Logging

## Context
Replace `print()` statements with proper logging framework and add `@log_function_call` decorator to maintain consistency with existing codebase patterns.

## WHERE

### File to Modify
```
src/mcp_coder/utils/github_operations/labels_manager.py
```

## WHAT

### Logging Setup and Method Decorators

```python
import logging
from mcp_coder.utils.log_utils import log_function_call

logger = logging.getLogger(__name__)

class LabelsManager:
    @log_function_call
    def get_labels(self) -> list[LabelData]:
    
    @log_function_call  
    def get_label(self, name: str) -> LabelData:
    
    @log_function_call
    def create_label(self, name: str, color: str, description: str = "") -> LabelData:
    
    @log_function_call
    def update_label(self, name: str, color: Optional[str] = None, ...) -> LabelData:
    
    @log_function_call
    def delete_label(self, name: str) -> bool:
```

## HOW

### Integration Points
- Import `logging` and `log_function_call` from `mcp_coder.utils.log_utils`
- Add logger configuration: `logger = logging.getLogger(__name__)`
- Apply `@log_function_call` decorator to all public methods
- Replace `print()` statements with appropriate logging levels

### Module-level Docstring
Add comprehensive module docstring explaining the labels management functionality.

## ALGORITHM

### Error Handling Classification
```
1. Validation failures → logger.warning() (invalid inputs)
2. Expected API responses → logger.debug() (label not found)  
3. GitHub API errors → logger.error() (authentication, permissions)
4. Unexpected exceptions → logger.error() (network, parsing)
5. Success operations → implicit via @log_function_call decorator
```

## DATA

### Logging Levels Used
- `logger.warning()`: Input validation failures
- `logger.debug()`: Expected negative results (label not found)
- `logger.error()`: API failures and unexpected exceptions
- `@log_function_call`: Automatic logging for method entry/exit

### Error Messages Format
- Include method context and relevant parameters
- Use consistent formatting: `"GitHub API error {operation}: {error_details}"`
- Validation warnings: `"Invalid {parameter}: {details}"`

## LLM Prompt

```
Standardize error handling and logging in LabelsManager to match existing codebase patterns.

Context: Read pr_info/steps/summary.md and pr_info/steps/decisions.md for overview.
Reference: src/mcp_coder/utils/github_operations/pr_manager.py -> logging patterns

Tasks:
1. Add proper imports: logging, log_function_call from mcp_coder.utils.log_utils
2. Add logger configuration: logger = logging.getLogger(__name__)
3. Add basic module-level docstring explaining labels management functionality
4. Replace all print() statements with appropriate logging levels:
   - logger.warning() for validation failures (invalid inputs)
   - logger.debug() for expected cases (label not found)
   - logger.error() for GitHub API errors and unexpected exceptions
5. Add @log_function_call decorator to all public methods:
   - get_labels(), get_label(), create_label(), update_label(), delete_label()

Implementation notes:
- Follow exact logging patterns from pr_manager.py
- Use consistent error message formatting
- Maintain all existing functionality - only change logging approach
- Keep method signatures unchanged

Run: pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
Expected: All tests PASS (no functional changes, only logging improvements)
```

## Notes

- No functional changes to method behavior
- Only logging and decoration improvements
- Follow exact patterns established in `pr_manager.py`
- Maintain backward compatibility with existing API
