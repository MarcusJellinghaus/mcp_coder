# Step 4: Prompt Execution and Session Management

## Objective

Implement LLM prompt execution workflow with session continuation across three prompts.

## Files to Modify

- `workflows/create_plan.py` - Add prompt loading, execution, and validation functions

## Implementation Details

### WHERE
- `workflows/create_plan.py` - Add `_load_prompt_or_exit()`, `format_initial_prompt()`, `run_planning_prompts()`, and `validate_output_files()` functions

### WHAT

```python
def _load_prompt_or_exit(header: str) -> str:
    """Load prompt template or exit with clear error message."""

def format_initial_prompt(prompt_template: str, issue_data: IssueData) -> str:
    """Format initial analysis prompt with issue content."""

def run_planning_prompts(
    project_dir: Path,
    issue_data: IssueData,
    llm_method: str
) -> bool:
    """Execute three planning prompts with session continuation.
    
    Returns:
        True if all prompts succeed, False on error
    """

def validate_output_files(project_dir: Path) -> bool:
    """Validate required output files exist.
    
    Returns:
        True if files exist, False otherwise
    """
```

### HOW

**Imports:**
```python
from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.session import parse_llm_method
```

**_load_prompt_or_exit():**
- Reuse exact pattern from create_pr.py
- Load prompt using get_prompt()
- Exit with sys.exit(1) on error

**format_initial_prompt():**
- Take prompt template and issue data
- Append formatted issue section at end

**run_planning_prompts():**
- Load all three prompts using _load_prompt_or_exit()
- Format initial prompt with issue content
- Execute first prompt, capture session_id
- Execute second and third prompts using session_id
- Return success/failure

**validate_output_files():**
- Check pr_info/steps/summary.md exists
- Check pr_info/steps/step_1.md exists
- Return True only if both exist

### ALGORITHM

**format_initial_prompt():**
```
1. Create issue section with:
   - Separator line "---"
   - "## Issue to Implement:"
   - "**Title:** {title}"
   - "**Number:** #{number}"
   - "**Description:**"
   - "{body}"
2. Append to prompt_template
3. Return combined string
```

**run_planning_prompts():**
```
1. Load three prompts: "Initial Analysis", "Simplification Review", "Implementation Plan Creation"
2. Format initial prompt with issue data
3. Parse llm_method to (provider, method)
4. Call prompt_llm() with initial prompt, get response_1
5. Extract session_id = response_1["session_id"]
6. Call prompt_llm() with second prompt and session_id, get response_2
7. Call prompt_llm() with third prompt and session_id, get response_3
8. If any call fails or returns empty: return False
9. Return True
```

**validate_output_files():**
```
1. summary_path = project_dir / "pr_info" / "steps" / "summary.md"
2. step_1_path = project_dir / "pr_info" / "steps" / "step_1.md"
3. If not summary_path.exists(): log error, return False
4. If not step_1_path.exists(): log error, return False
5. Log "✓ Required output files exist"
6. Return True
```

### DATA

**format_initial_prompt() returns:**
```python
str  # Combined prompt text
```

**run_planning_prompts() returns:**
```python
bool  # Success/failure indicator
```

**validate_output_files() returns:**
```python
bool  # True if both files exist
```

## Testing

Create `tests/workflows/create_plan/test_prompt_execution.py`:

```python
def test_load_prompt_or_exit_success()
def test_load_prompt_or_exit_failure()
def test_format_initial_prompt()
def test_run_planning_prompts_success()
def test_run_planning_prompts_first_fails()
def test_run_planning_prompts_session_continuation()
def test_validate_output_files_both_exist()
def test_validate_output_files_missing_summary()
def test_validate_output_files_missing_step_1()
```

## Acceptance Criteria

- [ ] Function loads prompts using get_prompt()
- [ ] Function exits cleanly on prompt loading failure
- [ ] Initial prompt includes formatted issue content
- [ ] All three prompts execute in sequence
- [ ] Session ID propagates through all prompts
- [ ] Function handles LLM failures gracefully
- [ ] Validation checks both required files
- [ ] All tests pass with mocked LLM responses

## LLM Prompt for Implementation

```
Please implement Step 4 of the create_plan workflow.

Reference the summary at pr_info/steps/summary.md and previous steps.

Add prompt loading, execution, and validation functions to workflows/create_plan.py.

Key requirements:
- Use PROMPTS_FILE_PATH from constants module
- Load prompts with headers: "Initial Analysis", "Simplification Review", "Implementation Plan Creation"
- Format initial prompt by appending issue details (title, number, body)
- Use prompt_llm() with session continuation (pass session_id between calls)
- Parse llm_method using parse_llm_method() before calling prompt_llm()
- Validate pr_info/steps/summary.md and pr_info/steps/step_1.md exist
- Follow _load_prompt_or_exit() pattern from create_pr.py

Implement the tests as specified with proper mocking of LLM calls.
```
