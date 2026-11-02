# Step 6 — Review uses the LLM fallback; hand-off shows the LLM reason

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md` only.
> Write the tests first, then the implementation. Run pylint, pytest (fast unit
> set, `-n auto`), mypy and lint-imports until they pass, run `run_format_code`,
> and make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/review/steps.py` (`_after_steps`)
- `src/mcp_coder/workflows/review/handoff.py` (`_route_to_human`)
- New test file: `tests/workflows/review/test_after_steps_llm_rebase.py`
  (`test_core_after_steps.py` is near the line limit; only update its patch target)

## WHAT

No new functions. `_after_steps` keeps its signature and return shape.

## HOW

- `_after_steps`: replace `_attempt_rebase_and_push(project_dir)` with
  `rebase_with_llm_fallback(project_dir, provider, mcp_config)` — no settings override:
  the job's broader `settings_file` is deliberately not used for the rebase (it is
  still passed to `check_and_fix_ci`). Remove the "#1266's follow-up" comment and
  update the docstring (rebase gate = git-only, then LLM rebase).
- Existing tests patching `steps._attempt_rebase_and_push` now patch
  `steps.rebase_with_llm_fallback`.
- `_route_to_human`: after the `Next step` field append
  `("LLM rebase", rebase.llm_detail if rebase is not None else None)`.
  `_REBASE_HANDOFF` stays unchanged. Docstring mentions the field.

## ALGORITHM

```
outcome = rebase_with_llm_fallback(project_dir, provider, mcp_config)
if not outcome.ok:
    log warning; return "rebase", outcome, None
...CI gate unchanged (polls get_latest_commit_sha, which the helper pushed)...
```

## DATA

Unchanged: `(reason, outcome, detail)`.

## Tests

- `_after_steps` calls the helper with provider / mcp_config and no settings override;
  non-ok → `("rebase", outcome, None)`; ok → CI gate runs.
- `_route_to_human` with `RebaseOutcome("conflict", "main", "abc1234", llm_detail="binary conflict in x.png")`
  → comment contains `LLM rebase` and the detail, plus the unchanged Category / Next step.
- Without `llm_detail` no `LLM rebase` line appears.
