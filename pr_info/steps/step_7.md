# Step 7: Update Module Docstring and Integration Testing

## LLM Prompt

```
Implement Step 7 of Issue #422 (see pr_info/steps/summary.md for full context).

Update the orchestrator.py module docstring to document branch handling logic.
Run final integration tests to verify all acceptance criteria.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | UPDATE docstring |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | ADD integration test |

---

## WHAT

### Updated Module Docstring

Replace the existing docstring at the top of `orchestrator.py`:

```python
"""Session orchestration for vscodeclaude feature.

Main functions for preparing, launching, and managing sessions.

Session Lifecycle Rules:
- Sessions are created for issues at human_action statuses with initial_command
- Eligible statuses: status-01:created, status-04:plan-review, status-07:code-review
- Ineligible: bot_pickup (02, 05, 08), bot_busy (03, 06, 09), pr-created (10)

Branch Handling Rules:
- status-01:created: Use linked branch if exists, fall back to 'main' if not
- status-04:plan-review: REQUIRE linked branch, skip if missing
- status-07:code-review: REQUIRE linked branch, skip if missing

Restart Behavior:
- Every restart runs 'git fetch origin' to sync with remote
- status-01 restarts: Stay on current branch, fetch only
- status-04/07 restarts: Verify linked branch, checkout if different, pull
- Status changes (01→04): Auto-switch to linked branch if repo is clean

Branch Verification on Restart:
1. git fetch origin (always, all statuses)
2. If status-04/07:
   a. Get linked branch from GitHub API
   b. If no linked branch → skip restart, show "!! No branch"
   c. Check repo dirty (git status --porcelain)
   d. If dirty → skip restart, show "!! Dirty"
   e. git checkout <linked_branch>
   f. git pull
   g. If git error → skip restart, show "!! Git error"
3. Update .vscodeclaude_status.txt with branch name
4. Regenerate session files
5. Launch VSCode

Cleanup Behavior:
- Stale sessions (status changed, closed, bot stage, pr-created) eligible for --cleanup
- Dirty folders (uncommitted changes) require manual cleanup, never auto-deleted

Dirty Folder Protection:
- Sessions with uncommitted git changes are never auto-deleted
- Display shows "!! Manual cleanup" for these cases
- Dirty detection: any output from 'git status --porcelain'

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
"""
```

---

## HOW

### Integration Points

1. Replace lines 1-20 of `orchestrator.py` with new docstring
2. Keep all existing code unchanged
3. Add integration test that verifies full flow

---

## INTEGRATION TEST

### File: `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`

Add comprehensive integration test:

```python
class TestBranchHandlingIntegration:
    """Integration tests for branch handling feature."""

    def test_full_session_lifecycle_status_01_to_04(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Test full lifecycle: create at 01, restart when changed to 04."""
        # Phase 1: Create session at status-01 without branch
        mock_issue_01: IssueData = {
            "number": 100,
            "title": "Test Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
        }
        
        # Session created on main (no branch required for status-01)
        # ... mock setup for creation ...
        
        # Phase 2: Issue status changes to status-04, has linked branch
        mock_issue_04: IssueData = {
            "number": 100,
            "title": "Test Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
        }
        
        # Session restart should:
        # 1. Detect status change
        # 2. Run git fetch
        # 3. Get linked branch
        # 4. Check dirty
        # 5. Checkout and pull
        # 6. Update status file
        # 7. Regenerate session files
        # 8. Launch VSCode
        
        # ... verify all steps ...
        pass  # Detailed implementation in actual test

    def test_status_04_session_without_branch_skips_completely(
        self, tmp_path: Path, mocker: MockerFixture, caplog
    ) -> None:
        """Status-04 without branch: doesn't create session, shows indicator."""
        # Verify that:
        # 1. process_eligible_issues skips the issue
        # 2. Log shows error message
        # 3. Status table would show "→ Needs branch"
        pass

    def test_dirty_repo_blocks_branch_switch(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Dirty repo prevents branch switch, shows !! Dirty."""
        # Create a session that needs branch switch
        # Make repo dirty (mock git status --porcelain output)
        # Verify restart is skipped
        # Verify "!! Dirty" would be shown
        pass

    def test_git_fetch_runs_on_every_restart(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """git fetch origin runs on every restart regardless of status."""
        # Test with status-01, status-04, status-07
        # Each should call git fetch as first operation
        pass

    def test_intervention_session_requires_branch_for_status_04(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Intervention sessions follow same branch rules."""
        # Create intervention session at status-04
        # Verify it requires linked branch
        # Verify skip behavior matches normal sessions
        pass
```

---

## ACCEPTANCE CRITERIA VERIFICATION

| Criteria | Test/Verification |
|----------|-------------------|
| `status-01:created` sessions launch on `main` | Step 4 tests |
| `status-04:plan-review` sessions require linked branch | Step 4 tests |
| `status-07:code-review` sessions require linked branch | Step 4 tests |
| New sessions without linked branch show `→ Needs branch` | Step 6 tests |
| `git fetch origin` runs on every restart | Step 3, 5 tests |
| Restart verifies linked branch for status-04/07 | Step 3, 5 tests |
| Session restart runs: fetch → checkout → pull | Step 3, 5 tests |
| Status change auto-switches branch | Step 5 tests |
| Dirty repos show `!! Dirty` | Step 2, 5 tests |
| Missing branch shows `!! No branch` | Step 2, 5 tests |
| Git errors show `!! Git error` | Step 2, 5 tests |
| Status file updated after branch switch | Step 5 tests |
| Intervention sessions follow same rules | Step 5 tests |
| Module docstring documents logic | This step |

---

## FINAL VERIFICATION

Run all vscodeclaude tests:

```bash
pytest tests/workflows/vscodeclaude/ -v --tb=short
```

Run specific feature tests:

```bash
pytest tests/workflows/vscodeclaude/test_issues.py::TestStatusRequiresLinkedBranch -v
pytest tests/workflows/vscodeclaude/test_next_action.py::TestGetNextActionSkipReason -v
pytest tests/workflows/vscodeclaude/test_orchestrator_sessions.py::TestPrepareRestartBranch -v
pytest tests/workflows/vscodeclaude/test_orchestrator_launch.py::TestProcessEligibleIssuesBranchRequirement -v
pytest tests/workflows/vscodeclaude/test_orchestrator_sessions.py::TestRestartClosedSessionsBranchHandling -v
pytest tests/workflows/vscodeclaude/test_status_display.py::TestDisplayStatusTableBranchIndicators -v
```

---

## MANUAL TESTING CHECKLIST

1. [ ] Create issue at status-01, run coordinator → session starts on main
2. [ ] Create issue at status-04 without branch → session NOT started, log shows error
3. [ ] Create issue at status-04 with branch → session starts on branch
4. [ ] Close VSCode for status-01 session → restarts normally
5. [ ] Close VSCode for status-04 session (clean repo) → restarts on branch
6. [ ] Close VSCode for status-04 session (dirty repo) → does NOT restart
7. [ ] Change issue status 01→04 with branch → auto-switches branch on restart
8. [ ] Status table shows correct indicators for each scenario
