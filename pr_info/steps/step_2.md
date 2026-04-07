# Step 2: Add labels + refactor create_plan.py → package

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## Goal
Add 2 new failure labels to `labels.json`. Convert the single-file `create_plan.py` module into a package with `__init__.py`, `core.py`, `constants.py`, `prerequisites.py`. No logic changes — pure mechanical restructuring. Tests pass with updated patch paths.

## WHERE

### New files
- `src/mcp_coder/workflows/create_plan/__init__.py`
- `src/mcp_coder/workflows/create_plan/core.py`
- `src/mcp_coder/workflows/create_plan/constants.py`
- `src/mcp_coder/workflows/create_plan/prerequisites.py`

### Deleted files
- `src/mcp_coder/workflows/create_plan.py`

### Modified files
- `src/mcp_coder/config/labels.json` — add 2 labels
- `src/mcp_coder/workflows/__init__.py` — may need update for package import
- `tests/workflows/create_plan/test_main.py` — update patch paths
- `tests/workflows/create_plan/test_prerequisites.py` — update patch paths
- `tests/workflows/create_plan/test_branch_management.py` — update patch paths
- `tests/workflows/create_plan/test_prompt_execution.py` — update patch paths
- `tests/workflows/create_plan/test_argument_parsing.py` — update patch paths

## WHAT

### `labels.json` — 2 new entries in `workflow_labels` array
```json
{
  "internal_id": "planning_llm_timeout",
  "name": "status-03f-timeout:planning-llm-timeout",
  "color": "e99695",
  "description": "LLM timed out during planning",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "⏱️",
    "display_name": "PLANNING LLM TIMEOUT",
    "stage_short": "plan-timeout",
    "commands": ["/check_branch_status"]
  }
},
{
  "internal_id": "planning_prereq_failed",
  "name": "status-03f-prereq:planning-prereq-failed",
  "color": "b60205",
  "description": "Planning prerequisites failed",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "❌",
    "display_name": "PLANNING PREREQ FAILED",
    "stage_short": "plan-prereq-fail",
    "commands": ["/check_branch_status"]
  }
}
```

### `constants.py`
```python
from enum import Enum
from dataclasses import dataclass

class FailureCategory(Enum):
    GENERAL = "planning_failed"
    LLM_TIMEOUT = "planning_llm_timeout"
    PREREQ_FAILED = "planning_prereq_failed"

@dataclass(frozen=True)
class WorkflowFailure:
    category: FailureCategory
    stage: str
    message: str
    prompt_stage: int | None = None
    elapsed_time: float | None = None
```

### `prerequisites.py` — moved functions (no changes to logic)
Functions moved from `create_plan.py`:
- `check_prerequisites(project_dir, issue_number) -> tuple[bool, IssueData]`
- `manage_branch(project_dir, issue_number, issue_title, base_branch) -> Optional[str]`
- `check_pr_info_not_exists(project_dir) -> bool`
- `create_pr_info_structure(project_dir) -> bool`
- `resolve_project_dir(project_dir_arg) -> Path`

All imports these functions need move with them.

### `core.py` — moved functions (no changes to logic)
Functions moved from `create_plan.py`:
- `run_create_plan_workflow(...)` — the main orchestrator
- `run_planning_prompts(...)` — LLM prompt execution
- `validate_output_files(project_dir) -> bool`
- `format_initial_prompt(prompt_template, issue_data) -> str`
- `_load_prompt_or_exit(header) -> str` (private helper)
- `PROMPT_3_TIMEOUT` constant

`core.py` imports prerequisites functions from `.prerequisites`.

### `__init__.py` — re-exports
```python
from .core import (
    run_create_plan_workflow,
    run_planning_prompts,
    validate_output_files,
    format_initial_prompt,
)
from .prerequisites import (
    check_prerequisites,
    manage_branch,
    resolve_project_dir,
    check_pr_info_not_exists,
    create_pr_info_structure,
)
# Also re-export private helper used by tests:
from .core import _load_prompt_or_exit
```

### `workflows/__init__.py`
Check if `from . import create_plan` or similar needs updating — currently only imports `create_pr` and `vscodeclaude`. The `create_plan` import happens lazily in CLI, so `workflows/__init__.py` likely needs no change.

## HOW — Test patch path updates

