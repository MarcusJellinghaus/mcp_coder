# Step 4: Add Missing Returns and Yields Sections

> **Context:** See [summary.md](summary.md) for overall plan. This is step 4 of 4 (Step 3 removed).

## Goal

Add `Returns` and `Yields` sections to docstrings of functions/methods that return or yield values but don't document them.

## Rules Addressed

| Rule | Count | Description |
|---|---|---|
| DOC201 | ~151 | Missing `Returns` section in docstring |
| DOC402 | ~24 | Missing `Yields` section in docstring |

**Total:** ~175 fixes

## WHERE

`src/` only (tests excluded from scope — see [decisions.md](decisions.md)):
- Functions with return values (~77 DOC201)
- Generators (~24 DOC402)

Identify exact files:
```bash
ruff check src --select DOC201,DOC402
```

## WHAT

No new functions. Add `Returns:` or `Yields:` sections to existing docstrings.

## HOW

Google-style Returns/Yields format:

```python
def get_config(path: str) -> dict[str, Any]:
    """Load configuration from path.

    Args:
        path: Path to config file.

    Returns:
        Configuration dictionary with parsed settings.
    """

def iter_lines(path: str) -> Iterator[str]:
    """Iterate over lines in file.

    Args:
        path: Path to file.

    Yields:
        Each line from the file, stripped of trailing newline.
    """
```

Guidelines:
- For simple return types, a one-line description suffices
- For complex returns (tuples, dicts), describe each element
- For `bool` returns, describe what True/False mean
- For `Optional` returns, mention when None is returned
- For test helpers, keep Returns brief

## ALGORITHM

```
1. Run ruff check to list all DOC201 and DOC402 violations
2. For each violation, read the function to understand what it returns/yields
3. Add a Returns: or Yields: section in Google-style format
4. Run ./tools/format_all.sh
5. Run ruff check, pylint, pytest, mypy to verify
6. Commit
```

## DATA

No data structures. Output: modified `.py` files with added Returns/Yields docstring sections.

## Verification

- `ruff check src --select DOC201,DOC402` — should report 0
- `pytest` — all pass
- `mypy` — no regressions

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for context.

Execute step 4: Add missing Returns and Yields sections.

1. Run `ruff check src --select DOC201,DOC402` to get the full violation list
2. For each function/method:
   - Read the implementation to understand the return/yield value
   - Add a `Returns:` or `Yields:` section in Google-style format
   - Keep descriptions concise but accurate
   - For bool returns, describe what True/False mean
   - For Optional returns, mention when None is returned
3. Run ./tools/format_all.sh
4. Verify with ruff check, pylint, pytest, mypy — all must pass
5. Commit the changes

Note: ~101 fixes in `src/` only. Work through files systematically by directory.
```
