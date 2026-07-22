# Step 6 — Orchestrator `run_rebase_workflow`

Goal: the public entry point that composes guards → no-op short-circuit → LLM
session → worst-case-wins mapping → Python force-push → `finally` safety net, and
returns the `0/1/2` exit code. One commit.

## WHERE
- MODIFY `src/mcp_coder/workflows/rebase.py` (add the public function + a private
  session helper).
- CREATE `tests/workflows/rebase/test_workflow.py` (mocks — no real LLM/network).

## WHAT
```python
def run_rebase_workflow(
    project_dir: Path,
    provider: str,
    base_branch: str | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    execution_dir: Path | None = None,
) -> int:
    """Orchestrate the automated rebase. Returns 0 (success/no-op),
    1 (aborted → needs-human), or 2 (error / push rejected)."""
```
Optional private helper `_run_rebase_session(...) -> str` wrapping the single
`prompt_llm` call and returning response text (raises on LLM error/timeout).

## HOW
- Imports: `prompt_llm`, `LLMTimeoutError` (`mcp_coder.llm.interface`);
  `prepare_llm_environment` (`mcp_coder.llm.env`); `get_prompt`
  (`mcp_coder.prompt_manager`); `PROMPTS_FILE_PATH` (`mcp_coder.constants`);
  `needs_rebase`, `fetch_remote`, `get_latest_commit_sha`, `git_push`
  (`mcp_coder.mcp_workspace_git`); `get_branch_name_for_logging`
  (`mcp_coder.utils.git_utils`); Steps 3–5 helpers.
- Single `prompt_llm` call, `timeout=600` (inactivity budget, like create_plan),
  forwarding `provider`, `settings_file`, `mcp_config`,
  `execution_dir` (as `str` or None), `env_vars`, `branch_name`. Append the
  resolved `base_branch` to the prompt so the LLM rebases onto `origin/<base>`.
- `settings_file` is already resolved by the CLI layer (Step 7); forward as-is.

## ALGORITHM
```
if (err := _preflight(project_dir)): log; return 2
base, berr = _resolve_base_branch(project_dir, base_branch); if berr: log; return 2
fetch_remote(project_dir, "origin")
if (err := _check_pr_info_absent_on_base(project_dir, base)): log; return 2
needed, reason = needs_rebase(project_dir)
if not needed: log("already current"); return 0
pre_sha = get_latest_commit_sha(project_dir)
try:
    text = _run_rebase_session(project_dir, base, provider, ...)   # prompt_llm
    outcome, mreason = _parse_outcome_marker(text)
    decision = _evaluate_pre_push(
        mid_rebase=_is_rebase_in_progress(project_dir),
        marker_outcome=outcome,
        rebase_success_shape=_rebase_success_shape(project_dir, pre_sha),
    )
    if decision == "abort":
        logger.error("Rebase aborted (needs human): %s", mreason or reason)
        return 1
    result = git_push(project_dir, force_with_lease=True)
    if result["success"]:
        return 0
    logger.error("Force-push rejected/failed: %s", result.get("error"))
    _reset_hard(project_dir, pre_sha)      # never leave unpushed rebased commits
    return 2
except (LLMTimeoutError, Exception) as e:
    logger.error("Rebase session failed: %s", e)
    return 1                               # needs-human; finally makes it retry-safe
finally:
    if _is_rebase_in_progress(project_dir):
        _abort_rebase(project_dir)
```

## DATA
- Returns `int` exit code `{0,1,2}`.
- `git_push(...)` → `dict` with `"success": bool`, `"error": str|None`.

## TESTS (write first) — mock `prompt_llm` and the git helpers
`test_workflow.py` (monkeypatch module-level names):
1. `_preflight` returns error → `2`; no `prompt_llm` call.
2. non-standard base without arg → `2`.
3. `needs_rebase` → False → `0`; no `prompt_llm` call.
4. `pr_info` present on base → `2`.
5. Session returns success marker + `_rebase_success_shape` True + `git_push`
   success → `0` (assert `git_push` called with `force_with_lease=True`).
6. Marker `aborted` (even with success shape) → `1`; `git_push` NOT called.
7. `_is_rebase_in_progress` True after session → `1` and `_abort_rebase` called
   (finally).
8. Success shape + `git_push` returns `{"success": False}` → `_reset_hard(pre_sha)`
   called and `2`.
9. `prompt_llm` raises `LLMTimeoutError` → `1`; finally aborts if mid-rebase.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement Step 6
> (TDD). First write `tests/workflows/rebase/test_workflow.py` driving every
> exit-code path with mocks (patch `prompt_llm`, `needs_rebase`, `fetch_remote`,
> `git_push`, and the Step 4/5 helpers as needed) per the nine cases in this step.
> Then add `run_rebase_workflow` (and an optional `_run_rebase_session` helper) to
> `src/mcp_coder/workflows/rebase.py` following the algorithm here — single
> `prompt_llm` call, worst-case-wins mapping, Python-owned force-push with restore
> on failure, and the `finally` abort safety net. Run pylint, pytest (`-n auto`,
> unit markers), mypy, bandit; fix everything. Exactly one commit.
