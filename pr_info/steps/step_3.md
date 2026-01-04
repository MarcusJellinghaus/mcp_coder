# Step 3: Move CLI Handlers and Templates to commands.py

## Objective
Move CLI entry point functions and all command templates/constants from coordinator.py to commands.py, establishing the clean separation between CLI interface and business logic.

## LLM Prompt
```
Based on summary.md, implement Step 3 of the coordinator module refactoring. Move CLI entry point functions (execute_coordinator_test, execute_coordinator_run) and all command templates/constants from coordinator.py to commands.py. Import business logic functions from core.py as needed. Preserve exact functionality and maintain test compatibility.
```

## Implementation Details

### WHERE (Files)
- **Source**: `src/mcp_coder/cli/commands/coordinator.py`
- **Target**: `src/mcp_coder/cli/commands/coordinator/commands.py`

### WHAT (Functions and Constants to Move)
**CLI Entry Points:**
```python
def execute_coordinator_test(args: argparse.Namespace) -> int
def execute_coordinator_run(args: argparse.Namespace) -> int
def format_job_output(job_path: str, queue_id: int, url: Optional[str]) -> str
```

**Command Templates and Constants:**
```python
# All template constants (~300 lines)
DEFAULT_TEST_COMMAND: str
DEFAULT_TEST_COMMAND_WINDOWS: str
CREATE_PLAN_COMMAND_WINDOWS: str
IMPLEMENT_COMMAND_WINDOWS: str
CREATE_PR_COMMAND_WINDOWS: str
CREATE_PLAN_COMMAND_TEMPLATE: str
IMPLEMENT_COMMAND_TEMPLATE: str
CREATE_PR_COMMAND_TEMPLATE: str

# Template mappings
TEST_COMMAND_TEMPLATES: Dict[str, str]
PRIORITY_ORDER: List[str]
WORKFLOW_MAPPING: Dict[str, Dict[str, str]]
```

### HOW (Integration Points)
**Imports for commands.py:**
```python
import argparse
import sys
from typing import Optional

from .core import (
    create_default_config,
    get_config_file_path,
    load_repo_config,
    validate_repo_config,
    get_jenkins_credentials,
    get_cached_eligible_issues,
    get_cache_refresh_minutes,
    dispatch_workflow,
    WORKFLOW_MAPPING,  # If moved to core, otherwise keep in commands
)
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.jenkins_operations.models import JobStatus
from ....utils.github_operations.issue_manager import IssueManager
from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.github_utils import RepoIdentifier
```

### ALGORITHM (CLI Functions Logic)
**execute_coordinator_test:**
1. Auto-create config if needed (via core.create_default_config)
2. Load and validate repo config (via core functions)
3. Get Jenkins credentials (via core.get_jenkins_credentials)
4. Select OS-appropriate command template
5. Create JenkinsClient and trigger job
6. Return exit code

**execute_coordinator_run:**
1. Auto-create config if needed
2. Determine repository list (single vs all mode)  
3. For each repo: load config, create managers, get eligible issues
4. Dispatch workflows using core.dispatch_workflow
5. Return exit code with error handling

### DATA (Function Signatures)
- **execute_coordinator_test**: `(args: argparse.Namespace) -> int`
- **execute_coordinator_run**: `(args: argparse.Namespace) -> int`  
- **format_job_output**: `(job_path: str, queue_id: int, url: Optional[str]) -> str`

**Template Data:**
- All command template strings preserved exactly
- Dictionary mappings for OS selection and workflows
- Priority ordering list maintained

## Test Strategy
**Test File Updates:**
1. Update imports in `tests/cli/commands/test_coordinator.py` to import CLI functions from `coordinator.commands`
2. Update imports for business logic functions to come from `coordinator.core`
3. Verify all existing test cases pass without logic changes

**Import Examples:**
```python
# In test_coordinator.py
from mcp_coder.cli.commands.coordinator.commands import (
    execute_coordinator_test,
    execute_coordinator_run,
    format_job_output,
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
)
from mcp_coder.cli.commands.coordinator.core import (
    load_repo_config,
    validate_repo_config,
    get_jenkins_credentials,
    # Other core functions...
)
```

## Success Criteria
- [x] All CLI entry point functions moved to commands.py with exact logic
- [x] All command templates and constants moved to commands.py  
- [x] Commands.py properly imports needed functions from core.py
- [x] No circular dependencies between commands.py and core.py
- [x] All existing tests pass with updated imports
- [x] CLI functions can execute business logic through core module imports

## Dependencies
- **Requires**: Step 2 completion (core.py contains all business logic)
- **Provides**: Complete separation of CLI interface from business logic
- **Next**: Step 4 will update all remaining import references and finalize the refactoring