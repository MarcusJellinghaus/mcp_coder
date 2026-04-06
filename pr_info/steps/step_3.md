# Step 3: Update formatters and recommendations with N/A blocker logic

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context. This step updates `format_for_human()`, `format_for_llm()`, and `_generate_recommendations()` to handle all `TaskTrackerStatus` values with correct icons, inline reasons, and N/A blocker logic. Write tests first, then implement. Run all quality checks after.

## WHERE

- `src/mcp_coder/checks/branch_status.py` — update formatter methods and recommendations function
- `tests/checks/test_branch_status.py` — add formatter and recommendation tests for each status

## WHAT

### `format_for_human()` task section

Replace the boolean-based icon/text with status-aware logic:

```python
# Icon mapping based on status and tasks_is_blocking
tasks_icon_map = {
    TaskTrackerStatus.COMPLETE: "✅",
    TaskTrackerStatus.INCOMPLETE: "❌",
    TaskTrackerStatus.ERROR: "⚠️",
}
if self.tasks_status == TaskTrackerStatus.N_A:
    tasks_icon = "⚠️" if self.tasks_is_blocking else "➖"
else:
    tasks_icon = tasks_icon_map.get(self.tasks_status, "❓")

tasks_status_text = self.tasks_status.value  # "COMPLETE", "INCOMPLETE", "N_A", "ERROR"

# Show reason inline
f"Task Tracker: {tasks_icon} {tasks_status_text} ({self.tasks_reason})"
```

### `format_for_llm()` task section

```python
tasks_line = f"Tasks={self.tasks_status.value} ({self.tasks_reason})"
```

### `_generate_recommendations()` update

```python
tasks_status = report_data.get("tasks_status")
tasks_reason = report_data.get("tasks_reason", "")
tasks_is_blocking = report_data.get("tasks_is_blocking", False)

if tasks_status == TaskTrackerStatus.INCOMPLETE:
    recommendations.append(f"Complete remaining tasks ({tasks_reason})")
elif tasks_status == TaskTrackerStatus.N_A and tasks_is_blocking:
    recommendations.append(f"Fix task tracker: {tasks_reason}")
elif tasks_status == TaskTrackerStatus.ERROR:
    recommendations.append(f"Fix task tracker error: {tasks_reason}")

# Update the "ready to merge" check
tasks_ok = not tasks_is_blocking
```

## HOW

- Use `self.tasks_is_blocking` / `report_data.get("tasks_is_blocking")` directly for icon selection and recommendation logic (no keyword-based detection needed)
- Update `format_for_human()` method in `BranchStatusReport`
- Update `format_for_llm()` method in `BranchStatusReport`
- Update `_generate_recommendations()` function
- Import `TaskTrackerStatus` is already done from step 2

## DATA

- No new data structures
- `tasks_is_blocking` field used directly (no helper needed)
- Formatter output strings change as described in issue's expected behavior table

## TESTS

### Formatter tests in `tests/checks/test_branch_status.py`

1. **`test_format_human_tasks_complete`** — shows `✅ COMPLETE (all 5 tasks complete)`
2. **`test_format_human_tasks_incomplete`** — shows `❌ INCOMPLETE (3 of 5 tasks complete)`
3. **`test_format_human_tasks_na_non_blocking`** — shows `➖ N_A (no pr_info folder)`
4. **`test_format_human_tasks_na_blocking`** — shows `⚠️ N_A (implementation plan exists but no TASK_TRACKER.md)`
5. **`test_format_human_tasks_error`** — shows `⚠️ ERROR (could not read task tracker: ...)`
6. **`test_format_llm_tasks_with_reason`** — shows `Tasks=INCOMPLETE (3 of 5 tasks complete)`
7. **`test_format_llm_tasks_na`** — shows `Tasks=N_A (no pr_info folder)`

### Recommendation tests

8. **`test_recommendations_tasks_incomplete`** — includes "Complete remaining tasks (3 of 5 tasks complete)"
9. **`test_recommendations_tasks_na_non_blocking`** — no task recommendation, can show "Ready to merge" if CI ok
10. **`test_recommendations_tasks_na_blocking`** — includes "Fix task tracker: ..."
11. **`test_recommendations_tasks_error`** — includes "Fix task tracker error: ..."
12. **`test_recommendations_ready_to_merge_with_na_non_blocking`** — N/A + CI passed + no rebase → "Ready to merge"

### Parameterized scenario test

Recommended: add a parameterized test that maps all 8 scenarios from the issue's expected behavior table to expected `(status, reason, is_blocking, icon)` tuples. This ensures every row in the table is covered and makes it easy to add new scenarios.

## COMMIT

```
feat(branch-status): add N/A blocker logic to formatters and recommendations

Part of #676 — formatters now show context-dependent icons (➖ for
non-blocking N/A, ⚠️ for blocking N/A/ERROR) and inline reasons.
Recommendations distinguish blocking vs non-blocking N/A states.
```
