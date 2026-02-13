# Step 1: Create `llm_response_utils.py` and Enhance `strip_claude_footers()` (TDD)

## Objective

Create a new shared module `llm_response_utils.py`, move `strip_claude_footers()` from `commit_operations.py`, and enhance it to handle real-world footer patterns with case-insensitive matching and model name variations, using Test-Driven Development.

## Context

**Summary Reference**: See `pr_info/steps/summary.md` for full context.

**Current Limitation**: The existing function only matches exact string `"Co-Authored-By: Claude <noreply@anthropic.com>"` (case-sensitive), missing real-world variations like:
- `Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>`
- `co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>`

## WHERE

**New Module**: `src/mcp_coder/workflow_utils/llm_response_utils.py`
**Function**: `strip_claude_footers(message: str) -> str` (moved from `commit_operations.py`)

**New Test File**: `tests/workflow_utils/test_llm_response_utils.py`
**Test Class**: `TestStripClaudeFooters` (moved from `test_commit_operations.py`)

**Files to Update**:
- `src/mcp_coder/workflow_utils/commit_operations.py` (remove function, add import)
- `tests/workflow_utils/test_commit_operations.py` (remove test class)

## WHAT

### 1. Create New Module and Test File

**Create** `src/mcp_coder/workflow_utils/llm_response_utils.py`:
```python
"""LLM response processing utilities.

This module provides shared utilities for processing LLM responses,
including footer stripping used by both commit and PR workflows.
"""

import re

# Function implementation will be moved from commit_operations.py
```

**Create** `tests/workflow_utils/test_llm_response_utils.py` and move `TestStripClaudeFooters` class from `test_commit_operations.py`.

### 2. Add New Parameterized Tests (Write Tests First - TDD)

Add the following parameterized test methods to `TestStripClaudeFooters` class in new test file:

```python
@pytest.mark.parametrize("message,expected", [
    # Case-insensitive variations
    ("feat: add feature\n\nCo-authored-by: Claude Opus 4.5 <noreply@anthropic.com>", "feat: add feature"),
    ("feat: add feature\n\nco-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>", "feat: add feature"),
    ("feat: add feature\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>", "feat: add feature"),
])
def test_strip_coauthored_case_insensitive(message: str, expected: str) -> None:
    """Test case-insensitive matching for Co-Authored-By patterns."""

@pytest.mark.parametrize("message,expected", [
    # Model name variations
    ("feat: test\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>", "feat: test"),
    ("feat: test\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>", "feat: test"),
    ("feat: test\n\nCo-Authored-By: Claude <noreply@anthropic.com>", "feat: test"),
])
def test_strip_coauthored_model_variations(message: str, expected: str) -> None:
    """Test stripping Co-Authored-By with different Claude model names."""

def test_preserve_autorunner_bot_footer() -> None:
    """Test that AutoRunner Bot footers are preserved (not removed)."""
```

**Note:** Use `@pytest.mark.parametrize` to reduce test count from 8 individual tests to ~3 parameterized tests.

### 3. Move and Enhance `strip_claude_footers()` Function

**Move** `strip_claude_footers()` from `commit_operations.py` to `llm_response_utils.py`.

**Updated Signature and Docstring**:
```python
def strip_claude_footers(message: str) -> str:
    """Remove Claude Code footer lines from text (commit messages, PR bodies, etc.).

    Removes lines starting with 🤖 (robot emoji) and Co-Authored-By patterns
    with case-insensitive matching for 'Claude <model>? <noreply@anthropic.com>'
    from the end of the message. Also cleans up trailing blank lines.

    Supports model name variations: Claude Opus 4.5, Claude Sonnet 4.5, Claude (no model).
    Preserves non-Claude co-author footers (e.g., AutoRunner Bot).

    Args:
        message: The text to clean (commit message, PR body, etc.)

    Returns:
        Cleaned text with Claude footers removed
    """
```

**Implementation Changes**:
- Function already imports `re` module in new file
- Replace exact string matching with regex pattern for Co-Authored-By
- Support case-insensitive matching (use `re.IGNORECASE`)
- Support optional model name variations (Opus 4.5, Sonnet 4.5, etc.)
- Preserve AutoRunner Bot footers (regex only matches `Claude.*<noreply@anthropic.com>`)

**Update Imports**:
- In `commit_operations.py`: Add `from .llm_response_utils import strip_claude_footers`
- Remove original function definition from `commit_operations.py`

## HOW

### Integration Points

**New Module** `llm_response_utils.py`:
```python
import re  # Required for regex pattern matching
```

**Update** `commit_operations.py`:
```python
from .llm_response_utils import strip_claude_footers  # Add import, remove function
```

**No decorator or signature changes** - function signature remains the same.

### Algorithm (Enhanced Footer Detection)

