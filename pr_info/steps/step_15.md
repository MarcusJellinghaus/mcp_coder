# Step 15 — Call the refresh from create-pr phase B and `fix-ci`

## Precondition (check first)
`refresh_pr_description` must exist in `src/mcp_coder/workflow_steps/pr_description.py` (step 14).
If it does not, write one line to `pr_info/.blocked.txt`
(`Blocked: refresh_pr_description missing - step 14 not done (MarcusJellinghaus/mcp-workspace#349)`) and stop.

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_15.md` exactly, starting with its precondition.
> Write the tests first, then the code.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass. Format the code and make exactly one commit.

## WHERE
- `src/mcp_coder/workflows/create_pr/post_creation.py` — `run_post_creation`
- `src/mcp_coder/workflows/create_pr/core.py` — phase B call site
- `src/mcp_coder/workflows/fix_ci/core.py` — `run_fix_ci_workflow.body`
- `tests/workflows/create_pr/test_post_creation.py`, `tests/workflows/fix_ci/test_core.py`
- `docs/processes-prompts/development-process.md` §6, `docs/cli-reference.md` (one line each on the refresh)

## WHAT
```python
def run_post_creation(
    project_dir: Path,
    branch: str,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
) -> str
```
Phase B in `core.py` passes `provider, mcp_config, settings_file`.

## ALGORITHM
create-pr (`run_post_creation`):
```
head_before = get_latest_commit_sha(pd)            # first line of the function
... mergeability + CI wait unchanged; compute label but do not return yet (also for pr_merge_conflict) ...
if get_latest_commit_sha(pd) != head_before: refresh_pr_description(pd, branch, provider, mcp_config, settings_file)
return label
```
fix-ci (`body`):
```
head_before = get_latest_commit_sha(project_dir)
try: ci_ok = check_and_fix_ci(...)
finally: if get_latest_commit_sha(project_dir) != head_before: refresh_pr_description(project_dir, branch, provider, mcp_config, settings_file)
```
`finally` covers green, exhausted and the LLM-failure `except` path alike.

## HOW
- `refresh_pr_description` never raises, so it cannot change any label or exit code.
- Use a single exit point in `run_post_creation` so the refresh runs on every outcome.

## Tests (write first)
- create-pr: HEAD unchanged → refresh not called; `dirty` rebase changed HEAD → refresh called (also when the final label
  is `pr_merge_conflict`); label unchanged by refresh result.
- fix-ci: HEAD changed + CI green → refresh called, label `pr_created`; HEAD changed + exhausted → refresh called,
  `_fail` path unchanged; HEAD changed + `LLMTimeoutError` → refresh called, `_fail` path unchanged;
  HEAD unchanged → refresh not called.
- Patch `get_latest_commit_sha` with `side_effect=[before, after]`.

## DATA
`run_post_creation` still returns the label ID `str`.
