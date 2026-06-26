# Step 10 — `--explain` flag (on-demand transparency)

**Read first:** [summary.md](./summary.md) (section "Transparency" surface 2). The
`SessionAssessment.to_explain()` serializer makes this a near-trivial dump.

## WHERE
- Modify: the vscodeclaude CLI argument parser (where `--cleanup`, `--repo`,
  `--max-sessions` are registered — search the coordinator CLI parser module that
  feeds `execute_coordinator_vscodeclaude_*`).
- Modify: `src/mcp_coder/cli/commands/coordinator/commands.py`
  (`execute_coordinator_vscodeclaude_status` and/or launch entrypoint render `--explain`).
- Optional: small renderer `render_explain(assessments)` in
  `src/mcp_coder/workflows/vscodeclaude/assessment.py`.
- Tests: `tests/workflows/vscodeclaude/test_status_display.py` (or a new
  `test_explain.py`).

## WHAT
```python
def render_explain(assessments: dict[str, SessionAssessment]) -> str:
    """One block per session: full DetectionSignals + verdict + rule + transition + action."""
```
CLI: add `--explain` (store_true) to the vscodeclaude `status` (and optionally
`launch`) subcommand.

## HOW
- `--explain` is read-only: it renders the **already-built** assessments
  (`build_assessments` from Step 5) via the shared `SessionAssessment.to_explain()`
  serializer (same source as audit/column — cannot drift). It must **not** trigger
  `apply_assessments` (no writes, no audit) — consistent with status being write-free.
- Print per session: folder, `signals.*` (folder_exists, title_match, cmdline_match,
  pid_alive, found_pid, age_seconds, within_grace, directory_empty), `verdict.active`,
  `verdict.rule`, `decision.action`, `decision.destructive`, `decision.reason`,
  `transition.flipped_to_inactive`.
- When `--explain` is absent, behaviour is unchanged.

## ALGORITHM
```
for folder, a in assessments.items():
    lines.append(a.to_explain())   # e.g. "{folder}: active={verdict.active} "
                                   #      "rule={verdict.rule.value} action={decision.action.value} "
                                   #      "destructive={decision.destructive} "
                                   #      "flip={transition.flipped_to_inactive}\n  signals: {signals}"
return "\n".join(lines)
```

## DATA
Returns a string; CLI prints it. Exit code unchanged (0).

## Tests (write first)
- `render_explain` includes every signal field and the winning rule for a sample
  assessment.
- `--explain` on the status path triggers no disk write (patch `save_sessions` /
  `append_run`, assert not called).
- Parser accepts `--explain`; default `False`.

## Done when
All three checks pass; `docs/coordinator-vscodeclaude.md` Options table updated with
`--explain`. One commit.
