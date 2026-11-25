# Step 3 — `pr_health` behaviour: selection, repo URL, cache write-back

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`). Implement step 3 only,
> test-first: change `check_pr_health` in `src/mcp_coder/workflows/pr_health/checks.py` to select
> open `status-10:pr-created` issues without an assignee filter, derive the repo URL with
> `RepoIdentifier.from_repo_url`, and write each successful escalation back to the issue cache.
> `vscodeclaude launch` still calls `check_pr_health` in this step (moved in step 4). Run all checks
> from the summary; produce exactly one commit.

## WHERE

- `src/mcp_coder/workflows/pr_health/checks.py`
- Tests: `tests/workflows/pr_health/conftest.py` (new), `test_checks_selection.py` (new),
  `test_checks_warm_cache.py` (new, moved), `test_checks.py`, `test_checks_pr_cache.py`,
  `test_checks_rate_limit.py`, `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py`

## WHAT

```python
PR_CREATED_LABEL = "status-10:pr-created"

def _escalate(issue, issue_manager, to_label_id, to_label_name, repo_name) -> None:  # signature unchanged
def check_pr_health(repo_name: str, repo_config: dict[str, str], all_cached_issues: list[IssueData]) -> None:  # unchanged
```

New imports in `checks.py` from `...mcp_workspace_github`: `RepoIdentifier`, `update_issue_labels_in_cache`.
Removed imports: `..vscodeclaude.config` (`get_github_username`, `get_repo_full_name`),
`..vscodeclaude.issues` (`_filter_eligible_vscodeclaude_issues`), `get_issue_status` from
`issue_helpers` (`lookup_branch`, `is_marked` stay). After this step `pr_health` imports nothing from
`vscodeclaude`.

## ALGORITHM

`check_pr_health` setup block (inside the existing `try`; `except` unchanged — warn + skip repo):
```
labels_config = load_labels_config(get_labels_config_path(None))
ignore = set(labels_config.get("ignore_labels", []))
pr_issues = [i for i in all_cached_issues
             if i["state"] == "open" and PR_CREATED_LABEL in i["labels"] and not ignore & set(i["labels"])]
if not pr_issues: return                      # still before any manager is built
repo_url = RepoIdentifier.from_repo_url(repo_config["repo_url"]).https_url
managers / caches built from repo_url (as today); label_names = build_label_lookups(labels_config)["id_to_name"]
```

`_escalate`:
```
if update_workflow_label(issue_manager, "pr_created", to_label_id, validated_issue_number=n):
    update_issue_labels_in_cache(issue_manager.repo_identifier, issue_number=n,
                                 old_label=PR_CREATED_LABEL, new_label=to_label_name)
    logger.log(OUTPUT, "PR-health: %s #%d → %s", ...)   # unchanged
```
No `try` around the cache call: `update_issue_labels_in_cache` catches and logs every exception itself.

Update the `check_pr_health` docstring: selection = open, `status-10:pr-created` label, no
`ignore_labels`, regardless of assignee and other `status-*` labels; successful escalations are
written back to the issue cache.

## DATA

No new return values. Cache write-back mirrors dispatch: only `status-10` → target is changed in the
cache; other workflow labels stay there until the next incremental refresh (accepted by the issue).

## HOW — tests first

1. `tests/workflows/pr_health/conftest.py`: autouse fixture `_no_cache_write` patching
   `mcp_coder.workflows.pr_health.checks.update_issue_labels_in_cache` with a `MagicMock` and
   yielding it, so escalating tests never touch the real `coordinator_cache` directory.
2. `test_checks.py` `_patch_env`: remove the `get_github_username` and
   `_filter_eligible_vscodeclaude_issues` patches (they stop being attributes of `checks`).
3. Setup-failure tests need a new trigger — a bad `repo_url` makes `RepoIdentifier.from_repo_url`
   raise `ValueError` inside the setup `try`:
   - `test_checks.py::TestCheckPrHealth::test_setup_failure_logs_warning_and_does_not_raise`:
     `check_pr_health("test-repo", {"repo_url": "not-a-url"}, [_make_pr_issue(987)])`; assert the WARNING
     naming `test-repo`.
   - `test_checks_pr_cache.py::test_setup_failure_does_not_save`: same trigger; assert neither cache saves.
4. `test_checks_rate_limit.py`: delete `test_username_limit_propagates` and the now unused
   `_wrapped_rate_limit` helper.
5. New `test_checks_selection.py` (the only place selection is tested), using `_setup` /
   `_make_pr_issue` from `tests.workflows.pr_health.test_checks`; "checked" = `branch_cache.lookup`
   called for that issue:
   - unassigned `status-10` issue (`assignees=[]`) is checked;
   - `status-10` plus another `status-*` label (e.g. `status-08:ready-pr`) is checked;
   - closed `status-10` issue (`state="closed"`) is not checked;
   - `status-10` issue with an ignore label (`"blocked"`, bundled `labels.json`) is not checked.
6. Cache write-back tests, added to `test_checks_pr_cache.py` (request the `_no_cache_write` fixture):
   - dirty PR → called once with `(issue_manager.repo_identifier, issue_number=999,
     old_label="status-10:pr-created", new_label="status-71:merge-conflict")`;
   - `issue_manager.transition_issue_label.return_value = False` → not called.
7. Move `TestPrHealthWarmCacheCallCount` and its module helpers/constants (`_STORE`, `_EVENTS`,
   `_FETCH_ALERTS`, `_ISSUE_UPDATED_AT`, `_gh_pr`, `_gh_run`, `_feedback`) from
   `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py` to
   `tests/workflows/pr_health/test_checks_warm_cache.py`; drop its `get_github_username` patch, use
   `CHECKS = "mcp_coder.workflows.pr_health.checks"`. Remove the moved part (and imports it alone used)
   from `test_vscodeclaude_pr_health.py`; `TestPrHealthOutsideCapacityGate` stays until step 4.
8. Then change `checks.py` as in ALGORITHM; run all checks.

## Verify

- `mcp__mcp-workspace__search_files` in `src/mcp_coder/workflows/pr_health/` for `vscodeclaude` → no match.
- `tests/workflows/pr_health/test_checks.py` stays under the 750-line limit (`check_file_size`).
