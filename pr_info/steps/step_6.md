# Step 6 — Orchestrator rewrite, marker-machinery removal, OUTPUT logging

Rewire `run_rebase_workflow` around the pieces from Steps 1–5, delete the outcome-marker
machinery atomically with its prompt section, and add user-visible progress output.
See [summary.md](./summary.md) ("Design change", "CLI output").

## WHERE

- Modify: `src/mcp_coder/workflows/rebase.py` (rewrite orchestrator; delete dead code;
  update module docstring — it still describes the marker contract)
- Modify: `src/mcp_coder/prompts/prompts.md` (delete the `## Automated Rebase` section)
- Modify: `tests/workflows/rebase/test_workflow.py` (rework)
- Modify: `tests/workflows/rebase/test_prompt.py` (drop "Automated Rebase" tests)
- Delete: `tests/workflows/rebase/test_decision.py` (covers only removed functions)

## WHAT — deletions

`_parse_outcome_marker`, `_evaluate_pre_push`, `_OUTCOME_RE`, `_REASON_RE`,
`_VALID_OUTCOMES`, `_run_rebase_session`, `_SESSION_TIMEOUT`, `_REBASE_PROMPT_HEADER`,
and the "Automated Rebase" prompt section. Keep unchanged: `_preflight`,
`_resolve_base_branch`, `_check_pr_info_absent_on_base`, `_run_git`, `_GitResult`,
`_is_rebase_in_progress`, `_abort_rebase`, `_reset_hard`, `_rebase_success_shape`.

## WHAT — constants

```python
_MAX_SAME_FILE_CONFLICTS = 3   # /rebase abort rule 4
_MAX_FIX_ATTEMPTS = 2          # /rebase abort rule 5
```

## ALGORITHM — `run_rebase_workflow` (signature unchanged)

```
guards (unchanged): _preflight → _resolve_base_branch → fetch_remote →
    _check_pr_info_absent_on_base → needs_rebase no-op short-circuit → pre_sha
OUTPUT log: "Rebasing <branch> onto origin/<base>..." at the very start

baseline:
    OUTPUT "Running baseline checks (pytest, pylint, mypy)..."
    try: baseline = _run_all_checks(project_dir)
    except CheckRunError → log error, exit 2          # no git mutation yet
    if baseline: OUTPUT f"{len(baseline)} pre-existing failure(s) in baseline — "
                        "these will not block the rebase"

try:
    session_id = None; env_vars = prepare_llm_environment(project_dir)
    conflict_counts = Counter(); stop = 0
    result = _run_git(dir, "rebase", f"origin/{base}")
    while result.returncode != 0:                     # conflict stop
        if not _is_rebase_in_progress(dir): abort → exit 1   # unexpected rebase error
        files = _conflicted_files(dir)
        if not files:
            if _run_git(dir, "diff", "--cached", "--quiet").returncode == 0:
                # resolved commit became empty (all changes already on base)
                OUTPUT "Skipping commit made redundant by rebase (already on base)..."
                result = _run_git(dir, "rebase", "--skip"); continue
            abort → exit 1                            # other non-conflict failure
        if _binary_conflict(dir): abort → exit 1      # rule 2
        conflict_counts.update(files)
        if any count >= _MAX_SAME_FILE_CONFLICTS: abort → exit 1   # rule 4
        pr_info_files = [f for f in files if f.startswith("pr_info/")]
        for f in pr_info_files:
            if not _resolve_pr_info_conflict(dir, f): abort → exit 1
        others = files - pr_info_files
        if others:
            OUTPUT "Resolving N conflicted file(s) via LLM..."
            stop += 1
            text, session_id = _prompt_in_session(
                _build_conflict_prompt(dir, others), session_id, ...,
                step_name=f"conflict_{stop}")
            if any(_has_conflict_markers(dir, f) for f in others): abort → exit 1  # rule 3
        result = _stage_all_and_continue(dir)

    OUTPUT "Verifying no regression..."
    regressions = _run_all_checks(dir) - baseline     # CheckRunError → caught below
    attempt = 0; last_text = None
    while regressions and attempt < _MAX_FIX_ATTEMPTS:
        text = _format_failure_keys(regressions)
        if text == last_text: break                   # stall guard: one string, one ==
        last_text = text; attempt += 1
        OUTPUT f"Fixing {len(regressions)} regression(s) (attempt {attempt}/2)..."
        _, session_id = _prompt_in_session(
            _build_regression_fix_prompt(text), session_id, ...,
            step_name=f"fix_{attempt}")
        run_format_code(dir); _run_git(dir, "add", "-A")
        _run_git(dir, "commit", "-m", f"fix: resolve regressions from rebase onto origin/{base}")
        regressions = _run_all_checks(dir) - baseline
    if regressions: _reset_hard(dir, pre_sha) → exit 1

    if not _rebase_success_shape(dir, pre_sha): → exit 1   # git corroboration gate
    OUTPUT "Force-pushing (with lease)..."
    push (unchanged): success → OUTPUT result, exit 0
                      rejected → _reset_hard(pre_sha), exit 2
except CheckRunError → _reset_hard(dir, pre_sha); log error, exit 1
                                                  # verification/re-check infra failure:
                                                  # the rebase already completed, so the
                                                  # finally net cannot restore — explicit
                                                  # reset to pre_sha is required
except Exception → log error, exit 1                  # LLM/unexpected; finally net cleans up
finally: if _is_rebase_in_progress(dir): _abort_rebase(dir)   # unchanged safety net
```

