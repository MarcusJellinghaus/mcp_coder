# Step 1: Add PROMPT_3_TIMEOUT Constant

## LLM Prompt
```
Please review pr_info/steps/summary.md and this step (step_1.md).

Add the PROMPT_3_TIMEOUT constant to src/mcp_coder/workflows/create_plan.py following the KISS principle approach.

Requirements:
1. Add ONE module-level constant: PROMPT_3_TIMEOUT = 900
2. Place it after the logger setup (line ~30) and before the first function definition
3. Include a clear multi-line comment explaining:
   - Why this prompt needs 15 minutes (generates detailed multi-file plans)
   - That other prompts use standard 600s timeout
   - Reference to the issue (#173) is optional but helpful
4. Follow existing code style (spacing, naming conventions)

After implementation:
- Run code quality checks using MCP tools
- Verify the constant is defined correctly
- Do NOT modify any function calls yet (that's step 2)
```

## Objective
Add a single timeout constant for the Implementation Plan Creation prompt (Prompt 3) that requires 15 minutes instead of the standard 10 minutes used by other prompts.

## Context
- **File**: `src/mcp_coder/workflows/create_plan.py`
- **Location**: After logger setup (~line 30), before first function
- **Principle**: KISS - only add what's needed for the broken prompt

## Implementation Details

### WHERE
**File**: `src/mcp_coder/workflows/create_plan.py`
**Location**: After this line (~line 30):
```python
logger = logging.getLogger(__name__)
```

And before the first function definition:
```python
def check_prerequisites(project_dir: Path, issue_number: int) -> tuple[bool, IssueData]:
```

### WHAT
Add one module-level constant with documentation:

```python
# Timeout for Implementation Plan Creation prompt (15 minutes)
# This prompt requires more time than the standard 600s timeout used by other prompts
# because it generates detailed multi-file implementation plans with pseudocode and algorithms.
# See issue #173 for context.
PROMPT_3_TIMEOUT = 900  # 15 minutes
```

### HOW
**Integration**:
- No imports needed (simple integer constant)
- Module-level scope (accessible to all functions in the module)
- Follows existing naming convention (UPPER_CASE for constants)

**Style Requirements**:
- Use ALL_CAPS naming convention (Python PEP 8)
- Add clear multi-line comment explaining the rationale
- Place blank line before and after the constant block
- Inline comment after value to clarify units

### ALGORITHM
Not applicable - this is a constant definition with no logic.

### DATA
**Constant Definition**:
```python
PROMPT_3_TIMEOUT: int = 900  # Type: int, Value: 900 seconds (15 minutes)
```

**Usage** (will be implemented in Step 2):
- Will replace hardcoded `timeout=600` in Prompt 3 execution
- Will replace hardcoded `timeout=600s` in Prompt 3 debug log

## Testing Strategy

### Test Approach
**No new tests required** - this is a constant definition that will be validated by existing tests when used in Step 2.

### Validation
1. **Code quality checks**: Run pylint, pytest, mypy via MCP tools
2. **Visual inspection**: Verify constant placement and formatting
3. **Import test**: Ensure module still imports correctly

### Existing Test Coverage
- `tests/workflows/create_plan/test_prompt_execution.py` - Will validate timeout usage in Step 2
- `tests/workflows/create_plan/test_main.py` - Integration tests will verify no regression

## Acceptance Criteria
- [x] `PROMPT_3_TIMEOUT = 900` defined at module level
- [x] Clear multi-line comment explains the rationale
- [x] Constant placed after logger, before first function
- [x] Follows PEP 8 naming conventions
- [x] All code quality checks pass (pylint, pytest, mypy)
- [x] Module imports successfully

## Code Quality Verification
After implementation, run:
```bash
# Using MCP tools (mandatory per CLAUDE.md)
mcp__code-checker__run_pylint_check(target_directories=["src"])
mcp__code-checker__run_mypy_check(target_directories=["src"])
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"])
```

## Dependencies
- **Depends on**: None (first step)
- **Required by**: Step 2 (use the constant)

## Notes
- This step introduces the constant but doesn't use it yet
- Step 2 will update the actual timeout references
- Keeping changes atomic for easier review and rollback if needed
