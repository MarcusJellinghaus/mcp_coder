# Step 3 — Call `check_pr_health` from the Step 4 loop, outside the capacity gate

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> Step 2 is done: `check_pr_health` exists and `process_eligible_issues` still calls it.
> Work test-first: add `test_vscodeclaude_pr_health.py` so it fails, then move the call.
> Run pylint, pytest (fast unit tests, `-n auto`), mypy, lint-imports and tach; all must pass.
> Format, then make exactly one commit.

## WHERE

Source:
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`

Tests:
- `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py` (create)
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` (autouse fixture)
- `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`, `test_session_launch.py`,
  `test_session_restart_branch_integration.py` (remove `session_launch.CIResultsManager` patches)

## WHAT / HOW

- `commands_vscodeclaude.py`: add `check_pr_health` to the existing
  `from ....workflows.vscodeclaude import (...)`; in the Step 4 loop, right after
  `all_cached_issues = list(...)` and before `process_eligible_issues(...)`:
  `check_pr_health(repo_name, validated_config, all_cached_issues)`. No capacity condition.
- `session_launch.py` / `process_eligible_issues()`:
  - delete the `checks.check_pr_health(...)` call added in step 2
  - remove the imports `CIResultsManager`, `build_label_lookups`, `get_labels_config_path`,
    `load_labels_config` (the whole `...config.label_config` import) and `from . import checks`
  - keep the capacity early return, `issue_manager`, `branch_manager`
  - docstring: no mention of PR-health checks

## ALGORITHM

None beyond the single call in the Step 4 loop.

## DATA

`check_pr_health(repo_name, validated_config, all_cached_issues) -> None`, once per repo that
passes the loop's `--repo` filter, `repo_url` check and failed-cache skip.

## Tests (write first)

`test_vscodeclaude_pr_health.py` (new, same `@patch` style as `TestAtCapacityDiagnosticLog`):
- two repos (`repo_a`, `repo_b`), `max_sessions=1`, `build_assessments` → one active stub
  (`SimpleNamespace(verdict=SimpleNamespace(active=True))`), cache populated for both repos,
  `process_eligible_issues` → `[]`
- assert `check_pr_health` called twice, with `repo_name` `repo_a` and `repo_b`, each with that
  repo's `{"repo_url": ...}` and cached-issue list
- `--repo repo_b` → called once, for `repo_b` only

`test_vscodeclaude_cli.py`:
```python
@pytest.fixture(autouse=True)
def _no_pr_health(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock()
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.check_pr_health", mock
    )
    return mock
```

Remove:
- every `monkeypatch.setattr("mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager", ...)`
  (and its now-unused `mock_ci_manager`) in `test_session_launch.py`, `test_session_restart_branch_integration.py`,
  `test_session_launch_process_issues.py` — the attribute no longer exists, so `monkeypatch` would raise

## Commit

`fix(vscodeclaude): run PR-health checks independently of the session limit (#1238)`