Notes:

- "abort → exit 1" paths log the concrete observed reason at OUTPUT level (Python
  observes; no LLM self-report) and rely on the `finally` net for `git rebase --abort`.
- Fast path check: no conflicts + empty regression set ⇒ `prompt_llm` is never called.
- `OUTPUT` comes from `mcp_coder.utils.log_utils`; use `logger.log(OUTPUT, ...)`.
  Final line always states the result (pushed / aborted + reason / error).
- Empty-commit edge in the fix loop: if the LLM changed nothing, the commit exits
  non-zero — harmless (re-check runs anyway; identical regressions then hit the stall
  guard or attempt cap).
- Empty-commit stop in the conflict loop (decided: auto-skip): when a resolution
  takes the base's version wholesale, the replayed commit becomes empty and
  `git rebase --continue` refuses with "nothing to commit" while staying mid-rebase.
  Python detects the state deterministically (mid-rebase, no conflicted files,
  `git diff --cached --quiet` clean) and runs `git rebase --skip`, logging at OUTPUT
  that the commit was skipped as redundant, then continues the loop. Only this
  specific case skips; any other non-conflict `--continue` failure still aborts.
- Fix-prompt detail: `_format_failure_keys` output carries file/code/message for
  pylint/mypy but only node IDs for pytest (no tracebacks — keys must stay
  line-insensitive and deterministic for the stall guard). The "Rebase Regression
  Fix" prompt therefore instructs the LLM to re-run the granted MCP check tools for
  full failure detail before editing (see step_4.md).

## DATA

Exit codes unchanged: `0` success/no-op, `1` needs-human (abort/regression/LLM failure),
`2` error (guards, baseline infra, push rejected).

## TDD

Rework `tests/workflows/rebase/test_workflow.py` first (mock at the existing boundary:
`_run_git`-level helpers, wrappers/`_run_all_checks`, `prompt_llm`/`_prompt_in_session`,
`git_push`, guard helpers — keep the file's current fixture style):

1. Fast path: clean rebase, empty baseline/verification → push called, exit 0, **no
   LLM call**.
2. Baseline `CheckRunError` → exit 2, no `git rebase` invoked.
3. `pr_info/`-only conflict → auto-resolved, no LLM call.
4. Mixed conflict → LLM called with inlined context; markers remaining after LLM →
   exit 1; markers gone → continue.
5. Binary conflict → exit 1. Same file at 3 stops → exit 1.
5a. Empty-commit stop (continue fails, no conflicted files, staged diff clean) →
    `git rebase --skip` invoked, loop continues, exit 0; same state but staged diff
    dirty → abort, exit 1.
6. Regression fixed on attempt 1 → commit made, exit 0. Identical failure text on
   attempt 2 → stall guard, reset to `pre_sha`, exit 1. Still failing after 2 attempts
   → reset, exit 1.
7. Verification `CheckRunError` → reset, exit 1.
8. Push rejected → reset, exit 2 (existing test survives with new mocks).
9. Session threading: `session_id` from first LLM response passed to second call.
10. OUTPUT logging: caplog at OUTPUT level sees start/end lines.

Also: delete `test_decision.py`; remove "Automated Rebase" assertions from
`test_prompt.py` (add an assertion the section is gone).

## Commit

One commit. Suggested message:
`feat: rebase workflow executes git in Python; LLM only for conflicts/regressions (#1085)`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement `pr_info/steps/step_6.md`
> exactly: rewrite `run_rebase_workflow` in `src/mcp_coder/workflows/rebase.py` per the
> step's pseudocode, delete the marker machinery and `_run_rebase_session` (and the
> "Automated Rebase" section in `src/mcp_coder/prompts/prompts.md`), add OUTPUT-level
> progress logging, and update the module docstring. Rework
> `tests/workflows/rebase/test_workflow.py` first (TDD), delete
> `tests/workflows/rebase/test_decision.py`, and update `test_prompt.py`. Preserve the
> exit-code contract (0/1/2), the `finally` abort net, and the fast path with zero LLM
> calls. Run pylint, pytest, and mypy via the MCP check tools, plus
> `mcp-coder check file-size --max-lines 750`, and fix any findings before finishing.
