# Implementation Summary: `mcp-coder coordinator run`

## Overview

Implement automated coordinator command that monitors GitHub issues and triggers Jenkins workflows based on issue labels. This automates the issue → plan → implement → PR pipeline.

## Architectural Changes

### Design Philosophy: KISS Principle
- **Extend existing `coordinator.py`** (currently 260 lines) with ~100 new lines
- **Reuse existing patterns** from `coordinator test` command
- **No new directories** - all logic in single command module
- **Simple data structures** - plain dicts and lists, no complex OOP

### Component Design

**Modified Files (4):**
1. `src/mcp_coder/cli/commands/coordinator.py` - Add coordinator run logic (~100 lines)
2. `src/mcp_coder/cli/main.py` - Wire up CLI routing (~10 lines)
3. `workflows/label_config.py` - Add `build_label_lookups()` function (~30 lines)
4. `src/mcp_coder/utils/github_operations/base_manager.py` - Support `repo_url` parameter (~20 lines)

**Extended Tests (2):**
1. `tests/cli/commands/test_coordinator.py` - Add TestCoordinatorRun class (~200 lines)
2. `workflows/validate_labels.py` - Update import to use shared `build_label_lookups()`

**Total New Code: ~360 lines**

### Key Functions Added

```python
# Note: Uses shared build_label_lookups() from workflows/label_config.py
# No new label config function needed - reuse existing functionality

# 2. Issue filtering (30 lines)
def get_eligible_issues(issue_manager: IssueManager, log_level: str) -> list[IssueData]:
    """Get issues ready for automation, sorted by priority."""

# 3. Workflow dispatch (40 lines)
def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,
    repo_config: dict[str, str],
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str
) -> None:
    """Trigger Jenkins job and update label."""

# 4. Main orchestrator (60 lines)
def execute_coordinator_run(args: Namespace) -> int:
    """Execute coordinator run command."""
```

### Data Structures

**Label Mapping (Constant):**
```python
WORKFLOW_MAPPING = {
    "status-02:awaiting-planning": {
        "workflow": "create-plan",
        "branch_strategy": "main",
        "next_label": "status-03:planning"
    },
    "status-05:plan-ready": {
        "workflow": "implement",
        "branch_strategy": "from_issue",
        "next_label": "status-06:implementing"
    },
    "status-08:ready-pr": {
        "workflow": "create-pr",
        "branch_strategy": "from_issue",
        "next_label": "status-09:pr-creating"
    }
}

PRIORITY_ORDER = [
    "status-08:ready-pr",
    "status-05:plan-ready", 
    "status-02:awaiting-planning"
]
```

**Command Templates (Three separate constants for each workflow):**
```python
# Template 1: create-plan (runs on main branch)
CREATE_PLAN_COMMAND_TEMPLATE = """
git checkout main
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo
"""

# Template 2: implement (runs on feature branch)
IMPLEMENT_COMMAND_TEMPLATE = """
git checkout {branch_name}
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo
"""

# Template 3: create-pr (runs on feature branch)
CREATE_PR_COMMAND_TEMPLATE = """
git checkout {branch_name}
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo
"""
```

### Integration Points

**Reused Components:**
- `JenkinsClient` - Job triggering and status verification
- `IssueManager` - GitHub issue querying and label updates
- `IssueBranchManager` - Branch resolution for implement/create-pr
- `load_repo_config()` - Repository configuration loading
- `get_jenkins_credentials()` - Jenkins authentication

**New Integrations:**
- Use `build_label_lookups()` from `workflows/label_config.py` for label filtering
- Query GitHub issues via `IssueManager.list_issues(state="open")`
- Instantiate managers with `repo_url` (using refactored `BaseGitHubManager`)
- Filter issues by labels and exclusion rules
- Map labels to workflows and trigger Jenkins jobs

## Error Handling Strategy

**Phase 1: Simple Fail-Fast**
- Stop processing on **any** error during issue processing
- Jenkins job trigger failure → exit 1
- Job status verification failure → exit 1  
- Label update failure → exit 1
- Missing linked branch → exit 1

**Rationale:** KISS principle - advanced error handling can be added later if needed.

## Implementation Steps

### Step 0: Refactor Shared Components (TDD)
- **Test:** Move `build_label_lookups()`, add `repo_url` support to `BaseGitHubManager`
- **Implement:** Refactor shared functionality
- **Duration:** 45 min

