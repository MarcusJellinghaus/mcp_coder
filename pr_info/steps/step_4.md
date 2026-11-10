# Step 4 — Guards against acting on a fresh or `NO_WINDOW` "inactive"

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`), then implement Step 4 only:
> - add `LivenessRule.NO_WINDOW` (not yet produced by `assess_liveness`; Step 5 does that)
> - add `Transition.prior_last_active`
> - add the pure helper `guard_reason`
> - apply it in `decide` (via `_decide_unguarded`) and in `cleanup._retry_to_be_deleted`
> - update the docs
>
> Write the tests first, then the implementation. Run the checks from the summary plus `run_lint_imports_check` and `run_tach_check`, then make one commit.

## Rationale

The guards land before the title becomes authoritative (Step 5), so no commit can `DELETE` a `NO_WINDOW` session or an unconfirmed `NO_MATCH` one. The `NO_WINDOW` override is inert until Step 5 makes `assess_liveness` return that rule; the confirmation guard is live from this step on all platforms.

## WHERE / WHAT

**`src/mcp_coder/workflows/vscodeclaude/types.py`**
- `LivenessRule.NO_WINDOW = "no_window"`.
- `Transition`: add `prior_last_active: bool | None`, with no default.
- `_flatten()["transition"]`: add `"prior_last_active"`.

**`src/mcp_coder/workflows/vscodeclaude/assessment.py`**
- `assess_transition`: `return Transition(flipped_to_inactive=flipped, prior_last_active=prior_last_active)`.
- Rename the current body of `decide` to `_decide_unguarded(...)` with the same signature, unchanged.
- New public pure helper:

  ```python
  NO_WINDOW_REASON = (
      "no window, but VSCode main process still references folder"
      " — close all VSCode windows to release it"
  )
  CONFIRMING_REASON = "just went inactive, confirming next run"

  def guard_reason(
      verdict: LivenessVerdict, transition: Transition, action: SessionAction
  ) -> str | None:
      """Reason to hold back a DELETE/RESTART, or None if it may proceed."""
  ```

- New `decide` (same signature as today):

  ```python
  def decide(verdict, issue_state, transition, git_status, directory_empty) -> Decision:
      decision = _decide_unguarded(verdict, issue_state, transition, git_status, directory_empty)
      if decision.action not in (SessionAction.DELETE, SessionAction.RESTART):
          return decision
      reason = guard_reason(verdict, transition, decision.action)
      if reason is None:
          return decision
      return Decision(action=SessionAction.SKIP, reason=reason, destructive=False)
  ```

  - Existing SKIP reasons (Dirty, unverified git status) keep precedence automatically: those branches never return DELETE or RESTART.
  - `DELETE` is still produced only in `_decide_unguarded`.
  - Docstrings for `decide` / `_decide_unguarded` state this.

**`src/mcp_coder/workflows/vscodeclaude/cleanup.py`** (`_retry_to_be_deleted`)
- After the "folder gone → drop entry" branch, before `safe_delete_folder`:

  ```python
  if assessment is not None:
      reason = guard_reason(assessment.verdict, assessment.transition, SessionAction.DELETE)
      if reason is not None:
          logger.info("Sparing .to_be_deleted entry %s (%s); leaving it queued.", folder_name, reason)
          continue
  ```

- Import `guard_reason` from `.assessment`. `assessment` does not import `cleanup`, so there is no cycle.
- If `run_lint_imports_check` or `run_tach_check` rejects the `cleanup → assessment` import, move `guard_reason` and the two reason constants into `types.py` instead and import them from there in both modules.
- Docstring: mention that queued entries are spared while their verdict is `NO_WINDOW` or not yet confirmed inactive. Entries without an assessment keep today's behaviour.

**Cleanup output for guard-converted restarts (intended).** `get_stale_sessions` (`cleanup.py:63`) drops only `RESTART` decisions. An eligible session whose `RESTART` the confirmation guard turned into `SKIP` therefore reaches `cleanup_stale_sessions`' SKIP branch: it logs/prints `[WARN] Skipping (just went inactive, confirming next run): <folder>` and is counted in `result["skipped"]`. This is intended — cleanup reports every inactive session it did not act on this run, and the line tells the user why. `get_stale_sessions` is not changed. Document it in the `cleanup_stale_sessions` docstring's `SKIP` bullet ("dirty / unverified non-empty / not yet confirmed inactive / no window").

**`docs/coordinator-vscodeclaude.md`** ("Session States" / "Automatic behavior", ~line 135)
- Closed sessions are restarted or deleted one `launch` run after they first go inactive. The first run shows `!! just went inactive, confirming next run` (and cleanup prints a `Skipping` line for it).

## ALGORITHM (`guard_reason`)

```
if action == DELETE and verdict.rule == NO_WINDOW:  return NO_WINDOW_REASON     # override guard
if transition.prior_last_active is not False:      return CONFIRMING_REASON    # confirmation guard
return None
```

## Tests (write first)

**Fixtures (`conftest.py`)**
- `NO_FLIP = Transition(flipped_to_inactive=False, prior_last_active=False)`. Prior `False` = confirmed inactive, so tests that expect DELETE/RESTART keep their meaning.
- Add `make_transition(prior: bool | None) -> Transition`, deriving `flipped_to_inactive` as `assess_transition` does for an inactive verdict.
- `make_assessment` / `make_sample_assessment`: pass `prior_last_active=False`.
- `_build_assessment`: add parameter `prior_last_active: bool | None = False` and pass it to `assess_session`. This keeps `test_status_display_delete_actions.py` / `test_status_display_assessment_consumer.py` meaningful.

**Constructors** — add `prior_last_active=` to every remaining `Transition(...)`:
- `test_audit.py`, `test_cleanup.py` (`_assessment` helper: `False`), `test_closed_issues_integration.py`, `test_status_display_scenario.py`, `test_types.py`.

**`test_assessment_orchestration.py`**
- `test_apply_records_destructive_delete_removed_by_cleanup` and `test_locked_folder_retry_recurs_across_runs` use prior `None`. Set the stored session's `last_active=False` (or pass `prior_last_active=False`) so they still expect DELETE.

**`test_assessment_layers.py`** — parametrized `decide` guard matrix. `NO_WINDOW` verdicts are built directly (`LivenessVerdict(active=False, rule=LivenessRule.NO_WINDOW)`):

| verdict rule | issue | git | prior | expected |
|---|---|---|---|---|
| NO_MATCH | ineligible | Clean | False | DELETE |
| NO_MATCH | ineligible | Clean | True / None | SKIP, `CONFIRMING_REASON` |
| NO_WINDOW | ineligible | Clean | False | SKIP, `NO_WINDOW_REASON` |
| NO_MATCH | eligible | Clean | False | RESTART |
| NO_MATCH | eligible | Clean | True / None | SKIP, `CONFIRMING_REASON` |
| NO_WINDOW | eligible | Clean | False | RESTART |
| NO_WINDOW | eligible | Clean | None | SKIP, `CONFIRMING_REASON` |
| NO_MATCH / NO_WINDOW | any | Dirty | None | SKIP, `"dirty"` |
| NO_ARTIFACTS | any | Missing | None | REMOVE_MISSING |

- Plus `assess_transition` sets `prior_last_active` for `True`, `False` and `None`.
- The existing destructive-invariant test must still pass unchanged (it uses `NO_FLIP`).

**`test_cleanup_retry.py`**
- A queued, present folder whose assessment has rule `NO_WINDOW` (prior `False`) → `safe_delete_folder` not called; entry still in `.to_be_deleted`.
- Same with rule `NO_MATCH` and prior `None` → not deleted, stays queued.
- `NO_MATCH` with prior `False` → deleted (the existing `test_cleanup_retry_inactive_assessment_retries_delete` covers this once its helper uses prior `False`).

**`test_cleanup.py`**
- `cleanup_stale_sessions` with one eligible, inactive `NO_MATCH` session at prior `None` (decision `SKIP`, `CONFIRMING_REASON`): it is in `result["skipped"]`, not deleted, and the printed output contains `Skipping (just went inactive, confirming next run)`.

**`test_audit.py` / `test_explain.py`**
- `prior_last_active` appears in the `transition` block.

## Commit

`feat(vscodeclaude): guard delete/restart on unconfirmed or no-window inactivity`
