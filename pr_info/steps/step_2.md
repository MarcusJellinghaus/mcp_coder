# Step 2: Migrate Test Files and Add Import-Linter Contract

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 2.

This step migrates test files to use the subprocess wrapper and adds the 
import-linter contract to enforce the architectural constraint.
```

## Overview

1. Migrate test files that use `subprocess` directly
2. Add import-linter contract to `.importlinter`
3. Verify everything passes

---

## Task 2.1: Migrate `test_issue_manager_label_update.py`

### WHERE
`tests/utils/github_operations/test_issue_manager_label_update.py`

### WHAT
Replace `subprocess.run()` calls for git setup with `execute_command()`.

**Before:**
```python
import subprocess

# In test methods:
subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
subprocess.run(
    ["git", "config", "user.email", "test@example.com"],
    cwd=tmp_path,
    check=True,
    capture_output=True,
)
subprocess.run(
    ["git", "config", "user.name", "Test User"],
    cwd=tmp_path,
    check=True,
    capture_output=True,
)
```

**After:**
```python
from mcp_coder.utils.subprocess_runner import execute_command

# In test methods:
execute_command(["git", "init"], cwd=str(tmp_path))
execute_command(
    ["git", "config", "user.email", "test@example.com"],
    cwd=str(tmp_path),
)
execute_command(
    ["git", "config", "user.name", "Test User"],
    cwd=str(tmp_path),
)
```

### HOW
1. Remove `import subprocess`
2. Add `from mcp_coder.utils.subprocess_runner import execute_command`
3. Replace all `subprocess.run()` calls with `execute_command()`
4. Note: `execute_command()` takes `cwd` as string, not Path

### ALGORITHM
```
For each subprocess.run() call:
1. Replace with execute_command()
2. Convert cwd from Path to str
3. Remove check=True (execute_command doesn't raise by default)
4. Remove capture_output=True (execute_command captures by default)
```

---

## Task 2.2: Remove Unused Import from `test_create_pr_integration.py`

### WHERE
`tests/workflows/test_create_pr_integration.py`

### WHAT
Remove the unused `import subprocess` statement.

**Before (line 4):**
```python
import os
import subprocess  # ← REMOVE (unused)
import tempfile
```

**After:**
```python
import os
import tempfile
```

### HOW
Delete the line `import subprocess`.

---

## Task 2.2b: Remove Unused Import from `test_main.py`

### WHERE
`tests/cli/test_main.py`

### WHAT
Remove the unused `import subprocess` statement.

**Before (line 4):**
```python
import argparse
import subprocess  # ← REMOVE (unused)
import sys
```

**After:**
```python
import argparse
import sys
```

### HOW
Delete the line `import subprocess`.

---

## Task 2.3: Delete Redundant Test from `test_git_encoding_stress.py`

### WHERE
`tests/utils/test_git_encoding_stress.py`

### WHAT
Delete the entire `test_subprocess_encoding_directly()` test method (lines ~243-297).

### WHY
This test directly tests subprocess encoding behavior, which:
1. Is now handled by `subprocess_runner.py`
2. Violates the new architectural constraint
3. Is redundant since the wrapper already handles encoding

### HOW
Delete the entire method:
```python
def test_subprocess_encoding_directly(self) -> None:
    """Test subprocess encoding handling directly without git repository."""
    # ... entire method body ...
```

---

## Task 2.4: Change Exception Imports in Test Files (3 files)

### WHERE
- `tests/llm/providers/claude/test_claude_code_api.py`
- `tests/llm/providers/claude/test_claude_code_api_error_handling.py`
- `tests/llm/providers/claude/test_claude_code_cli.py`

### WHAT
Change import statements to use exceptions from `subprocess_runner`.

**Before:**
```python
import subprocess
# ... later ...
subprocess.TimeoutExpired(...)
subprocess.CalledProcessError(...)
```

**After:**
```python
from mcp_coder.utils.subprocess_runner import CalledProcessError, TimeoutExpired
# ... later ...
TimeoutExpired(...)
CalledProcessError(...)
```

### HOW
For each file:
1. Remove `import subprocess`
2. Add import from `subprocess_runner`
3. Update all `subprocess.TimeoutExpired` → `TimeoutExpired`
4. Update all `subprocess.CalledProcessError` → `CalledProcessError`

### Note
These tests mock/create exception instances for testing error handling. The exception classes are the same - just imported from a different location.

---

## Task 2.5: Add Import-Linter Contract

### WHERE
`.importlinter`

### WHAT
Add new contract at end of file:

```ini
# -----------------------------------------------------------------------------
# Contract: Subprocess Library Isolation
# -----------------------------------------------------------------------------
# The 'subprocess' module should only be used by subprocess_runner.
# All other modules must use subprocess_runner as an abstraction layer.
# This is the first library isolation contract enforced in tests as well.
# -----------------------------------------------------------------------------
[importlinter:contract:subprocess_isolation]
name = Subprocess Library Isolation
type = forbidden
source_modules =
    mcp_coder
    tests
forbidden_modules =
    subprocess
ignore_imports =
    mcp_coder.utils.subprocess_runner -> subprocess
```

### HOW
Append to end of `.importlinter` file, following existing contract format.

### WHY This Contract Design
- `source_modules` includes both `mcp_coder` and `tests` (first contract to do this)
- `forbidden_modules` is `subprocess` (the stdlib module)
- `ignore_imports` allows only `subprocess_runner` to import `subprocess`

---

## Verification

After completing this step:

```bash
# Run import linter
lint-imports

# Expected output: All contracts passed

# Run full test suite
pytest tests/ -v

# Verify no subprocess imports remain (except in subprocess_runner.py)
grep -r "import subprocess" src/ tests/ --include="*.py" | grep -v subprocess_runner.py
# Should return empty
```

---

## Final Checklist

- [ ] `test_issue_manager_label_update.py` uses `execute_command()`
- [ ] `test_create_pr_integration.py` has no subprocess import
- [ ] `test_main.py` has no subprocess import
- [ ] `test_subprocess_encoding_directly` test deleted
- [ ] `test_claude_code_api.py` imports exceptions from `subprocess_runner`
- [ ] `test_claude_code_api_error_handling.py` imports exceptions from `subprocess_runner`
- [ ] `test_claude_code_cli.py` imports exceptions from `subprocess_runner`
- [ ] Import-linter contract added to `.importlinter`
- [ ] `lint-imports` passes
- [ ] All tests pass
