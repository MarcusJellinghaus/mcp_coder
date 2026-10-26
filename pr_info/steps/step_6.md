# Step 6 — `review/handoff` scoped commit and unstage

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement step 6 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(review): commit round log via commit_paths`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `commit_paths` (from `.commits`) and `unstage_paths` (from `.staging`)
- `src/mcp_coder/workflows/review/handoff.py` — `_flush_round_log`, `_unstage_path`; delete `_relative_to_project`, `_unrelated_staged_entries`, `_commit_only_path`
- `tests/workflows/review/test_handoff.py` (~211–438), `tests/workflows/review/test_handoff_route.py` (~424)
- `tests/workflows/review/conftest.py` (~130–144) — replace the `monkeypatch.setattr(handoff, "get_full_status" / "commit_staged_files", ...)` mocks (they raise `AttributeError` once the imports go) with `commit_paths` / `unstage_paths` mocks (`mocks.commit_paths` returns a full `CommitResult` with `commit_hash="LOGSHA"`; `mocks.unstage_paths` returns a successful `GitResult`)
- `tests/workflows/review/test_core.py` (~113, ~184, ~298) and `tests/workflows/review/test_core_after_steps.py` (~256, ~646) — `env.commit_staged_files` assertions become `env.commit_paths` (and, where a failed flush is asserted, `env.unstage_paths`) assertions

## WHAT

`_flush_round_log` (`only` branch) always uses `commit_paths`; no `commit_staged_files` fork:

```python
if only is not None:
    if not stage_specific_files([only], project_dir):   # keep: first flush, log is untracked
        logger.warning("Could not stage the round log %s - not committing", only)
        return
    result = commit_paths(message, [only], project_dir)
else:
    result = commit_all_changes(message, project_dir)
if result["error_category"] == "nothing_to_commit":
    logger.debug("Round-log commit had nothing to commit")
    return
if not result["success"]:
    logger.warning(...)            # unchanged text
    if only is not None:
        _unstage_path(only, project_dir)
    return
if result["commit_hash"] is None:  # commit_all_changes "no changes" path
    logger.debug("Round-log commit had nothing to commit")
    return
... push tail unchanged
```

`_unstage_path(only: Path, project_dir: Path) -> None`:

```python
result = unstage_paths([only], project_dir)
if not result["success"]:
    logger.warning(
        "Could not unstage the round log %s after the failed commit: %s",
        only, (result["stderr"] or "").strip() or result["error"],
    )
```

Upstream validates "path outside project_dir" itself (`validation_failed` / `success=False`),
so `_relative_to_project` goes. Remove now-unused imports (`commit_staged_files`,
`get_full_status`, `execute_command`, and `get_latest_commit_sha` / `SHORT_SHA_LENGTH` /
`CommitResult` if no other use remains). Update the `_flush_round_log` and `_unstage_path`
docstrings: no pathspec escape hatch, no two routes.

## Tests (write first)

Patch `mcp_coder.workflows.review.handoff.{stage_specific_files, commit_paths, unstage_paths, commit_all_changes, push_changes}`.
`CommitResult` mock dicts must carry all keys incl. `returncode`, `stderr`, `error_category`.

- `only=` success → `stage_specific_files([only], dir)` then `commit_paths(message, [only], dir)`; push iff `push=True`.
- `only=` + `nothing_to_commit` → debug log, no warning, no unstage, no push.
- `only=` + `commit_failed` → warning, `unstage_paths([only], dir)` called, no push.
- `unstage_paths` returns `success=False` → warning names the round log.
- staging fails → no commit call.
- Delete tests of `_unrelated_staged_entries` / `_commit_only_path` / the `commit_staged_files` route; fix `test_handoff_route.py` if it patches any removed name.

## DATA

- `CommitResult` keys read: `success`, `commit_hash`, `error`, `error_category`. `GitResult` keys read: `success`, `error`, `stderr`.
