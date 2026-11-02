# Step 6 — Status table marks untrusted launch rows

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest set (`-n auto`).
> Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/issues.py` — new `find_untrusted_launch_keys`
- `src/mcp_coder/workflows/vscodeclaude/status.py` — `display_status_table`
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py` — `execute_coordinator_vscodeclaude_status`
- `tests/cli/commands/coordinator/conftest.py` — add an autouse patch returning `set()` (target: see below)
- `tests/workflows/vscodeclaude/test_status_untrusted.py` — **new**
- `tests/cli/commands/coordinator/test_vscodeclaude_trust.py` — add status-command tests

## WHAT

```python
# issues.py
def find_untrusted_launch_keys(
    eligible_issues: list[tuple[str, IssueData]],
    sessions: list[VSCodeClaudeSession],
    issues_without_branch: set[tuple[str, int]],
    repo_filter: str | None,
) -> set[tuple[str, int]]:
    """Return (repo_full_name, number) of launchable rows whose body is not trusted.

    Raises:
        GitHubRateLimitError: If a trust lookup hit a GitHub rate limit.
    """

# status.py — new last parameter
def display_status_table(..., issues_without_branch=None,
                         untrusted_keys: set[tuple[str, int]] | None = None) -> None
```

## HOW

- `issues.py` imports `IssueManager`, `BodyTrust` (shim) and `evaluate_body_trust` (`...workflow_utils.issue_trust`).
  It builds one `IssueManager` per repo, lazily, only when a row needs a lookup.
- Command: inside the existing `try`, after the `--explain` return and after
  `build_eligible_issues_with_branch_check`, call
  `untrusted_keys = find_untrusted_launch_keys(eligible_issues, sessions, issues_without_branch, args.repo)`.
  Pass `untrusted_keys=untrusted_keys` to `display_status_table`. The existing `except` already handles rate limits.
- Display: in the eligible-issue loop, in the `else: action = "-> Create and start"` branch only, append
  `" (untrusted body: review-only)"` when `(repo_name, issue["number"])` is in `untrusted_keys`.
  The display makes no GitHub calls.
- `untrusted` and `lookup_failed` share the marker.

## ALGORITHM

```
session_keys = {(s["repo"], s["issue_number"]) for s in sessions}
managers, keys = {}, set()
for repo, issue in eligible_issues:
    key = (repo, issue["number"])
    if key in session_keys or key in issues_without_branch: continue
    if repo_filter and repo.split("/")[-1] != repo_filter: continue
    if not is_status_eligible_for_session(get_issue_status(issue)): continue
    if repo not in managers: managers[repo] = IssueManager(repo_url=f"https://github.com/{repo}")
    if evaluate_body_trust(managers[repo], issue).status is not BodyTrust.TRUSTED: keys.add(key)
return keys
```

## DATA

`set[tuple[str, int]]`, keyed by `(repo_full_name, issue_number)` like `issues_without_branch`.

## conftest.py (coordinator)

The command imports `find_untrusted_launch_keys` **inside the function**, next to the existing local
`build_eligible_issues_with_branch_check` import. `commands_vscodeclaude` therefore has no module-level attribute of that name.
The autouse patch targets the defining module, as `test_active_set_invariant.py` does:
`mcp_coder.workflows.vscodeclaude.issues.find_untrusted_launch_keys`, returning `set()`, so existing status-command tests
make no lookups. New command tests in `test_vscodeclaude_trust.py` override the same target.

## Callers outside the coordinator tests

`tests/workflows/vscodeclaude/test_active_set_invariant.py` and `test_explain.py` also call
`execute_coordinator_vscodeclaude_status`. They need no change and no extra autouse patch:
- `test_active_set_invariant.py` stubs `build_eligible_issues_with_branch_check` to `([], set())`, so the finder loops over
  nothing and makes no lookup.
- `test_explain.py` uses `--explain`, which returns before the finder is called.

Do **not** add an autouse patch of the finder to `tests/workflows/vscodeclaude/conftest.py`: `test_status_untrusted.py`
tests the real finder there.

## Tests

`test_status_untrusted.py` (display + finder; patch `issues.evaluate_body_trust` and `issues.IssueManager`):
- Marker on a "Create and start" row in `untrusted_keys`; no marker on "Needs branch" or "(awaiting merge)" rows, even
  when the key is in the set; no marker on session rows.
- The finder: a `LOOKUP_FAILED` row is included; trusted is excluded; session rows, `issues_without_branch` rows,
  status-ineligible rows and other repos (by short name vs `repo_filter`) get **no lookup** (call count);
  one `IssueManager` per repo.

`test_vscodeclaude_trust.py` (command):
- `--explain` → `find_untrusted_launch_keys` is not called.
- A rate limit from `find_untrusted_launch_keys` → exit code 0, no table.
- The returned set is passed to `display_status_table` as `untrusted_keys`.
