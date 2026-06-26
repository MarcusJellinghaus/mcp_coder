# Step 9 — Audit trail + transition/decision logging

**Read first:** [summary.md](./summary.md) (section "Transparency" surface 3 +
logging). One global file, one run-block per invocation, last-50 ring buffer,
written **only** by `apply()` runs.

## WHERE
- Create: `src/mcp_coder/workflows/vscodeclaude/audit.py`
- Modify: `src/mcp_coder/workflows/vscodeclaude/assessment.py` (`apply_assessments`
  writes the run-block; `build_assessments`/`assess_session` emit log lines)
- Tests: `tests/workflows/vscodeclaude/test_audit.py`,
  `tests/workflows/vscodeclaude/test_assessment.py`

## WHAT
```python
def get_audit_file_path() -> Path:
    """~/.mcp_coder/coordinator_cache/vscodeclaude_audit.json (global, sibling of sessions.json)."""

def append_run(records: list[dict[str, Any]], *, max_runs: int = 50) -> None:
    """Append one run-block, trim to the last max_runs runs (ring buffer), atomic write."""

def assessment_to_record(a: SessionAssessment, session: VSCodeClaudeSession) -> dict[str, Any]:
    """Thin wrapper that delegates to `a.to_audit_record(session)` — the ONE
       serializer (Step 1/3). Do NOT re-flatten here; the audit trail, --explain,
       and the VSCode column must all read the same source so they cannot drift."""
    return a.to_audit_record(session)
```

## HOW
- Reuse the `sessions.json` discipline: `mkdir(parents=True, exist_ok=True)` +
  `write_text(json.dumps(..., indent=2))`. File shape:
  `{"runs": [ {"run_at": iso, "records": [...] }, ... ]}` (newest last), trimmed to 50.
- `apply_assessments(assessments, write_audit=True)` builds one run-block from all
  assessments and calls `append_run` once (a run = one command invocation across all
  repos = one run-block). `write_audit=False` (or the `status` path never calling
  apply) → no record. This satisfies "written only by apply() runs".
- **Decision-line logging** (in `assess_session` or `build_assessments`), reading the
  embedded sub-results:
  `logger.info("assess #%s: verdict=%s rule=%s -> action=%s destructive=%s reason=%s",
  ..., a.verdict.active, a.verdict.rule.value, a.decision.action.value,
  a.decision.destructive, a.decision.reason)` and a `logger.debug(...)` per-signal breakdown.
- **Transition logging:** when `a.transition.flipped_to_inactive`,
  `logger.info("Session #%s flipped active->inactive (was rule=%s)", ...)`.

## ALGORITHM (`append_run`)
```
data = _load()                       # {"runs": [...]} or {"runs": []}
data["runs"].append({"run_at": now_iso(), "records": records})
data["runs"] = data["runs"][-max_runs:]
_atomic_write(get_audit_file_path(), data)
```

## DATA
JSON `{"runs": [{"run_at": str, "records": [record, ...]}]}`; ring buffer ≤ 50 runs.

## Tests (write first)
- `append_run` keeps only the last 50 runs (write 51, assert len == 50, newest kept).
- A run-block contains one record per assessed session with verdict+action+destructive.
- `status` path writes **no** audit record (no apply()).
- `#38`-shaped record: `rule=no_match`/`action=delete`/`destructive=true` is present
  and greppable as a one-glance post-mortem; a locked-folder retry recurs across runs.
- Transition log emitted on a true active→inactive flip; not on `prior_last_active=None`.

## Done when
All three checks pass. One commit.
