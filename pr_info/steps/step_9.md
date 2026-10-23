# Step 9 — Migrate misc (2 files) + acceptance checks

## LLM prompt

> Read `pr_info/steps/summary.md` (especially "Shared migration rules"), then implement
> `pr_info/steps/step_9.md` exactly. Run the checks listed in the summary, including the
> full fast pytest suite, plus the acceptance checks below; all must pass. Produce one commit.

## WHERE
- `tests/services/test_branch_info.py`
- `tests/workflow_utils/test_base_branch.py`

## WHAT
- `test_branch_info.py::_issue(labels, title="Some title", number=42)`:
  return type `dict[str, Any]` → `IssueData` (add `from mcp_coder.mcp_workspace_github import IssueData`); body becomes
  ```python
  return make_issue_data(
      number=number, labels=labels, title=title, user="u",
      created_at="2026-04-30T08:00:00Z", updated_at="2026-04-30T09:00:00Z",
  )
  ```
  (`state`, `body`, `assignees`, `url`, `locked`, `author_association` equal factory defaults.)
  Retype any receivers mypy flags; drop `Any` import if unused.
- `test_base_branch.py`: literal (~line 154) → `make_issue_data(...)` per the shared rules.

## Acceptance checks (whole repo)
1. `mcp__mcp-workspace__search_files(pattern='"locked":|\\blocked=', glob="tests/**/*.py")`
   matches only `tests/github_factories.py` (or nothing — the factory has no literal).
   Convert any remaining site.
2. `mcp__mcp-workspace__search_files(pattern="IssueData\\(|IssueData = \\{", glob="src/**/*.py")`
   returns no matches.
3. pylint, mypy, lint-imports and the fast pytest suite pass.

## DATA
Same values per site as before.