```
PSEUDOCODE for strip_claude_footers():
1. IF message is empty, RETURN empty string
2. Split message into lines
3. Compile regex pattern for Co-Authored-By (case-insensitive):
   Pattern: r'^Co-Authored-By:\s*Claude.*<noreply@anthropic\.com>$'
   Flags: re.IGNORECASE
4. WHILE lines array is not empty:
   a. Get last line and strip whitespace
   b. IF line starts with "🤖" OR matches Co-Authored-By pattern OR is empty:
      - Remove last line from array
   c. ELSE:
      - BREAK (stop removing)
5. Join remaining lines with newlines and RETURN
```

### Implementation Details

**Pattern Matching Logic**:
```python
# Compile regex pattern once (outside loop for efficiency)
co_authored_pattern = re.compile(
    r'^Co-Authored-By:\s*Claude.*<noreply@anthropic\.com>$',
    re.IGNORECASE
)

# In the loop, replace exact string match with regex:
# OLD: last_line == "Co-Authored-By: Claude <noreply@anthropic.com>"
# NEW: co_authored_pattern.match(last_line)
```

**AutoRunner Bot Preservation**:
- The regex pattern `Claude.*<noreply@anthropic\.com>` will NOT match `AutoRunner Bot <autorunner@example.com>`
- No special handling needed - AutoRunner Bot footers naturally preserved

## DATA

### Input

```python
message: str  # Commit message with potential Claude footers
```

### Output

```python
returns: str  # Cleaned message with Claude footers removed
```

### Test Data Examples

**Input 1** (lowercase with model):
```
"feat: add feature\n\nCo-authored-by: Claude Opus 4.5 <noreply@anthropic.com>"
```

**Expected Output 1**:
```
"feat: add feature"
```

**Input 2** (AutoRunner Bot - should be preserved):
```
"feat: add feature\n\nCo-authored-by: AutoRunner Bot <autorunner@example.com>"
```

**Expected Output 2**:
```
"feat: add feature\n\nCo-authored-by: AutoRunner Bot <autorunner@example.com>"
```

**Input 3** (mixed case with Sonnet):
```
"fix: bug fix\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Expected Output 3**:
```
"fix: bug fix"
```

## LLM Implementation Prompt

```
Please implement Step 1 of the plan in pr_info/steps/summary.md.

Context: We are creating a new shared module llm_response_utils.py and moving 
strip_claude_footers() from commit_operations.py to this new module. We will 
enhance it to handle case-insensitive Co-Authored-By patterns with model name variations.

Follow TDD approach:
1. Create src/mcp_coder/workflow_utils/llm_response_utils.py with module docstring and imports
2. Create tests/workflow_utils/test_llm_response_utils.py
3. Move TestStripClaudeFooters class from test_commit_operations.py to new test file
4. Add ~3 new parameterized tests (using @pytest.mark.parametrize) as described in step_1.md
5. Run tests to verify they fail (red phase)
6. Move strip_claude_footers() from commit_operations.py to llm_response_utils.py
7. Enhance the function using regex pattern matching as described in step_1.md
8. Update docstring to reflect case-insensitive matching, model variations, and PR body usage
9. Add import in commit_operations.py: from .llm_response_utils import strip_claude_footers
10. Remove TestStripClaudeFooters class from test_commit_operations.py
11. Run tests to verify they pass (green phase)

Key requirements:
- Use regex pattern: r'^Co-Authored-By:\s*Claude.*<noreply@anthropic\.com>$' with re.IGNORECASE
- Preserve AutoRunner Bot footers (don't remove them)
- Keep backward compatibility with all existing tests (moved to new file)
- Use parameterized tests to reduce duplication
- Update docstring to reflect broader usage (commits + PR bodies)
- Follow the pseudocode algorithm in step_1.md

After implementation, run: mcp__code-checker__run_pytest_check with appropriate markers
to verify all tests pass.
```

## Acceptance Criteria

- [ ] New module `src/mcp_coder/workflow_utils/llm_response_utils.py` created
- [ ] New test file `tests/workflow_utils/test_llm_response_utils.py` created
- [ ] `TestStripClaudeFooters` class moved from `test_commit_operations.py` to new test file
- [ ] ~3 new parameterized tests added (case-insensitive, model variations, AutoRunner preservation)
- [ ] All new tests pass
- [ ] All existing tests still pass (backward compatibility)
- [ ] `strip_claude_footers()` function moved to new module
- [ ] Function handles case-insensitive Co-Authored-By patterns
- [ ] Function handles model name variations (Opus 4.5, Sonnet 4.5, no model)
- [ ] AutoRunner Bot footers are preserved
- [ ] Docstring updated to reflect case-insensitive matching, model variations, and PR body usage
- [ ] Import added to `commit_operations.py`: `from .llm_response_utils import strip_claude_footers`
- [ ] Original function removed from `commit_operations.py`
- [ ] Pytest runs successfully for `test_llm_response_utils.py`
- [ ] Pytest runs successfully for `test_commit_operations.py` (import works)
