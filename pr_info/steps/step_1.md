# Step 1: Add Failing Test for `status-10:pr-created` Display

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

In `tests/workflows/vscodeclaude/test_status_display.py`, add ONE test method
to the existing `TestStatusDisplay` class.

The test must:
- Create an IssueData dict with label "status-10:pr-created"
- Call display_status_table() with it as an eligible issue (no sessions, no branch info)
- Assert "(awaiting merge)" appears in captured stdout
- Assert "-> Create and start" does NOT appear in captured stdout

Do NOT modify any source files yet. The test should FAIL at this point.
```

---

## WHERE

**File:** `tests/workflows/vscodeclaude/test_status_display.py`  
**Class:** `TestStatusDisplay` (existing — append method at end of class)

---

## WHAT

```python
def test_pr_created_eligible_issue_shows_awaiting_merge(
    self,
    capsys: pytest.CaptureFixture[str],
) -> None:
```

---

## HOW

- No new imports needed — `IssueData`, `display_status_table`, and `pytest` are already imported.
- Uses `capsys` fixture (already used throughout the test file).
- Follows the same pattern as `test_display_status_table_with_eligible_issue` directly above it
  in `TestStatusDisplay`.

---

## ALGORITHM

```
1. Build IssueData dict: number=435, labels=["status-10:pr-created"], state="open"
2. Wrap in eligible_issues list: [("owner/repo", issue)]
3. Call display_status_table(sessions=[], eligible_issues=..., repo_filter=None)
4. Capture stdout with capsys.readouterr()
5. Assert "(awaiting merge)" in captured.out
6. Assert "-> Create and start" not in captured.out
```

---

## DATA

- **Input:** `IssueData` with `labels=["status-10:pr-created"]`
- **Expected stdout contains:** `(awaiting merge)`
- **Expected stdout does NOT contain:** `-> Create and start`
- **Test result at this step:** FAIL (before fix is applied)
