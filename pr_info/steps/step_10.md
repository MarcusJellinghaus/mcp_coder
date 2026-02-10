# Step 10: Add Comprehensive Decision Matrix to Module Docstring

## Goal
Add a comprehensive decision matrix and scenario examples to the `orchestrator.py` module docstring that clearly documents all combinations of status, branch state, VSCode state, folder state, and the resulting actions.

## Context
The current module docstring (lines 1-57) explains each concept linearly but doesn't provide a single reference showing all state combinations. Developers and future maintainers need a clear decision matrix to understand "what happens when" for any given combination of states.

## Files to Modify

### `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`

**Add new section after "Status Table Indicators" (around line 50):**

```python
"""
... existing docstring sections ...

Status Table Indicators:
- (active): VSCode is running
- !! No branch: status-04/07 without linked branch
- !! Dirty: Repo has uncommitted changes, can't switch branch
- !! Git error: Git operation failed
- → Needs branch: Eligible issue at status-04/07 needs linked branch
- Blocked (label): Issue has ignore label
- → Delete (with --cleanup): Session is stale
- → Restart: Normal restart needed
- → Create and start: New session can be created

Intervention Sessions:
- Follow same branch rules as normal sessions
- is_intervention flag doesn't affect branch requirements

---

## Decision Matrix: Session Actions by State

### Launch Behavior (New Sessions)

| Status | Branch State | Action | Reason |
|--------|--------------|--------|--------|
| 01:created | No linked | Launch on `main` | Fallback allowed for status-01 |
| 01:created | Has linked | Launch on linked | Use linked branch if available |
| 04:plan-review | No linked | Skip, log error | Branch required for status-04 |
| 04:plan-review | Has linked | Launch on linked | Normal flow |
| 04:plan-review | Multiple linked | Skip, log error | Ambiguous branch state |
| 07:code-review | No linked | Skip, log error | Branch required for status-07 |
| 07:code-review | Has linked | Launch on linked | Normal flow |
| 07:code-review | Multiple linked | Skip, log error | Ambiguous branch state |
| 10:pr-created | Any | No session | PR-created issues don't need sessions |

### Restart Behavior (Existing Sessions)

| Status | Branch | VSCode | Folder | Blocked | Git Fetch | Action | Indicator |
|--------|--------|--------|--------|---------|-----------|--------|-----------|
| 01 | Any | Running | Any | No | - | No action | (active) |
| 01 | Any | Closed | Clean | No | Success | Restart, stay on branch | → Restart |
| 01 | Any | Closed | Dirty | No | Success | Skip | !! Dirty |
| 01 | Any | Closed | Clean | Yes | - | Skip | Blocked (label) |
| 01 | Any | Closed | Clean | No | Failed | Skip | !! Git error |
| 04 | No linked | Closed | Clean | No | Success | Skip | !! No branch |
| 04 | Multiple | Closed | Clean | No | Success | Skip | !! Multi-branch |
| 04 | Has linked | Running | Any | No | - | No action | (active) |
| 04 | Has linked | Closed | Dirty | No | Success | Skip | !! Dirty |
| 04 | Has linked | Closed | Clean | No | Failed | Skip | !! Git error |
| 04 | Has linked | Closed | Clean | No | Success | Checkout + pull + restart | → Restart |
| 04 | Has linked | Closed | Clean | Yes | - | Skip | Blocked (label) |
| 07 | No linked | Closed | Clean | No | Success | Skip | !! No branch |
| 07 | Multiple | Closed | Clean | No | Success | Skip | !! Multi-branch |
| 07 | Has linked | Running | Any | No | - | No action | (active) |
| 07 | Has linked | Closed | Dirty | No | Success | Skip | !! Dirty |
| 07 | Has linked | Closed | Clean | No | Failed | Skip | !! Git error |
| 07 | Has linked | Closed | Clean | No | Success | Checkout + pull + restart | → Restart |
| 07 | Has linked | Closed | Clean | Yes | - | Skip | Blocked (label) |

**Priority Order for Restart Decisions:**
1. VSCode running → (active)
2. Skip reason (no branch/dirty/git error/multi-branch) → !! indicators
3. Blocked label → Blocked (label)
4. Stale (status changed to ineligible) → → Delete (with --cleanup)
5. Normal flow → → Restart

### Status Display (No Existing Session)

| Status | Branch State | Issue State | Indicator |
|--------|--------------|-------------|-----------|
| 01 | Any | Open, eligible | → Create and start |
| 04 | No linked | Open, eligible | → Needs branch |
| 04 | Multiple linked | Open, eligible | → Needs branch |
| 04 | Has linked | Open, eligible | → Create and start |
| 07 | No linked | Open, eligible | → Needs branch |
| 07 | Multiple linked | Open, eligible | → Needs branch |
| 07 | Has linked | Open, eligible | → Create and start |
| 10:pr-created | Any | Open | (No session row) |

---

## Common Scenarios

### Scenario 1: Fresh Planning Session
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Not running
Folder: Does not exist
Action: Create folder, clone, checkout feature/issue-123, launch VSCode
```

