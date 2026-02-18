# Step 2: Pass Pre-Fetched Issues from Caller in `execute_coordinator_vscodeclaude`

## Context
See [summary.md](summary.md) for the full problem description.
Step 1 must be complete before this step (the `all_cached_issues` parameter must exist).

This step wires the caller side: derives the per-repo issue list from the already-fetched
`cached_issues_by_repo` dict and passes it to `process_eligible_issues`.

---

## WHERE

| File | Role |
|---|---|
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Modify the per-repo loop in `execute_coordinator_vscodeclaude` |

No test file change needed — the unit test in Step 1 covers `process_eligible_issues` directly.
The integration behaviour is implicitly covered: if `all_cached_issues` is passed correctly,
Step 1's test already proves `get_all_cached_issues` is not called a second time.

---

## WHAT

Inside `execute_coordinator_vscodeclaude`, in the per-repo loop (Step 4), replace:

```python
# BEFORE
started = process_eligible_issues(
    repo_name=repo_name,
    repo_config=validated_config,
    vscodeclaude_config=vscodeclaude_config,
    max_sessions=max_sessions,
    repo_filter=args.repo,
)
```

with:

```python
# AFTER
repo_full_name = _get_repo_full_name_from_url(repo_config.get("repo_url", ""))
all_cached_issues = list(cached_issues_by_repo.get(repo_full_name, {}).values())

started = process_eligible_issues(
    repo_name=repo_name,
    repo_config=validated_config,
    vscodeclaude_config=vscodeclaude_config,
    max_sessions=max_sessions,
    repo_filter=args.repo,
    all_cached_issues=all_cached_issues,
)
```

---

## HOW

- `_get_repo_full_name_from_url` already exists in `commands.py` — reuse it, no new helper needed.
- `cached_issues_by_repo` is already in scope (built earlier in the same function by
  `_build_cached_issues_by_repo`).
- `repo_config` at this point in the loop is the raw dict from `load_repo_config`, so
  `repo_config.get("repo_url", "")` is the correct accessor (matches the existing pattern in
  `_build_cached_issues_by_repo`).
- If `repo_full_name` is empty or not in the dict, `.get(..., {}).values()` safely returns an
  empty list → `process_eligible_issues` falls back to fetching independently (backward-safe).

---

## ALGORITHM

```
# Per-repo loop in execute_coordinator_vscodeclaude (new lines only)
repo_url        = repo_config.get("repo_url", "")
repo_full_name  = _get_repo_full_name_from_url(repo_url)   # already exists
all_cached_issues = list(cached_issues_by_repo.get(repo_full_name, {}).values())

process_eligible_issues(..., all_cached_issues=all_cached_issues)
# get_all_cached_issues is now skipped inside process_eligible_issues
```

---

## DATA

`cached_issues_by_repo` type: `dict[str, dict[int, IssueData]]`
- outer key: `repo_full_name` (`"owner/repo"`)
- inner key: issue number (`int`)
- inner value: `IssueData`

`all_cached_issues` derived: `list[IssueData]` — `.values()` of the inner dict, converted to list.

Empty-list fallback: if `repo_full_name` is not a key in `cached_issues_by_repo` (e.g. URL parse
failed earlier), `process_eligible_issues` receives `[]` — that is a valid non-None list so
`get_all_cached_issues` is still skipped. This is acceptable: if the cache build failed for this
repo, there is no fresh data to use anyway.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Step 1 (all_cached_issues parameter on process_eligible_issues) is already implemented.

Your task is to implement Step 2 of issue #468.

File to change:
  src/mcp_coder/cli/commands/coordinator/commands.py

Instructions:
  1. Read the file in full before making any changes.
  2. Locate the per-repo loop in execute_coordinator_vscodeclaude (labelled "Step 4").
  3. Immediately before the process_eligible_issues call, add two lines:
       repo_full_name = _get_repo_full_name_from_url(repo_config.get("repo_url", ""))
       all_cached_issues = list(cached_issues_by_repo.get(repo_full_name, {}).values())
  4. Add all_cached_issues=all_cached_issues as a keyword argument to process_eligible_issues.
  5. Do not change anything else in the file.
  6. Run the full test suite and confirm no tests are broken.
```
