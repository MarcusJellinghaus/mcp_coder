# Step 2: Implement the Fix in `display_status_table()`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

In `src/mcp_coder/workflows/vscodeclaude/status.py`, inside `display_status_table()`,
find the eligible-issues loop (the second loop, after "Print eligible issues not in sessions").

Replace:
    if needs_branch:
        action = "-> Needs branch"
    else:
        action = "-> Create and start"

With:
    if needs_branch:
        action = "-> Needs branch"
    elif not is_status_eligible_for_session(status):
        action = "(awaiting merge)"
    else:
        action = "-> Create and start"

No other changes. `is_status_eligible_for_session` is already imported at the top of the file.
After this change the test added in Step 1 must pass.
```

---

## WHERE

**File:** `src/mcp_coder/workflows/vscodeclaude/status.py`  
**Function:** `display_status_table()` — the eligible-issues loop  
**Location:** After the comment `# Print eligible issues not in sessions`, inside the `for repo_name, issue in eligible_issues:` loop, after `needs_branch` is computed.

---

## WHAT

Replace the 2-branch `if/else` with a 3-branch `if/elif/else`:

```python
# BEFORE
if needs_branch:
    action = "-> Needs branch"
else:
    action = "-> Create and start"

# AFTER
if needs_branch:
    action = "-> Needs branch"
elif not is_status_eligible_for_session(status):
    action = "(awaiting merge)"
else:
    action = "-> Create and start"
```

---

## HOW

- **Import:** `is_status_eligible_for_session` is already on line 10:
  ```python
  from .issues import is_status_eligible_for_session, status_requires_linked_branch
  ```
- **No other files touched.**
- **No new abstractions, helpers, or constants.**

---

## ALGORITHM

```
1. Compute needs_branch (existing logic — unchanged)
2. If needs_branch → action = "-> Needs branch"
3. Elif is_status_eligible_for_session(status) is False → action = "(awaiting merge)"
4. Else → action = "-> Create and start"
5. Append row to table (existing logic — unchanged)
```

---

## DATA

- **`is_status_eligible_for_session("status-10:pr-created")`** → `False`
  (because `initial_command` is `null` in `labels.json`)
- **`is_status_eligible_for_session("status-07:code-review")`** → `True`
  (has a non-null `initial_command`)
- **Action mapping:**

  | status | needs_branch | eligible | action |
  |--------|-------------|---------|--------|
  | status-04:plan-review | True | True | `-> Needs branch` |
  | status-10:pr-created | False | False | `(awaiting merge)` |
  | status-07:code-review | False | True | `-> Create and start` |
  | status-01:created | False | True | `-> Create and start` |