### Scenario 2: Planning Approved, Status Changed
```
Initial: Status 04:plan-review on feature/issue-123
User approves plan, status changes to 05:bot-pickup
VSCode: Running
Action: No restart (bot status ineligible), marked stale for cleanup
Display: "→ Delete (with --cleanup)"
```

### Scenario 3: Restart After VSCode Closed
```
Status: 07:code-review
Branch: feature/issue-123 (linked)
VSCode: Closed (user closed it)
Folder: Clean (no uncommitted changes)
Restart flow:
  1. git fetch origin
  2. Get linked branch: feature/issue-123
  3. Check dirty: Clean
  4. git checkout feature/issue-123
  5. git pull
  6. Regenerate session files
  7. Launch VSCode
```

### Scenario 4: Restart Blocked by Uncommitted Work
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Closed
Folder: Dirty (user made changes)
Action: Skip restart
Display: "!! Dirty"
Reason: Can't switch branches with uncommitted changes
```

### Scenario 5: Issue Moved to Code Review, No Branch
```
Status: 07:code-review
Branch: None linked (forgot to link in GitHub)
VSCode: Closed
Action: Skip restart
Display: "!! No branch"
Reason: Status-07 requires linked branch
```

### Scenario 6: Multiple Branches Linked
```
Status: 04:plan-review
Branch: Multiple branches linked to issue in GitHub
VSCode: Closed
Action: Skip restart
Display: "!! Multi-branch"
Reason: Ambiguous which branch to use
Fix: Unlink all but one branch in GitHub
```

### Scenario 7: Status-01 Without Branch
```
Status: 01:created
Branch: No linked branch
VSCode: Not running
Folder: Does not exist
Action: Create folder, clone, checkout main, launch VSCode
Display: "→ Create and start"
Reason: Status-01 allows fallback to main
```

### Scenario 8: Network Failure on Restart
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Closed
Folder: Clean
git fetch origin: FAILS (network down)
Action: Skip restart
Display: "!! Git error"
Reason: Can't proceed without fetch
```

---

## State Transitions

