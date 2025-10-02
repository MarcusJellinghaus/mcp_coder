# Step 3: Move Providers Package

## Objective
Move the entire `llm_providers/` directory to `llm/providers/` and update all imports. This consolidates all LLM functionality under the `llm/` package.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 2 moved core modules, all tests passing
- **Current State**: Providers at `src/mcp_coder/llm_providers/`
- **Target State**: Providers at `src/mcp_coder/llm/providers/`

## Files to Move

```
src/mcp_coder/llm_providers/           → src/mcp_coder/llm/providers/
└── claude/
    ├── __init__.py
    ├── claude_cli_verification.py
    ├── claude_code_api.py
    ├── claude_code_cli.py
    ├── claude_code_interface.py
    └── claude_executable_finder.py
```

## Files to Modify

### Source Files (~5 files)
- `src/mcp_coder/__init__.py` - Update provider imports
- `src/mcp_coder/llm/interface.py` - Update provider imports
- `src/mcp_coder/cli/commands/prompt.py` - Update provider imports

### Test Files (~10 files)
- `tests/llm_providers/claude/*.py` - All provider test files need import updates
- `tests/test_module_exports.py` - Update import tests
- `tests/cli/commands/test_prompt.py` - Update provider imports

## Implementation

### WHERE
1. Move directory: `src/mcp_coder/llm_providers/` → `src/mcp_coder/llm/providers/`
2. Update imports in all files that reference provider modules

### WHAT

**Main Functions (no signature changes):**
- All provider functions remain unchanged
- Only import paths change

**Key Import Updates:**
```python
# OLD imports
from mcp_coder.llm_providers.claude.claude_code_interface import ask_claude_code
from mcp_coder.llm_providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.llm_providers.claude.claude_code_api import ask_claude_code_api

# NEW imports
from mcp_coder.llm.providers.claude.claude_code_interface import ask_claude_code
from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.llm.providers.claude.claude_code_api import ask_claude_code_api
```

### HOW

**Step 3.1: Move Directory**
```bash
# Move entire directory (preserve git history)
git mv src/mcp_coder/llm_providers src/mcp_coder/llm/providers
```

**Step 3.2: Update `llm/interface.py` Imports**
```python
# In src/mcp_coder/llm/interface.py
# OLD
from .llm_providers.claude.claude_code_api import ask_claude_code_api
from .llm_providers.claude.claude_code_cli import ask_claude_code_cli
from .llm_providers.claude.claude_code_interface import ask_claude_code

# NEW
from .providers.claude.claude_code_api import ask_claude_code_api
from .providers.claude.claude_code_cli import ask_claude_code_cli
from .providers.claude.claude_code_interface import ask_claude_code
```

**Step 3.3: Update Root `__init__.py`**
```python
# In src/mcp_coder/__init__.py
# OLD
from .llm_providers.claude.claude_code_interface import ask_claude_code
from .llm_providers.claude.claude_executable_finder import (
    find_claude_executable,
    verify_claude_installation,
)

# NEW
from .llm.providers.claude.claude_code_interface import ask_claude_code
from .llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
    verify_claude_installation,
)
```

**Step 3.4: Update `prompt.py` Imports**
```python
# In src/mcp_coder/cli/commands/prompt.py
# OLD
from ...llm_providers.claude.claude_code_api import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    ask_claude_code_api_detailed_sync,
)

# NEW
from ...llm.providers.claude.claude_code_api import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    ask_claude_code_api_detailed_sync,
)
```

**Step 3.5: Update All Import Statements**

Use find/replace pattern:
```bash
# Source files
OLD: from mcp_coder.llm_providers
NEW: from mcp_coder.llm.providers

OLD: from .llm_providers
NEW: from .providers

OLD: from ...llm_providers
NEW: from ...llm.providers

# Test files
OLD: from mcp_coder.llm_providers
NEW: from mcp_coder.llm.providers
```

### ALGORITHM
```
1. Move llm_providers/ → llm/providers/ (git mv)
2. Update llm/interface.py provider imports
3. Update root __init__.py provider imports
4. Update cli/commands/prompt.py provider imports
5. Find and replace import paths in all source files
6. Find and replace import paths in all test files
7. Run provider tests after each update
```

### DATA

**Import Path Mapping:**
```python
{
    "llm_providers.claude": "llm.providers.claude",
    ".llm_providers": ".providers",
    "...llm_providers": "...llm.providers",
}
```

## Testing

### Test Strategy (TDD)

**Test 3.1: Verify Provider Imports**
```python
# tests/llm/providers/test_provider_structure.py (NEW)
def test_providers_package_structure():
    """Verify providers package structure and imports."""
    import mcp_coder.llm.providers
    import mcp_coder.llm.providers.claude
    
    # Verify claude provider modules importable
    from mcp_coder.llm.providers.claude import (
        claude_code_interface,
        claude_code_cli,
        claude_code_api,
    )
    
    assert hasattr(claude_code_interface, 'ask_claude_code')
    assert hasattr(claude_code_cli, 'ask_claude_code_cli')
    assert hasattr(claude_code_api, 'ask_claude_code_api')

def test_public_api_provider_exports():
    """Verify provider functions accessible via public API."""
    from mcp_coder import ask_claude_code
    
    assert callable(ask_claude_code)
```

**Test 3.2: Run Provider Tests**
```bash
# Run all provider tests with new import paths
pytest tests/llm_providers/claude/ -v  # Before move
pytest tests/llm/providers/claude/ -v   # After move (next step)

# Run integration tests (if any)
pytest tests/ -v -m "claude_cli_integration or claude_api_integration"
```

**Test 3.3: Run Full Test Suite**
```bash
# Ensure nothing broke
pytest tests/ -v
```

### Expected Results
- All provider imports resolve correctly
- No import errors in any module
- All provider tests pass unchanged
- Integration tests pass (if applicable)
- Public API still works from root `__init__.py`

## Verification Checklist
- [ ] `llm_providers/` moved to `llm/providers/`
- [ ] `llm/interface.py` provider imports updated
- [ ] Root `__init__.py` provider imports updated
- [ ] `cli/commands/prompt.py` provider imports updated
- [ ] All source file imports updated
- [ ] All test file imports updated (will move in Step 8)
- [ ] Provider structure test passes
- [ ] All provider tests pass
- [ ] Integration tests pass
- [ ] Full test suite passes

## LLM Prompt for Implementation

```
I'm implementing Step 3 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Move the llm_providers/ directory to llm/providers/ and update all imports.

Please:
1. Move the entire directory:
   - llm_providers/ → llm/providers/

2. Update imports in key files:
   - llm/interface.py: Update provider imports
   - src/mcp_coder/__init__.py: Update provider exports
   - cli/commands/prompt.py: Update provider imports

3. Find and replace all import statements:
   - from mcp_coder.llm_providers → from mcp_coder.llm.providers
   - from .llm_providers → from .providers
   - from ...llm_providers → from ...llm.providers

4. Create tests/llm/providers/test_provider_structure.py to verify imports

5. Run all provider tests to verify no regressions

6. Run full test suite

This is an import path change only - no functionality changes.
```

## Next Step
After this step completes successfully, proceed to **Step 4: Extract SDK Utilities**.
