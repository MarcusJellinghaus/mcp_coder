# Step 4: Update polling logic in `core.py` and `check_branch_status.py`

> **Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE
- **Source:** `src/mcp_coder/workflows/implement/core.py`
- **Source:** `src/mcp_coder/cli/commands/check_branch_status.py`
- **Test:** `tests/workflows/implement/test_ci_check.py` (verify existing tests still pass)
- **Test:** `tests/cli/commands/test_check_branch_status.py` (verify existing tests still pass)
- **Test:** `tests/cli/commands/test_check_branch_status_ci_waiting.py` (verify existing tests still pass)

## WHAT — Changes in `core.py`

### 1. `_poll_for_ci_completion()` — line ~265
Currently reads: `run_info = ci_status.get("run", {})`
Then checks: `run_info.get("status")`, `run_info.get("conclusion")`, `run_info.get("id")`

**Changes:**
- `run_info.get("status")` — **no change** (now aggregate status)
- `run_info.get("conclusion")` — **no change** (now aggregate conclusion)
- `run_info.get("id")` → `run_info.get("run_ids")` for logging only

### 2. `_wait_for_new_ci_run()` — line ~306
Currently compares: `new_run_id = new_status.get("run", {}).get("id")`
Against: `previous_run_id` (single int)

**Change:**
```python
# Before:
new_run_id = new_status.get("run", {}).get("id")
if new_run_id and new_run_id != previous_run_id:

# After:
new_run_ids = set(new_status.get("run", {}).get("run_ids", []))
if new_run_ids and not new_run_ids.issubset(previous_run_ids):
```

**Signature change:**
```python
# Before:
def _wait_for_new_ci_run(ci_manager, branch, previous_run_id: Any) -> tuple[...]:

# After:
def _wait_for_new_ci_run(ci_manager, branch, previous_run_ids: set[int]) -> tuple[...]:
```

### 3. `check_and_fix_ci()` — line ~380
Currently: `failed_run_id = ci_status.get("run", {}).get("id")`

**Change:**
```python
# Before:
failed_run_id = ci_status.get("run", {}).get("id")
# ... later:
new_status, new_run_detected = _wait_for_new_ci_run(ci_manager, branch, failed_run_id)
# ... and:
failed_run_id = ci_status.get("run", {}).get("id")

# After:
failed_run_ids = set(ci_status.get("run", {}).get("run_ids", []))
# ... later:
new_status, new_run_detected = _wait_for_new_ci_run(ci_manager, branch, failed_run_ids)
# ... and:
failed_run_ids = set(ci_status.get("run", {}).get("run_ids", []))
```

### 4. `_run_ci_analysis_and_fix()` — line ~331
Currently: `run_id = ci_status.get("run", {}).get("id")`
Used for: `ci_manager.get_run_logs(run_id)`

**Change (Decision 3):** Fetch logs from failed jobs' run_ids, not blindly from first run:
```python
# Before:
run_id = ci_status.get("run", {}).get("id")
logs = ci_manager.get_run_logs(run_id) if run_id else {}

# After:
jobs_data = ci_status.get("jobs", [])
failed_jobs = [j for j in jobs_data if j.get("conclusion") == "failure"]
failed_run_ids = list(dict.fromkeys(j["run_id"] for j in failed_jobs))
logs: Dict[str, str] = {}
for rid in failed_run_ids[:3]:
    try:
        logs.update(ci_manager.get_run_logs(rid))
    except Exception as e:
        logger.warning(f"Failed to get logs for run {rid}: {e}")
```

## WHAT — Changes in `check_branch_status.py`

### 1. `_wait_for_ci_completion()` — line ~57
Currently: `run_info = ci_status.get("run", {})`
Then checks: `run_info.get("status")`, `run_info.get("conclusion")`

**No changes needed** — reads `status` and `conclusion` which are now aggregate values.

### 2. `_run_auto_fixes()` — line ~205
Currently:
```python
old_run_id = old_status.get("run", {}).get("id")
# ... later:
new_run_id = new_status.get("run", {}).get("id")
if new_run_id and new_run_id != old_run_id:
```

**Change:**
```python
old_run_ids = set(old_status.get("run", {}).get("run_ids", []))
# ... later:
new_run_ids = set(new_status.get("run", {}).get("run_ids", []))
if new_run_ids and not new_run_ids.issubset(old_run_ids):
```

## HOW — Integration
- No new imports needed
- Set comparison is inline (no helper function — it's a one-liner)
- Existing tests should pass if their mocked `run` dicts are updated (may need `run_ids` key)

## DATA
No return type changes. Functions return same types as before.

## ALGORITHM
The polling comparison is:
```
old_ids = set of run IDs from previous status
new_ids = set of run IDs from current status
new_run_started = new_ids is not empty AND new_ids has IDs not in old_ids
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 4 from pr_info/steps/step_4.md.

Update polling logic in two files:
1. src/mcp_coder/workflows/implement/core.py — change run["id"] to run["run_ids"] in
   _wait_for_new_ci_run(), check_and_fix_ci(), _run_ci_analysis_and_fix(), _poll_for_ci_completion()
2. src/mcp_coder/cli/commands/check_branch_status.py — change run["id"] to run["run_ids"]
   in _run_auto_fixes()

Then run the existing tests in tests/workflows/implement/test_ci_check.py,
tests/cli/commands/test_check_branch_status.py, and
tests/cli/commands/test_check_branch_status_ci_waiting.py.
Fix any test fixtures that reference run["id"] to use run["run_ids"] instead.
All tests must pass.
```
