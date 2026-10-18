# Step 6 — round log carries `details`, not just the bare reason code

Part of issue #1183. Read `pr_info/steps/summary.md` first. Depends on Step 5
(so `details` carries the new per-status gate messages when exercised by
these tests).

## Precondition

The dismiss-gate-failure call site in `src/mcp_coder/workflows/review/
core.py` must still compute `reason, details = check_ci_proven_gate(...)` (or
leave `details = None` when the failure came from `_after_steps`) and then
call `write_round_log(..., changes=reason, escalate_reason=reason)` inside
the `if reason:` branch right before `_fail(...)`. If this call site has
moved or changed shape, write one line to `pr_info/.blocked.txt` describing
the mismatch and stop.

## Goal

The committed round log's `**Changes**:` line currently repeats the bare
machine-readable reason code (e.g. `ci_unknown`), even though a
human-readable `details` string (from Gate 2) is already available and goes
into the failure *comment*. Make the round log carry the same detail: pass
`changes=details or reason`. `escalate_reason=reason` is unchanged — the
label transition still keys off the machine-readable code.

## TDD order

1. Add the two tests below to `tests/workflows/review/test_core_gates.py`
   first — they fail against today's `changes=reason`.
2. Change the one `write_round_log` call's `changes=` argument until both
   pass.

## WHERE

`src/mcp_coder/workflows/review/core.py`, inside `run_review_workflow`'s
`body()`, in the `if verdict.decision == "dismiss":` block, the `if reason:`
sub-branch (the one that runs `write_round_log` then `_flush_round_log` then
`return _fail(...)`):

```python
if reason:
    write_round_log(
        project_dir,
        config,
        run_number,
        round_number,
        findings=report,
        decisions=str(verdict),
        changes=reason,
        escalate_reason=reason,
    )
```

## WHAT

No new function signature — `write_round_log`'s own signature in
`review_log.py` is untouched; only the argument value passed to it changes.

## HOW

One-line change: `changes=reason,` → `changes=details or reason,`. `details`
is already in scope at this point in `body()` (set a few lines above, from
either `_after_steps` — always `None` there — or `check_ci_proven_gate`).

## ALGORITHM

Not applicable — a single argument substitution, no new branching.

## DATA

No data-structure change. The round-log markdown file written by
`write_round_log` (`pr_info/{log_stem}_review_log_{n}.md`) now shows the
human-readable detail under `**Changes**:` instead of the bare reason code,
whenever `details` is not `None`.

## Tests to add

`tests/workflows/review/test_core_gates.py` — these run the real
(non-mocked) `write_round_log`/`next_run_number` against `tmp_path` exactly
like the existing tests in this file, then read the resulting log file back:

- `test_gate2_failure_details_reach_round_log` — reuse the existing
  `test_gate2_unprovable_ci_fails_ci_unknown` setup (`env.gate_
  collect_branch_status.return_value = _status(ci_status=CIStatus.UNKNOWN)`,
  `env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]`), run
  `_run(tmp_path)`, then read
  `(tmp_path / "pr_info" / f"{REVIEW_IMPLEMENTATION.log_stem}_review_log_1.md").read_text()`
  and assert the Gate 2 `UNKNOWN` message text (e.g. `"could not be
  collected"`, from Step 5) appears after `"**Changes**:"` — i.e. the full
  detail landed in the round log, not just the literal string `"ci_unknown"`
  on that line.
- `test_after_steps_failure_falls_back_to_bare_reason` — set
  `env.check_and_fix_ci.return_value = False` (so `_after_steps` returns
  `"ci"` and Gate 2 never runs, leaving `details = None`); run
  `_run(tmp_path)`; assert `result == 1`, and that the round-log file's
  `**Changes**:` line is the bare `"ci"` reason (proving the `or reason`
  fallback is exercised, not just the `details`-present path).

## Commit

One commit: the two tests above + the one-line `core.py` change, passing
pylint/pytest/mypy.

## LLM prompt

> Implement Step 6 of `pr_info/steps/summary.md` (issue #1183) exactly as
> described in `pr_info/steps/step_6.md`. Add the two tests first (they must
> fail against today's `changes=reason`), then change that one
> `write_round_log` call in `core.py` to `changes=details or reason`. Do not
> touch `escalate_reason` or any other call site. Run pylint/pytest/mypy;
> all must pass. Make exactly one commit.