### Step 1: Label Configuration Integration
- **Test:** Use `build_label_lookups()` from shared module
- **Implement:** Import and use existing functionality
- **Duration:** 15 min

### Step 2: Issue Filtering Logic (TDD)
- **Test:** Filter issues by labels, priority sorting, exclusions
- **Implement:** `get_eligible_issues()` function
- **Duration:** 45 min

### Step 3: Workflow Dispatcher (TDD)
- **Test:** Build params, trigger job, verify status, update label
- **Implement:** `dispatch_workflow()` function
- **Duration:** 60 min

### Step 4: Main Coordinator Runner (TDD)
- **Test:** Orchestrate repo processing, error handling
- **Implement:** `execute_coordinator_run()` function
- **Duration:** 60 min

### Step 5: CLI Integration
- **Test:** Command routing and argument parsing
- **Implement:** Wire up in `main.py`, add subcommand parser
- **Duration:** 30 min

### Step 6: Integration Testing
- **Test:** End-to-end with mocked GitHub/Jenkins APIs
- **Implement:** Full workflow validation
- **Duration:** 45 min

**Total Estimated Duration: 4.5-5.5 hours**

## Testing Strategy

### Unit Tests (in `test_coordinator.py`)
- `TestLoadLabelConfig` - Label parsing from JSON
- `TestGetEligibleIssues` - Filtering and priority logic
- `TestDispatchWorkflow` - Job triggering and label updates
- `TestExecuteCoordinatorRun` - Main orchestration

### Integration Tests
- Mock GitHub API (issue queries, label updates)
- Mock Jenkins API (job triggering, status checks)
- Test --all and --repo modes
- Test fail-fast error handling

### Coverage Target: >85%

## Success Criteria

- ✅ Queries issues by repository (--all or --repo)
- ✅ Filters by bot_pickup labels (status-02, 05, 08)
- ✅ Excludes ignore_labels
- ✅ Processes in priority order (08 → 05 → 02)
- ✅ Triggers correct Jenkins job per workflow
- ✅ Uses correct branch strategy per workflow
- ✅ Verifies job queued before updating labels
- ✅ Updates labels bot_pickup → bot_busy
- ✅ Stops on first error (fail-fast)
- ✅ Passes log level through to workflows
- ✅ All tests pass (pylint, pytest, mypy)

## Files to Create/Modify

### Create:
- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md` - Label config loading
- `pr_info/steps/step_2.md` - Issue filtering
- `pr_info/steps/step_3.md` - Workflow dispatcher
- `pr_info/steps/step_4.md` - Main coordinator
- `pr_info/steps/step_5.md` - CLI integration
- `pr_info/steps/step_6.md` - Integration tests

### Modify:
- `workflows/label_config.py` - Add `build_label_lookups()` function
- `workflows/validate_labels.py` - Update import
- `src/mcp_coder/utils/github_operations/base_manager.py` - Add `repo_url` support
- `src/mcp_coder/cli/commands/coordinator.py` - Add ~100 lines
- `src/mcp_coder/cli/main.py` - Add coordinator run subcommand
- `tests/cli/commands/test_coordinator.py` - Add ~200 lines
- `pr_info/TASK_TRACKER.md` - Track implementation progress

## Dependencies

**Existing:**
- `JenkinsClient` - src/mcp_coder/utils/jenkins_operations/client.py
- `IssueManager` - src/mcp_coder/utils/github_operations/issue_manager.py
- `IssueBranchManager` - src/mcp_coder/utils/github_operations/issue_branch_manager.py
- `label_config.py` - workflows/label_config.py (read labels.json)
- `labels.json` - workflows/config/labels.json

**No New Dependencies Required**

## Future Enhancements (Out of Scope)

- Differentiated debugging per workflow
- Continue on issue-specific errors
- Concurrency control via label locking
- Workflow retry and backoff logic
- Metrics and monitoring dashboard
- Audit logs for label changes
- Loop mode support
- Status labels for failures

## References

- Issue #147: Implement `mcp-coder coordinator run`
- Existing: `coordinator test` command (pattern to follow)
- Labels: `workflows/config/labels.json` (label definitions)
- Decisions: `pr_info/steps/decisions.md` (architectural decisions log)
