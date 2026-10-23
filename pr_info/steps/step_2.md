# Step 2 — Test factory `make_issue_data`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Write `tests/test_github_factories.py` first, then `tests/github_factories.py`.
> Run the checks listed in the summary; all must pass. Produce one commit.

## WHERE
- New `tests/github_factories.py`
- New `tests/test_github_factories.py`

## WHAT

```python
def make_issue_data(**overrides: Any) -> IssueData:
    """Build a full IssueData for tests; overrides replace defaults."""
```

Imports: `from typing import Any, cast`;
`from mcp_coder.mcp_workspace_github import IssueData, create_empty_issue_data`.
Module docstring states its purpose: one place that builds issue dicts, so upstream
field additions need no test changes.

## ALGORITHM

```
unknown = overrides.keys() - IssueData.__annotations__.keys()
if unknown: raise TypeError(f"Unknown IssueData keys: {sorted(unknown)}")
merged: dict[str, Any] = {**create_empty_issue_data(), "number": 1, "state": "open", **overrides}
if "title" not in overrides: merged["title"] = f"Issue {merged['number']}"
if "url" not in overrides: merged["url"] = f"https://github.com/owner/repo/issues/{merged['number']}"
return cast(IssueData, merged)
```

Do not use `setdefault` (base dict already has `title`/`url` keys) or `data.update()`
(fails strict mypy, `typeddict-item`).

## Tests (`tests/test_github_factories.py`, 2 tests)

1. `test_unknown_key_raises_type_error`:
   - `pytest.raises(TypeError)` on `make_issue_data(lable=["x"])`.
   - `make_issue_data(base_branch="main")["base_branch"] == "main"` (NotRequired key accepted).
2. `test_title_and_url_follow_number_unless_overridden`:
   - `make_issue_data(number=7)` → `title == "Issue 7"`,
     `url == "https://github.com/owner/repo/issues/7"`, `state == "open"`.
   - `make_issue_data(number=7, title="T", url="")` → `title == "T"`, `url == ""`.

## DATA
Returns `IssueData` containing every key from `create_empty_issue_data()` plus any overrides.
