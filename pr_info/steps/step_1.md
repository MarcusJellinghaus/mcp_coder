# Step 1: Move source file and update test

## Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md before starting.

Move `branch_status.py` to the `checks/` package and relocate its test file.
This is a pure file move — do NOT change any logic inside the files.

Tasks:
1. Copy `src/mcp_coder/workflow_utils/branch_status.py` to
   `src/mcp_coder/checks/branch_status.py` (no code changes).

2. Copy `tests/workflow_utils/test_branch_status.py` to
   `tests/checks/test_branch_status.py`, then update every import and
   every patch() target string inside it:
     - `mcp_coder.workflow_utils.branch_status` → `mcp_coder.checks.branch_status`
   No other changes.

3. Delete `src/mcp_coder/workflow_utils/branch_status.py`.
4. Delete `tests/workflow_utils/test_branch_status.py`.

Verify: Run pytest tests/checks/test_branch_status.py and confirm all tests pass.
Do NOT yet update any callers (workflow_utils/__init__.py, cli commands, etc.) —
those are handled in step 2.
```

---

## WHERE
| Action | Path |
|---|---|
| Create | `src/mcp_coder/checks/branch_status.py` |
| Create | `tests/checks/test_branch_status.py` |
| Delete | `src/mcp_coder/workflow_utils/branch_status.py` |
| Delete | `tests/workflow_utils/test_branch_status.py` |

## WHAT
No new functions. Exact copy of existing module content.

The only text changes are in `tests/checks/test_branch_status.py`:
- All `from mcp_coder.workflow_utils.branch_status import ...`
  → `from mcp_coder.checks.branch_status import ...`
- All `patch("mcp_coder.workflow_utils.branch_status.XXX")`
  → `patch("mcp_coder.checks.branch_status.XXX")`

## HOW
`src/mcp_coder/checks/branch_status.py` has no new integration points.
Its internal imports (`from mcp_coder.workflow_utils.base_branch import ...`,
`from mcp_coder.utils...`, etc.) are unchanged — those refer to other modules,
not to the file's own location.

## ALGORITHM
```
read  src/mcp_coder/workflow_utils/branch_status.py
write src/mcp_coder/checks/branch_status.py  (identical content)
delete src/mcp_coder/workflow_utils/branch_status.py

read  tests/workflow_utils/test_branch_status.py
replace all occurrences of "workflow_utils.branch_status"
        with               "checks.branch_status"
write tests/checks/test_branch_status.py
delete tests/workflow_utils/test_branch_status.py
```

## DATA
No new data structures. Module exposes the same public API at new path:
- `BranchStatusReport` (frozen dataclass)
- `collect_branch_status(project_dir, truncate_logs, max_log_lines) → BranchStatusReport`
- `create_empty_report() → BranchStatusReport`
- `get_failed_jobs_summary(jobs, logs) → Dict[str, Any]`
- `truncate_ci_details(details, max_lines, head_lines) → str`
- Constants: `CI_PASSED`, `CI_FAILED`, `CI_PENDING`, `CI_NOT_CONFIGURED`, `DEFAULT_LABEL`

## Verification
```
pytest tests/checks/test_branch_status.py
```
All tests must pass. (Callers still import from old path — that breakage is expected
and fixed in step 2.)