### Pattern
All test patches change from `mcp_coder.workflows.create_plan.<name>` to the submodule where the function is **looked up at runtime**:

| Function | Old patch target | New patch target |
|---|---|---|
| `check_prerequisites` | `...create_plan.check_prerequisites` | `...create_plan.core.check_prerequisites` |
| `manage_branch` | `...create_plan.manage_branch` | `...create_plan.core.manage_branch` |
| `check_pr_info_not_exists` | `...create_plan.check_pr_info_not_exists` | `...create_plan.core.check_pr_info_not_exists` |
| `create_pr_info_structure` | `...create_plan.create_pr_info_structure` | `...create_plan.core.create_pr_info_structure` |
| `run_planning_prompts` | `...create_plan.run_planning_prompts` | `...create_plan.core.run_planning_prompts` |
| `validate_output_files` | `...create_plan.validate_output_files` | `...create_plan.core.validate_output_files` |
| `commit_all_changes` | `...create_plan.commit_all_changes` | `...create_plan.core.commit_all_changes` |
| `git_push` | `...create_plan.git_push` | `...create_plan.core.git_push` |
| `IssueManager` (in core) | `...create_plan.IssueManager` | `...create_plan.core.IssueManager` |
| `is_working_directory_clean` | `...create_plan.is_working_directory_clean` | `...create_plan.prerequisites.is_working_directory_clean` |
| `IssueManager` (in prereqs) | `...create_plan.IssueManager` | `...create_plan.prerequisites.IssueManager` |
| `IssueBranchManager` | `...create_plan.IssueBranchManager` | `...create_plan.prerequisites.IssueBranchManager` |
| `checkout_branch` | `...create_plan.checkout_branch` | `...create_plan.prerequisites.checkout_branch` |
| `logger` (in prereqs tests) | `...create_plan.logger` | `...create_plan.prerequisites.logger` |
| `logger` (in core tests) | `...create_plan.logger` | `...create_plan.core.logger` |
| `get_prompt` | `...create_plan.get_prompt` | `...create_plan.core.get_prompt` |
| `prompt_llm` | `...create_plan.prompt_llm` | `...create_plan.core.prompt_llm` |
| `store_session` | `...create_plan.store_session` | `...create_plan.core.store_session` |

**Important**: `core.py` imports `check_prerequisites`, `manage_branch`, etc. from `.prerequisites`. Patches for `test_main.py` must target `mcp_coder.workflows.create_plan.core.<name>` because that's where `run_create_plan_workflow` looks them up.

## ALGORITHM
```
1. Add 2 new label entries to labels.json (after planning_failed)
2. Create create_plan/ directory with __init__.py
3. Create constants.py with FailureCategory + WorkflowFailure (empty for now, used in step 3)
4. Move prerequisite functions to prerequisites.py with their imports
5. Move orchestration functions to core.py with their imports; add imports from .prerequisites
6. Create __init__.py with re-exports of all 9 public symbols + _load_prompt_or_exit
7. Delete original create_plan.py
8. Update all test patch paths
9. Run tests to confirm no regressions
```

## DATA
No new return types or data structures beyond `FailureCategory` and `WorkflowFailure` (defined but not yet used — that's step 3-4).

## Commit message
```
refactor(create_plan): convert to package, add failure labels

Convert workflows/create_plan.py to workflows/create_plan/ package
mirroring implement's structure (core.py, constants.py, prerequisites.py).
Re-export all public symbols in __init__.py.

Add planning_llm_timeout and planning_prereq_failed labels to labels.json.
Add FailureCategory enum and WorkflowFailure dataclass in constants.py.

Update test patch paths from ...create_plan.* to submodule paths.
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_2.md.

Key points:
- Add 2 new labels to src/mcp_coder/config/labels.json (after the existing planning_failed entry)
- Create the create_plan/ package: __init__.py, core.py, constants.py, prerequisites.py
- Move functions as specified — NO logic changes, just file reorganization
- core.py imports prerequisite functions from .prerequisites
- __init__.py re-exports all 9 public symbols listed in the step
- Delete the original create_plan.py file
- Update ALL test patch paths as specified in the mapping table
- Run all quality checks (pylint, pytest, mypy) and fix any issues
- Verify all existing tests pass with the new structure
```
