# Step 4: Update Test Patches

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #358.

Implement Step 4: Update all test files to patch at the new import locations.

Tests stay in their current directories (test file reorganization 
happens in a follow-up PR). Only patch paths need updating.
```

---

## WHERE

### Test Files to Update
- `tests/utils/vscodeclaude/test_*.py` - Update patches from utils to workflows
- `tests/cli/commands/coordinator/test_core.py` - Update get_cache_refresh_minutes patches
- Any other tests patching vscodeclaude or cache function

---

## WHAT

### Patch Path Changes

| Old Patch Path | New Patch Path |
|----------------|----------------|
| `mcp_coder.utils.vscodeclaude.X` | `mcp_coder.workflows.vscodeclaude.X` |
| `mcp_coder.cli.commands.coordinator.get_cache_refresh_minutes` | `mcp_coder.utils.user_config.get_cache_refresh_minutes` |
| `mcp_coder.cli.commands.coordinator.vscodeclaude.X` | `mcp_coder.workflows.vscodeclaude.X` |

---

## HOW

### Pattern: Update @patch Decorators

**Before:**
```python
@patch("mcp_coder.utils.vscodeclaude.core.IssueManager")
def test_something(mock_manager):
    ...
```

**After:**
```python
@patch("mcp_coder.workflows.vscodeclaude.core.IssueManager")
def test_something(mock_manager):
    ...
```

### Pattern: Update patch() Context Managers

**Before:**
```python
with patch("mcp_coder.cli.commands.coordinator.get_cache_refresh_minutes") as mock:
    ...
```

**After:**
```python
with patch("mcp_coder.utils.user_config.get_cache_refresh_minutes") as mock:
    ...
```

---

## ALGORITHM

```
1. Search for all patches containing "vscodeclaude":
   grep -r "vscodeclaude" tests/

2. Search for patches of get_cache_refresh_minutes:
   grep -r "get_cache_refresh_minutes" tests/

3. For each match:
   - Replace utils.vscodeclaude → workflows.vscodeclaude
   - Replace coordinator.get_cache_refresh_minutes → utils.user_config.get_cache_refresh_minutes

4. Run tests to verify patches work correctly
```

---

## DATA

### Common Patch Targets

Functions/classes commonly patched in vscodeclaude tests:
- `IssueManager` - Mock GitHub issue operations
- `IssueBranchManager` - Mock branch resolution
- `load_labels_config` - Mock label configuration
- `get_config_values` - Mock user config reads
- `get_cache_refresh_minutes` - Mock cache settings

### Patch Location Rule

Always patch where the name is **used**, not where it's **defined**:

```python
# If workflows/vscodeclaude/core.py has:
from mcp_coder.utils.github_operations.issue_manager import IssueManager

# Patch at the usage location:
@patch("mcp_coder.workflows.vscodeclaude.core.IssueManager")
```

---

## Verification

After this step:
```bash
# Run all tests
mcp__code-checker__run_pytest_check

# Or run specific test directories
pytest tests/utils/vscodeclaude/ -v
pytest tests/cli/commands/coordinator/ -v
```

All tests should pass with the new patch paths.

---

## Note

Test file reorganization (moving test files to match new source locations) will happen in a **follow-up PR** as stated in the issue. This step only updates patch paths within existing test files.
