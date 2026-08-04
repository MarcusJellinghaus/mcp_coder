# Step 4 — `_fail` gains an optional `details` param

**Read first:** `pr_info/steps/summary.md` (§ "`_fail` gains an optional
`details`"). This step makes the failure comment able to name a cause. It is
backward compatible — no caller passes `details` yet, so behaviour is unchanged
until Steps 5/6.

## WHERE

- **Modified:** `src/mcp_coder/workflows/review/handoff.py`
- **Modified test:** `tests/workflows/review/test_handoff.py`

## WHAT

Add a keyword-only `details` parameter to `_fail`:

```python
def _fail(
    config: ReviewConfig,
    project_dir: Path,
    reason: str,
    *,
    update_issue_labels: bool,
    post_issue_comments: bool,
    round_number: int | None = None,
    verdict: Verdict | None = None,
    elapsed: float | None = None,
    details: str | None = None,   # NEW
) -> int:
```

## HOW / integration points

- Insert `details` into `comment_lines` **immediately after** the `❌ {message}`
  header and **before** the Round / Verdict / Elapsed lines, so the cause reads
  first. Update the docstring's Args section.

## ALGORITHM (comment assembly)

```
comment_lines = [f"❌ {message}"]
if details is not None:
    comment_lines.append(details)
if round_number is not None: comment_lines.append(f"Round: {round_number}")
if verdict is not None:      comment_lines.append(f"Verdict: {verdict.decision}")
if elapsed is not None:      comment_lines.append(f"Elapsed: {format_elapsed_time(elapsed)}")
```

## DATA

Return value unchanged: always `1`. Comment body gains one optional line.

## TDD — `tests/workflows/review/test_handoff.py`

- With `details="X"`, patch `handle_workflow_failure` and assert the passed
  `comment_body` has the `❌ …` header on line 1 and `X` on line 2 (before
  `Round:`/`Verdict:`/`Elapsed:`).
- With `details=None` (default), assert the comment body is identical to the
  pre-change output (no blank/extra line) — proves backward compatibility.

## Checks

pylint / pytest / mypy green.

## Commit

`Add optional details line to review failure comments`
