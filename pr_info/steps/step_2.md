# Step 2: Small Manual Fixes

> **Context:** See [summary.md](summary.md) for overall plan. This is step 2 of 4 (Step 3 removed).

## Goal

Fix all small, non-D102 manual docstring violations in one pass: missing module/class/function docstrings, accuracy errors, and capitalization/punctuation.

## Rules Addressed

| Rule | Count | Description |
|---|---|---|
| D100 | ~2 | Missing module docstring |
| D101 | ~7 | Missing class docstring |
| D103 | ~3 | Missing function docstring |
| D403 | ~10 | First word not capitalized |
| D415 | ~5 | Missing terminal punctuation (period) |
| D417 | ~2 | Undocumented parameter in docstring |
| DOC102 | ~1 | Extraneous parameter in docstring |
| DOC202 | ~5 | Extraneous `Returns` in docstring |

**Total:** ~35 manual fixes

## WHERE

Scattered across `src/` and `tests/`. Identify exact files by running:
```bash
ruff check src tests --select D100,D101,D103,D403,D415,D417,DOC102,DOC202
```

## WHAT

No new functions. Changes are:
- **D100**: Add module-level docstring (one-line summary of the module's purpose)
- **D101**: Add class-level docstring (one-line summary of the class)
- **D103**: Add function-level docstring (one-line summary)
- **D403**: Capitalize the first word of the docstring summary
- **D415**: Add period at end of summary line
- **D417**: Add missing parameter to Args section
- **DOC102**: Remove parameter from Args that doesn't exist in signature
- **DOC202**: Remove `Returns` section from functions that return None

## HOW

For each violation, edit the file to fix the docstring. Use Google-style format:

```python
# Module docstring (D100)
"""Module for handling X operations."""

# Class docstring (D101)
class MyClass:
    """Manages X resources."""

# Function docstring (D103)
def my_func():
    """Perform X operation."""
```

## ALGORITHM

```
1. Run ruff check to list all D100,D101,D103,D403,D415,D417,DOC102,DOC202 violations
2. For each violation, open the file and fix the docstring
3. Run ./tools/format_all.sh
4. Run ruff check, pylint, pytest, mypy to verify
5. Commit
```

## DATA

No data structures. Output: modified `.py` files with added/corrected docstrings.

## Verification

- `ruff check src tests` — D100, D101, D103, D403, D415, D417, DOC102, DOC202 counts should be 0
- `pylint` — C0114, C0115 counts should drop significantly
- `pytest` — all pass
- `mypy` — no regressions

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

Execute step 2: Fix small manual docstring violations.

1. Run `ruff check src tests --select D100,D101,D103,D403,D415,D417,DOC102,DOC202` to get the full list
2. For each violation, fix the docstring:
   - D100: Add module docstring (one-line summary of purpose)
   - D101: Add class docstring (one-line summary)
   - D103: Add function docstring (one-line summary)
   - D403: Capitalize first word
   - D415: Add period at end of summary
   - D417: Add missing param to Args section
   - DOC102: Remove extraneous param from Args
   - DOC202: Remove Returns section from None-returning functions
3. Use Google-style docstrings. Keep docstrings concise — one line where possible.
4. Run ./tools/format_all.sh
5. Verify with ruff check, pylint, pytest, mypy — all must pass
6. Commit the changes
```
