# Implementation Task: Add vulture check to architecture job matrix in `.github/workflows/ci.yml`

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Add vulture check to architecture job matrix in `.github/workflows/ci.yml`

Please implement this task step by step.

## LLM Response:
## Step 3 Complete

**All sub-tasks for Step 3 (Add CI Integration) have been completed:**

- [x] Add vulture check to architecture job matrix in `.github/workflows/ci.yml`
- [x] Verify CI workflow YAML is valid
- [x] Verify local vulture check still passes
- [x] Run pylint check and fix any issues
- [x] Run pytest and fix any failures
- [x] Run mypy check and fix any issues
- [x] Prepare git commit message

### Changes Made

**File modified:** `.github/workflows/ci.yml`

Added vulture to the architecture job matrix:
```yaml
- {name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 60"}
```

### Prepared Commit Message

```
ci: add vulture dead code check to architecture job matrix

Add vulture to the CI architecture checks that run on pull requests.
This enforces dead code detection with 60% minimum confidence threshold,
using the whitelist file for known false positives.

The vulture check will:
- Run as part of the architecture matrix (PR-only)
- Fail if dead code is detected above 60% confidence
- Check both src and tests directories
- Use vulture_whitelist.py for API completeness exclusions
```

---
Generated on: 2026-01-15T08:56:37.059891