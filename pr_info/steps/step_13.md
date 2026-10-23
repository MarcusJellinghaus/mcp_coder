# Step 13 — Move PR text helpers to `workflow_steps/pr_description.py`

## Precondition (check first)
Call `mcp__mcp-tools-py__get_library_source("mcp_workspace.github_operations.pr_manager.PullRequestManager.update_pull_request")`.
If it is not found, write one line to `pr_info/.blocked.txt`
(`Blocked: PullRequestManager.update_pull_request missing (MarcusJellinghaus/mcp-workspace#349)`) and stop.

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_13.md` exactly, starting with its precondition.
> Use `mcp__mcp-tools-py__move_symbol` for the move. Write the new helper's tests first.
> Run pylint, pytest (fast unit set, `-n auto`), mypy and lint-imports; all must pass. Format the code and make exactly one commit.

## WHERE
- From `src/mcp_coder/workflows/create_pr/helpers.py`: `_CLOSING_REF_RE`, `ensure_closing_reference`, `parse_pr_summary`
- To new `src/mcp_coder/workflow_steps/pr_description.py`
- New `tests/workflow_steps/test_pr_description.py`

## WHAT
```python
_CLOSING_REF_RE = re.compile(...)                                  # unchanged
def ensure_closing_reference(body: str, issue_number: int) -> str  # unchanged
def parse_pr_summary(llm_response: str) -> tuple[str, str]          # unchanged
def closing_issue_numbers(body: str) -> list[int]:
    """Sorted, de-duplicated issue numbers the body closes (Closes/Fixes/Resolves #N)."""
```

## ALGORITHM
```
return sorted({int(n) for n in _CLOSING_REF_RE.findall(body or "")})
```
`ensure_closing_reference` uses `closing_issue_numbers` internally instead of its own `findall`.

## HOW
- `workflows/create_pr/helpers.py` re-exports the moved names
  (`from mcp_coder.workflow_steps.pr_description import ensure_closing_reference as ensure_closing_reference`, ...).
- `workflows/create_pr/core.py` keeps its existing re-exports of `ensure_closing_reference` and `parse_pr_summary`
  (tests import them from there: `test_parsing.py:7`, `test_create_pr_integration.py:337`).
- Existing tests in `tests/workflows/create_pr/test_parsing.py` must pass unchanged.

## Tests (write first)
`closing_issue_numbers`: `"Closes #3\nfixes #1, resolves: #3"` → `[1, 3]`; no reference → `[]`; `""` → `[]`;
`"#5"` without a keyword → `[]`.

## DATA
`list[int]`.
