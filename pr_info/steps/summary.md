# Summary — #1285: IssueData factory so upstream field additions touch one place

## Problem

About 190 test lines in 36 files build a full `IssueData` dict by hand, in three forms:
`IssueData(...)` calls, annotated dicts `x: IssueData = {...}`, and untyped dicts / `dict[str, Any]`.
When upstream (`mcp-workspace`) added the required key `author_association`, commit
`8bc0fba` had to touch every one of them. The next upstream field would cost the same.

## Design

```
mcp_workspace.github_operations.issues.create_empty_issue_data   (upstream, owns all keys)
        │  re-exported
        ▼
src/mcp_coder/mcp_workspace_github.py   (shim, adds it to __all__)
        │                                  │
        ▼                                  ▼
src/.../create_plan/prerequisites.py   tests/github_factories.py::make_issue_data(**overrides)
  (empty sentinel)                        │
                                          ▼
                                  all test sites + local helpers/fixtures
```

- **Single source of keys.** The upstream constructor `create_empty_issue_data()` is the
  base dict. When upstream adds a required key there, mcp-coder needs no change.
- **Shim only.** Tests and `src/` import it through `mcp_coder.mcp_workspace_github`,
  never from `mcp_workspace.*` directly.
- **Test factory** `make_issue_data(**overrides) -> IssueData` in `tests/github_factories.py`:
  - defaults `number=1`, `state="open"`;
  - `title` = `f"Issue {number}"`, `url` = `f"https://github.com/owner/repo/issues/{number}"`,
    built from the final `number` unless explicitly overridden;
  - runtime typo check: `TypeError` for keys not in `IssueData.__annotations__`
    (includes `NotRequired` keys like `base_branch`);
  - merge into `dict[str, Any]`, return `cast(IssueData, merged)` (`data.update()` fails strict mypy).
- **"Not found" sentinels** (`number=0`, empty strings) use `create_empty_issue_data()` directly.
- **Local helpers/fixtures** stay as thin wrappers: `return make_issue_data(<non-default values>)`.
  Deleted only if every value they set equals the factory default.
- **Migration rule:** drop only values equal to the factory result; keep every other
  explicit value as an override (e.g. `title="Test Issue"`, `url=""`).
- **Typing rule:** where a converted site is annotated `dict[str, Any]` / `dict[str, object]`
  (return type, variable, `list[...]`), retype to `IssueData` / `list[IssueData]`. No `cast`.
- `src/` must never import the factory (import-linter `no_test_imports_in_source`).

## Files

### Created
- `tests/github_factories.py` — `make_issue_data`
- `tests/test_github_factories.py` — 2 tests for the factory

### Modified — source
- `src/mcp_coder/mcp_workspace_github.py` — re-export `create_empty_issue_data`
- `src/mcp_coder/workflows/create_plan/prerequisites.py` — use `create_empty_issue_data()`

### Modified — tests
- `tests/test_mcp_workspace_github_smoke.py` — `__all__` count 31 → 32
- `tests/cli/commands/`: `test_define_labels_execute.py`, `test_define_labels_staleness.py`,
  `test_define_labels_status.py`, `test_define_labels_validate.py`, `test_set_status.py`,
  `test_set_status_from_status.py`
- `tests/cli/commands/coordinator/`: `test_commands.py`, `test_core.py`,
  `test_integration.py`, `test_issue_stats.py`
- `tests/workflows/create_plan/`: `test_failure_handling.py`, `test_guard_net.py`,
  `test_main.py`, `test_prerequisites.py`, `test_prompt_execution.py`,
  `test_success_label_gate.py`
- `tests/workflows/vscodeclaude/` (restart): `test_session_restart.py`,
  `test_session_restart_branch_integration.py`, `test_session_restart_cache.py`,
  `test_session_restart_closed_sessions.py`
- `tests/workflows/vscodeclaude/` (rest): `test_assessment_issue_facts.py`,
  `test_cache_aware.py`, `test_checks.py`, `test_checks_review_comments.py`,
  `test_closed_issues_integration.py`, `test_helpers.py`, `test_issues.py`,
  `test_launch_vscode_env_vars.py`, `test_session_launch.py`,
  `test_session_launch_process_issues.py`, `test_session_launch_regenerate.py`,
  `test_status_display.py`, `test_status_display_branch_indicators.py`,
  `test_status_display_scenario.py`
- misc: `tests/services/test_branch_info.py`, `tests/workflow_utils/test_base_branch.py`

## Steps (one commit each)

1. Shim: re-export `create_empty_issue_data`
2. Test factory `make_issue_data` + its tests
3. `prerequisites.py` uses `create_empty_issue_data()`
4. Migrate `tests/cli/commands` (6 files)
5. Migrate `tests/cli/commands/coordinator` (4 files)
6. Migrate `tests/workflows/create_plan` (6 files)
7. Migrate `tests/workflows/vscodeclaude/test_session_restart*` (4 files)
8. Migrate remaining `tests/workflows/vscodeclaude` (14 files)
9. Migrate misc (2 files) + acceptance checks

## Checks for every step

```
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_lint_imports_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
```

Migration steps run the full fast suite: untyped `Mock.return_value` sites are only caught by pytest.

## Shared migration rules (steps 4–9)

- Import: `from tests.github_factories import make_issue_data`.
- Replace each full issue literal (any of the three forms) with `make_issue_data(...)`.
- Drop an override only if it equals the factory result:
  `number=1`, `state="open"`, `body=""`, `labels=[]`, `assignees=[]`, `user=None`,
  `created_at=None`, `updated_at=None`, `locked=False`, `author_association=None`,
  `title=f"Issue {number}"`, `url=f"https://github.com/owner/repo/issues/{number}"`.
- Keep every other explicit value, even if the test doesn't assert on it.
- "Not found" sentinel (`number=0`, empty strings, `state=""`) → `create_empty_issue_data()`
  imported from `mcp_coder.mcp_workspace_github`.
- Helpers/fixtures returning an issue dict: body becomes `return make_issue_data(...)`;
  delete only if all values are defaults (then inline `make_issue_data()` at call sites).
- Retype `dict[str, Any]` / `dict[str, object]` / `list[...]` receivers of converted
  values to `IssueData` / `list[IssueData]`. No `cast`.
- Remove imports left unused (`IssueData`, `Any`, ...).