```
NEW ISSUE (status-01:created)
    ├─► Has linked branch → Launch on linked branch
    └─► No linked branch → Launch on main

PLANNING PHASE (status-04:plan-review)
    ├─► Has linked branch + clean → Launch/restart
    ├─► Has linked branch + dirty → Skip (!! Dirty)
    ├─► No linked branch → Skip (!! No branch)
    └─► Multiple branches → Skip (!! Multi-branch)

CODE REVIEW (status-07:code-review)
    ├─► Has linked branch + clean → Launch/restart
    ├─► Has linked branch + dirty → Skip (!! Dirty)
    ├─► No linked branch → Skip (!! No branch)
    └─► Multiple branches → Skip (!! Multi-branch)

PR CREATED (status-10:pr-created)
    └─► No session created (displayed separately)
```
"""
```

## Tests

### File: `tests/workflows/vscodeclaude/test_orchestrator_documentation.py` (NEW)

Create a new test file to validate documentation accuracy:

```python
"""Tests to verify orchestrator documentation matches implementation."""

import pytest
from mcp_coder.workflows.vscodeclaude.orchestrator import (
    _prepare_restart_branch,
    process_eligible_issues,
)
from mcp_coder.workflows.vscodeclaude.issues import status_requires_linked_branch


class TestDocumentationAccuracy:
    """Verify decision matrix documentation matches actual behavior."""
    
    def test_status_01_allows_main_fallback(self):
        """Status-01 allows launching without linked branch (doc scenario 7)."""
        # This is tested via process_eligible_issues behavior
        assert not status_requires_linked_branch("status-01:created")
    
    def test_status_04_requires_linked_branch(self):
        """Status-04 requires linked branch (doc scenario 5)."""
        assert status_requires_linked_branch("status-04:plan-review")
    
    def test_status_07_requires_linked_branch(self):
        """Status-07 requires linked branch (doc scenario 5)."""
        assert status_requires_linked_branch("status-07:code-review")
    
    def test_priority_order_vscode_running_first(self, ...):
        """VSCode running takes priority (doc priority #1)."""
        # Verify get_next_action returns "(active)" when VSCode running
        # regardless of other states
    
    def test_priority_order_skip_reason_before_blocked(self, ...):
        """Skip reason takes priority over blocked label (doc priority #2)."""
        # Verify skip_reason parameter overrides blocked_label
    
    def test_dirty_folder_prevents_restart(self, ...):
        """Dirty folder prevents branch switch on restart (doc scenario 4)."""
        # Test _prepare_restart_branch with dirty folder
    
    def test_git_fetch_failure_prevents_restart(self, ...):
        """Git fetch failure prevents restart (doc scenario 8)."""
        # Test _prepare_restart_branch with mocked failing git fetch
```

## LLM Prompt

```
You are implementing Step 10 of issue #422 branch handling feature.

Reference: pr_info/steps/summary.md for full context
This step: pr_info/steps/step_10.md

Task: Add comprehensive decision matrix documentation to orchestrator.py module docstring.

Implementation order:
1. Read current orchestrator.py module docstring (lines 1-57)
2. Add the new sections after "Intervention Sessions" section
3. Create new test file test_orchestrator_documentation.py
4. Implement tests verifying documentation accuracy
5. Run all quality checks (pylint, pytest, mypy)

The decision matrix should be a definitive reference for understanding ALL
state combinations and their outcomes. Include the complete matrix tables,
common scenarios with examples, and state transition diagram as specified.

Use MCP tools exclusively (no Read/Write/Edit tools).
Run code quality checks after implementation using MCP code-checker tools.
```

## Integration Points

No code changes needed - this is pure documentation enhancement.

**Docstring structure after change:**
```
Session Lifecycle Rules
Branch Handling Rules
Restart Behavior
Branch Verification on Restart
Cleanup Behavior
Dirty Folder Protection
Status Table Indicators
Intervention Sessions
---
Decision Matrix: Session Actions by State    <-- NEW
  - Launch Behavior
  - Restart Behavior
  - Status Display
Common Scenarios                             <-- NEW
  - Scenario 1-8 with examples
State Transitions                            <-- NEW
  - ASCII diagram
```

## Acceptance Criteria

- [ ] Decision matrix tables added to module docstring with all state combinations
- [ ] Common scenarios section added with 8 concrete examples
- [ ] State transitions diagram added showing flow between states
- [ ] Priority order clearly documented for restart decisions
- [ ] New test file validates documentation matches implementation
- [ ] All tests pass
- [ ] Pylint, pytest, mypy all pass
- [ ] Documentation is comprehensive enough that any developer can understand the full business logic

## Commit Message

```
docs(vscodeclaude): add comprehensive decision matrix to orchestrator

Add detailed decision matrix, common scenarios, and state transitions
to orchestrator.py module docstring for complete business logic reference.

- Add launch behavior matrix (status x branch combinations)
- Add restart behavior matrix (status x branch x VSCode x folder x blocked)
- Add status display matrix for new issues
- Document 8 common scenarios with concrete examples
- Add state transition diagram
- Document priority order for restart decisions
- Add tests validating documentation accuracy

This provides a single definitive reference for understanding all
state combinations and their outcomes in the vscodeclaude coordinator.

Part of issue #422: Status-aware branch handling

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
