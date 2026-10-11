# Step 1: Closing-reference helper

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`. Write the tests first, then the implementation. Run pylint, mypy and the fast pytest suite (`-n auto`, integration markers excluded) and make sure all pass. Then run the formatter and produce one commit.

## WHERE

- `src/mcp_coder/workflows/create_pr/helpers.py`: add a module-level regex and a function.
- `src/mcp_coder/workflows/create_pr/core.py`: re-export it next to `parse_pr_summary`:
  `from mcp_coder.workflows.create_pr.helpers import ensure_closing_reference as ensure_closing_reference`
- `tests/workflows/create_pr/test_parsing.py`: add a `TestEnsureClosingReference` class, importing from `mcp_coder.workflows.create_pr.core`.

## WHAT

```python
_CLOSING_REF_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*#(\d+)\b", re.IGNORECASE
)

def ensure_closing_reference(body: str, issue_number: int) -> str:
    """Return body guaranteed to contain a closing keyword for issue_number."""
```

## ALGORITHM

```
numbers = {int(n) for n in _CLOSING_REF_RE.findall(body)}
if issue_number in numbers: return body
others = sorted(numbers - {issue_number})
if others: logger.warning("PR body already closes other issue(s) %s; also adding Closes #%s", ...)
return f"{body}\n\nCloses #{issue_number}"
```

## DATA

The function returns a `str`: either `body` unchanged, or `body + "\n\nCloses #<issue_number>"`. It has no other side effects besides the warning log.

## Tests (write first)

Parametrized `test_detects_existing_reference(body)`, with issue 123, expecting the body to be returned unchanged:
- `"Closes #123"`, `"fixes #123"`, `"RESOLVED #123"`, `"close #123"`, `"Fix #123"`, `"resolve #123"`, `"text\n\nCloses  #123."`

Parametrized `test_appends_when_missing(body)`, with issue 123, expecting `result == body + "\n\nCloses #123"`:
- `"No reference"` (the LLM omits it)
- `"Closes #1234"` (word boundary on the number)
- `"prefixes #123"` (word boundary on the keyword)
- `"See #123"` (not a closing keyword)

`test_other_issue_appends_and_warns(caplog)`:
- Body `"Closes #7\nFixes #9\nCloses #7"`, issue 123.
- The result ends with `"\n\nCloses #123"`.
- There is exactly one WARNING record, and it contains both `7` and `9`.
