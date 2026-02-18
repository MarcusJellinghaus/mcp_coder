# Step 1: Add Test and Implement Fix for `status-10:pr-created` Display

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Do both changes together:

1. In `tests/workflows/vscodeclaude/test_status_display.py`, add ONE test method
   to the existing `TestStatusDisplay` class:

   def test_pr_created_eligible_issue_shows_awaiting_merge(
       self,
       capsys: pytest.CaptureFixture[str],
   ) -> None:

   The test must:
   - Create an IssueData dict with label "status-10:pr-created"
   - Call display_status_table() with it as an eligible issue (no sessions, no branch info)
   - Assert "(awaiting merge)" appears in captured stdout
   - Assert "-> Create and start" does NOT appear in captured stdout

2. In `src/mcp_coder/workflows/vscodeclaude/status.py`, inside `display_status_table()`,
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

After both changes, the new test must pass.
```

---

## WHERE

**File 1:** `tests/workflows/vscodeclaude/test_status_display.py`  
**Class:** `TestStatusDisplay` (existing — append method at end of class)

**File 2:** `src/mcp_coder/workflows/vscodeclaude/status.py`  
**Function:** `display_status_table()` — the eligible-issues loop  
**Location:** After the comment `# Print eligible issues not in sessions`, inside the `for repo_name, issue in eligible_issues:` loop, after `needs_branch` is computed.

---

## WHAT

**Test method to add:**

```python
def test_pr_created_eligible_issue_shows_awaiting_merge(
    self,
    capsys: pytest.CaptureFixture[str],
) -> None:
```

**Source change — replace the 2-branch `if/else` with a 3-branch `if/elif/else`:**

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

**Test:**
- No new imports needed — `IssueData`, `display_status_table`, and `pytest` are already imported.
- Uses `capsys` fixture (already used throughout the test file).
- Follows the same pattern as `test_display_status_table_with_eligible_issue` directly above it in `TestStatusDisplay`.

**Source:**
- **Import:** `is_status_eligible_for_session` is already on line 10:
  ```python
  from .issues import is_status_eligible_for_session, status_requires_linked_branch
  ```
- **No other files touched.**
- **No new abstractions, helpers, or constants.**

---

## ALGORITHM

```
Test:
1. Build IssueData dict: number=435, labels=["status-10:pr-created"], state="open"
2. Wrap in eligible_issues list: [("owner/repo", issue)]
3. Call display_status_table(sessions=[], eligible_issues=..., repo_filter=None)
4. Capture stdout with capsys.readouterr()
5. Assert "(awaiting merge)" in captured.out
6. Assert "-> Create and start" not in captured.out

Source fix:
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
