# Step 5 — `_issue_facts` helper + `assess_issue_state` wiring (IssueFacts production)

**Read first:** [summary.md](./summary.md) (sections "The pipeline", R1, R2 observe/apply).
This is the first half of the observe/apply hinge: produce a frozen `IssueFacts` per
session from cached issue data, reusing today's eligibility logic so the assessment
layer classifies issues identically to `get_stale_sessions`. Step 5b then wires the
orchestration (`build_assessments`/`apply_assessments`) on top of it.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/assessment.py`
- Tests: `tests/workflows/vscodeclaude/test_assessment.py`

## WHAT
```python
def _issue_facts(
    session: VSCodeClaudeSession,
    cached_issue: IssueData | None,
    *,
    github_username: str | None,
    ignore_labels: list[str],
    cached_for_stale_check: dict[int, IssueData] | None,
) -> IssueFacts:
    """Derive frozen IssueFacts from cached issue data.

    Replicates the eligibility logic of get_stale_sessions
    (cleanup.py:99-180): closed/blocked/ineligible/unassigned, plus
    is_session_stale — feeding assess_issue_state in Step 3.
    """
```

## HOW
- Extract the ~80-line eligibility block from `get_stale_sessions`
  (`cleanup.py:99-180`) into this helper: the `is_closed` / blocked-label /
  status-eligibility / assignment checks, including the **individual-issue API
  fallback** (`get_all_cached_issues(..., additional_issues=[issue_number])`) when an
  issue is missing from the cache, and the `github_username`-gated assignment check.
- **MUST preserve the current short-circuit:** compute `is_session_stale` **only**
  when the session is not closed/blocked/unassigned/ineligible (mirror the
  `cleanup.py:174-180` `and`-chain). Calling `is_session_stale` on a
  closed/blocked/etc. issue triggers the spurious staleness warning the current code
  explicitly guards against — do not regress this.
- Reuse the existing helpers (`is_issue_closed` / `get_matching_ignore_label`,
  `is_status_eligible_for_session`, `is_session_stale`); do not re-implement them.
- The resulting `IssueFacts` is then classified by `assess_issue_state` (Step 3) —
  this step only *produces* the facts; `build_assessments` (Step 5b) consumes them.
- `stale_target` is populated for the reason string exactly as today's code derives it.

## DATA
Frozen `IssueFacts` (Step 1/Step 3 shape).

## Tests (write first)
- `_issue_facts` maps a closed issue → `is_closed=True`, and (short-circuit) does
  **not** call `is_session_stale` (patch it, assert not called).
- Blocked / ineligible / unassigned each map to the matching `IssueFacts` flag, and
  each short-circuits `is_session_stale`.
- Eligible, assigned, open issue → `is_session_stale` **is** called; result flows to
  `is_stale`.
- Issue missing from cache → individual-issue API fallback is invoked
  (patch `get_all_cached_issues`, assert called with `additional_issues=[issue_number]`).
- `IssueFacts` round-trips through `assess_issue_state` (Step 3) to the expected
  `IssueState` for each combo.

## Done when
All three checks pass. One commit.
