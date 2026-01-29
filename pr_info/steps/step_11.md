# Step 11: Test Refactoring to Match Utils Package Structure

## LLM Prompt

```
You are implementing Step 11 of the vscodeclaude feature. Read pr_info/steps/architecture_vscodeclaude.md for context.

This step splits the large test file (2873 lines) to match the refactored source structure in utils/vscodeclaude/.

The test file tests/cli/commands/coordinator/test_vscodeclaude.py violates:
1. File size limit (750 lines max)
2. Doesn't match new module structure in utils/vscodeclaude/

Split into:
- tests/utils/vscodeclaude/test_types.py - TestTypes, TestTypeHints
- tests/utils/vscodeclaude/test_sessions.py - TestSessionManagement
- tests/utils/vscodeclaude/test_config.py - TestConfiguration
- tests/utils/vscodeclaude/test_issues.py - TestIssueSelection
- tests/utils/vscodeclaude/test_workspace.py - TestWorkspaceSetup, TestGitOperations
- tests/utils/vscodeclaude/test_orchestrator.py - TestLaunch, TestOrchestration
- tests/utils/vscodeclaude/test_status.py - TestStatusDisplay
- tests/utils/vscodeclaude/test_cleanup.py - TestCleanup
- tests/cli/commands/coordinator/test_vscodeclaude_cli.py - TestTemplates, TestCLI, TestCommandHandlers

Update imports from old CLI path to new utils module paths.
Also fix monkeypatch path in test_process_eligible_issues_respects_max_sessions.

After changes, run all code quality checks and fix any issues.
```

## Overview

Refactor the monolithic test file to match the new modular source code structure, ensuring all files stay under 750 lines.

---

## Task 1: Create tests/utils/vscodeclaude Directory

### WHERE
- `tests/utils/vscodeclaude/`

### WHAT
Create new directory and `__init__.py` for the test package.

### HOW
```bash
mkdir -p tests/utils/vscodeclaude
touch tests/utils/vscodeclaude/__init__.py
```

---

## Task 2: Split Test Classes by Module

### MAPPING

| Test Class | Source Module | Target Test File |
|------------|---------------|------------------|
| TestTypes | types.py | test_types.py |
| TestTypeHints | types.py | test_types.py |
| TestTemplates | vscodeclaude_templates.py | test_vscodeclaude_cli.py |
| TestSessionManagement | sessions.py | test_sessions.py |
| TestConfiguration | config.py | test_config.py |
| TestIssueSelection | issues.py | test_issues.py |
| TestWorkspaceSetup | workspace.py | test_workspace.py |
| TestGitOperations | workspace.py | test_workspace.py |
| TestLaunch | orchestrator.py | test_orchestrator.py |
| TestOrchestration | orchestrator.py | test_orchestrator.py |
| TestCLI | commands.py | test_vscodeclaude_cli.py |
| TestCommandHandlers | commands.py | test_vscodeclaude_cli.py |
| TestStatusDisplay | status.py | test_status.py |
| TestCleanup | cleanup.py | test_cleanup.py |

---

## Task 3: Update Imports

### OLD IMPORTS (from CLI layer)
```python
from mcp_coder.cli.commands.coordinator.vscodeclaude import (
    VSCodeClaudeSession,
    load_sessions,
    ...
)
```

### NEW IMPORTS (from utils modules)
```python
from mcp_coder.utils.vscodeclaude.types import (
    VSCodeClaudeSession, VSCodeClaudeSessionStore, ...
)
from mcp_coder.utils.vscodeclaude.sessions import (
    load_sessions, save_sessions, add_session, ...
)
from mcp_coder.utils.vscodeclaude.config import (
    load_vscodeclaude_config, get_github_username, ...
)
# etc. for each module
```

---

## Task 4: Fix Monkeypatch Path

### WHERE
- `test_process_eligible_issues_respects_max_sessions`

### WHAT
Fix monkeypatch path from `sessions.get_active_session_count` to `orchestrator.get_active_session_count`.

### WHY
When a function is imported directly (not via module attribute), you must patch where it's **used**, not where it's **defined**.

### BEFORE
```python
monkeypatch.setattr(
    "mcp_coder.utils.vscodeclaude.sessions.get_active_session_count",
    lambda: 2,
)
```

### AFTER
```python
monkeypatch.setattr(
    "mcp_coder.utils.vscodeclaude.orchestrator.get_active_session_count",
    lambda: 2,
)
```

---

## Task 5: Delete Original Test File

### WHERE
- `tests/cli/commands/coordinator/test_vscodeclaude.py`

### WHAT
Delete the original monolithic test file after all test classes have been migrated.

---

## Verification

After all changes:
1. Run `mcp__code-checker__run_pytest_check` with `-n auto` and exclusion markers
2. Run `mcp__code-checker__run_pylint_check`
3. Run `mcp__code-checker__run_mypy_check`
4. Run `mcp-coder check file-size --max-lines 750` to verify all files under limit
5. Fix any issues found

## Results

New test file structure (all under 750 lines):

| File | Lines | Test Classes |
|------|-------|--------------|
| test_types.py | 169 | TestTypes, TestTypeHints |
| test_sessions.py | 333 | TestSessionManagement |
| test_config.py | 155 | TestConfiguration |
| test_issues.py | 277 | TestIssueSelection |
| test_workspace.py | 418 | TestWorkspaceSetup, TestGitOperations |
| test_orchestrator.py | 526 | TestLaunch, TestOrchestration |
| test_status.py | 335 | TestStatusDisplay |
| test_cleanup.py | 257 | TestCleanup |
| test_vscodeclaude_cli.py | 400 | TestTemplates, TestCLI, TestCommandHandlers |
