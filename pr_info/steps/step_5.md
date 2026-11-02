# Step 5 — Launch, restart and intervention wiring

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`.
> Write the tests first, then the code, and update the existing tests that break. Run pylint, mypy and the fast pytest
> set (`-n auto`). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — `prepare_and_launch_session`,
  `process_eligible_issues`, `regenerate_session_files`
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py` — `_handle_intervention_mode` and its call site
- `tests/workflows/vscodeclaude/conftest.py` — autouse trusted fixture
- `tests/workflows/vscodeclaude/test_session_launch_trust.py` — **new**
- `tests/cli/commands/coordinator/test_vscodeclaude_trust.py` — **new** (intervention part)
- existing callers in tests: `test_session_launch.py`, `test_session_launch_prepare.py`,
  `test_launch_vscode_env_vars.py`, `test_rate_limit_reraise.py` (calls near lines 211 and 304) — add
  `issue_manager=MagicMock()`
- existing assertions on `prepare_and_launch_session` kwargs: `test_session_launch_process_issues.py`,
  `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` (around lines 460 and 478), plus any others in
  `tests/cli/commands/coordinator/`

## WHAT

```python
def prepare_and_launch_session(
    issue: IssueData,
    repo_config: dict[str, str],
    vscodeclaude_config: VSCodeClaudeConfig,
    repo_vscodeclaude_config: RepoVSCodeClaudeConfig,
    branch_name: str | None,
    issue_manager: IssueManager,          # new, required, no default
    is_intervention: bool = False,
    skip_github_install: bool = False,
) -> VSCodeClaudeSession

def regenerate_session_files(session, issue) -> Path   # signature unchanged
```

## HOW

- `from ...workflow_utils.issue_trust import evaluate_body_trust`; `BodyTrust` via `...mcp_workspace_github`.
- `prepare_and_launch_session`: compute trust **before** `create_working_folder(folder_path)`.
  Pass `issue_title=display_title` to `create_workspace_file`, `create_startup_script` and `create_status_file`,
  and `untrusted_body=untrusted` to the latter two. Log untrusted launches at INFO
  (`"Issue #%d: untrusted body (%s) — review-only session"`).
- `process_eligible_issues`: pass its existing `issue_manager`.
- `_handle_intervention_mode`: pass its existing `issue_manager`.
- Intervention rate limit: at the call site in `execute_coordinator_vscodeclaude`, wrap
  `return _handle_intervention_mode(...)` in
  `try ... except Exception as exc: log_rate_limit_stop(_rate_limit_or_raise(exc)); return 0`.
  Non-rate-limit errors are re-raised by `_rate_limit_or_raise` and reach the existing outer handlers unchanged.
- `regenerate_session_files`: **first statement**
  `issue_manager = IssueManager(repo_url=f"https://github.com/{session['repo']}")`, then trust, then
  everything else, so a rate limit happens before any file is written. Same `display_title` / `untrusted_body` passing.
  Nothing is persisted in `VSCodeClaudeSession`; every restart recomputes trust.

## ALGORITHM (shared by both functions)

```
result = evaluate_body_trust(issue_manager, issue)        # may raise GitHubRateLimitError
untrusted = result.status is not BodyTrust.TRUSTED
display_title = "" if untrusted else issue["title"]
...existing steps, passing display_title / untrusted_body...
```

## DATA

No new data structures. The session store is unchanged.

## conftest.py (vscodeclaude)

An autouse fixture patches `mcp_coder.workflows.vscodeclaude.session_launch.evaluate_body_trust` to return a
TRUSTED `BodyTrustResult`, and `session_launch.IssueManager` with a `MagicMock`, so that existing
`regenerate_session_files` tests make no real GitHub construction. Tests that patch these themselves override it.

## Tests

`test_session_launch_trust.py`:
- Untrusted → `create_workspace_file`, `create_startup_script` and `create_status_file` receive `issue_title=""`, and the
  latter two receive `untrusted_body=True`. Trusted → real title, `untrusted_body=False`. `LOOKUP_FAILED` → treated as untrusted.
- A plain `MagicMock()` trust result → treated as untrusted (identity comparison).
- Rate limit from the helper in `prepare_and_launch_session` → `create_working_folder` is not called, no folder on disk
  (`tmp_path`), `GitHubRateLimitError` propagates.
- Rate limit in `regenerate_session_files` → no writer is called (`create_startup_script` etc. not called).
- Restart re-evaluation: two `regenerate_session_files` calls on the same session, untrusted then trusted → the second
  passes the real title and `untrusted_body=False`.
- `process_eligible_issues` passes its `issue_manager` to `prepare_and_launch_session`.

`test_vscodeclaude_trust.py` (coordinator dir):
- Intervention with `prepare_and_launch_session` raising `GitHubRateLimitError` → exit code 0, the stop message is logged, no traceback.
- The same with a raw rate-limit `GithubException` → exit code 0.
- Intervention passes `issue_manager` and `is_intervention=True`.
