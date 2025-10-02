# Step 7: Extract Session Logic

## Objective
Move `parse_llm_method()` from `cli/llm_helpers.py` to `llm/session/resolver.py` and delete the misplaced CLI helper file.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 6 extracted storage functions, all tests passing
- **Current State**: `parse_llm_method()` in `cli/llm_helpers.py` (wrong layer - business logic not CLI)
- **Target State**: Session logic in `llm/session/resolver.py`, `cli/llm_helpers.py` deleted

## Files to Create

```
src/mcp_coder/llm/session/resolver.py  (NEW)
```

## Files to Modify

```
src/mcp_coder/cli/commands/prompt.py    (Update import)
src/mcp_coder/llm/session/__init__.py   (Export function)
```

## Files to Delete

```
src/mcp_coder/cli/llm_helpers.py        (DELETE after moving function)
```

## Implementation

### WHERE
- Move from: `src/mcp_coder/cli/llm_helpers.py`
- Create: `src/mcp_coder/llm/session/resolver.py`
- Update: `src/mcp_coder/llm/session/__init__.py`
- Update: `src/mcp_coder/cli/commands/prompt.py`

### WHAT

**Function to Move:**

`parse_llm_method(llm_method: str) -> tuple[str, str]`

**Signature:** No changes - keep identical

**Reason for Move:**
- This is **business logic** (parsing provider/method strings)
- Not a CLI utility (doesn't parse argparse, doesn't handle CLI concerns)
- Belongs in session management (resolves LLM method strings)

### HOW

**Step 7.1: Create `resolver.py`**

```python
"""Session management and LLM method resolution utilities.

This module provides utilities for resolving session parameters and
parsing LLM method strings into provider/method tuples.
"""

__all__ = [
    "parse_llm_method",
]


def parse_llm_method(llm_method: str) -> tuple[str, str]:
    """Parse llm_method parameter into provider and method.
    
    Args:
        llm_method: Either 'claude_code_cli' or 'claude_code_api'
    
    Returns:
        Tuple of (provider, method)
        - provider: "claude"
        - method: "cli" or "api"
    
    Raises:
        ValueError: If llm_method is not supported
    
    Example:
        >>> provider, method = parse_llm_method("claude_code_api")
        >>> print(provider, method)
        claude api
        
        >>> provider, method = parse_llm_method("claude_code_cli")
        >>> print(provider, method)
        claude cli
    """
    if llm_method == "claude_code_cli":
        return "claude", "cli"
    elif llm_method == "claude_code_api":
        return "claude", "api"
    else:
        raise ValueError(
            f"Unsupported llm_method: {llm_method}. "
            f"Supported: 'claude_code_cli', 'claude_code_api'"
        )
```

**Step 7.2: Update `llm/session/__init__.py`**

```python
"""Session management and resolution utilities."""

from .resolver import parse_llm_method

__all__ = [
    "parse_llm_method",
]
```

**Step 7.3: Update `prompt.py` Import**

```python
# OLD import
from ..llm_helpers import parse_llm_method

# NEW import
from ...llm.session import parse_llm_method
```

**Step 7.4: Delete `cli/llm_helpers.py`**

```bash
# After verifying all imports updated and tests pass
rm src/mcp_coder/cli/llm_helpers.py
```

### ALGORITHM
```
1. Create llm/session/resolver.py
2. Copy parse_llm_method() from cli/llm_helpers.py
3. Update llm/session/__init__.py to export function
4. Update prompt.py import
5. Verify no other files import from cli/llm_helpers.py
6. Delete cli/llm_helpers.py
7. Run tests to verify behavior unchanged
```

### DATA

**Function Signature (unchanged):**
```python
Input:  llm_method: str  # "claude_code_cli" or "claude_code_api"
Output: tuple[str, str]  # ("claude", "cli") or ("claude", "api")
```

**Valid Inputs:**
```python
{
    "claude_code_cli": ("claude", "cli"),
    "claude_code_api": ("claude", "api"),
}
```

## Testing

### Test Strategy (TDD)

**Test 7.1: Verify Function Works in New Location**

```python
# tests/llm/session/test_resolver.py (will be created in Step 10)
# For now, just verify it works

def test_parse_llm_method_basic():
    """Verify parse_llm_method works from new location."""
    from mcp_coder.llm.session import parse_llm_method
    
    # Test valid inputs
    assert parse_llm_method("claude_code_cli") == ("claude", "cli")
    assert parse_llm_method("claude_code_api") == ("claude", "api")
    
    # Test invalid input
    import pytest
    with pytest.raises(ValueError, match="Unsupported llm_method"):
        parse_llm_method("invalid_method")
```

**Test 7.2: Verify Import in prompt.py**

```bash
# Run prompt tests to ensure new import works
pytest tests/cli/commands/test_prompt.py -v
```

**Test 7.3: Verify No Other Files Import Old Location**

```bash
# Search for any remaining imports of cli.llm_helpers
grep -r "from.*cli.llm_helpers" src/
grep -r "from.*cli.llm_helpers" tests/

# Should return no results after update
```

**Test 7.4: Run Full Test Suite**

```bash
pytest tests/ -v
```

### Expected Results
- `parse_llm_method()` works from new location
- `prompt.py` works with new import
- No files import from deleted `cli/llm_helpers.py`
- All existing tests pass
- No behavior changes

## Verification Checklist
- [ ] `resolver.py` created with `parse_llm_method()`
- [ ] Function implementation identical
- [ ] Docstring preserved/enhanced
- [ ] `llm/session/__init__.py` exports function
- [ ] `prompt.py` import updated
- [ ] No other files import from `cli/llm_helpers.py`
- [ ] `cli/llm_helpers.py` deleted
- [ ] Parse function test passes
- [ ] Prompt tests pass
- [ ] Full test suite passes
- [ ] `prompt.py` line count reduced (one less file to maintain)

## LLM Prompt for Implementation

```
I'm implementing Step 7 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Move parse_llm_method() from cli/llm_helpers.py to llm/session/resolver.py and delete the old file.

Please:
1. Create llm/session/resolver.py with parse_llm_method()
   - Copy exact implementation from cli/llm_helpers.py
   - No logic changes

2. Update llm/session/__init__.py to export parse_llm_method

3. Update prompt.py import:
   - OLD: from ..llm_helpers import parse_llm_method
   - NEW: from ...llm.session import parse_llm_method

4. Verify no other files import from cli/llm_helpers.py:
   - grep -r "from.*cli.llm_helpers" src/
   - grep -r "from.*cli.llm_helpers" tests/

5. Delete cli/llm_helpers.py (only if no other imports found)

6. Run tests:
   - pytest tests/cli/commands/test_prompt.py -v
   - pytest tests/ -v

This moves a misplaced function to the correct layer.
```

## Next Step
After this step completes successfully, proceed to **Step 8: Move Core Tests**.
