# Step 5: Fix Raises Sections

> **Context:** See [summary.md](summary.md) for overall plan. This is step 5 of 4 active steps (Step 3 removed).

## Goal

Add missing `Raises` sections and remove extraneous ones so docstrings accurately reflect which exceptions each function raises.

## Rules Addressed

| Rule | Count | Description |
|---|---|---|
| DOC501 | ~33 | Missing `Raises` section — function raises but docstring doesn't document it |
| DOC502 | ~62 | Extraneous `Raises` — docstring documents raises but function doesn't raise it |

**Total:** ~95 fixes

## WHERE

`src/` only (tests excluded from scope — see [decisions.md](decisions.md)):
- ~53 DOC502 (extraneous) + ~33 DOC501 (missing)

Identify exact files:
```bash
ruff check src --select DOC501,DOC502
```

## WHAT

No new functions. Two types of changes:

1. **DOC501 (add missing Raises):** Add `Raises:` section documenting exceptions the function actually raises
2. **DOC502 (remove extraneous Raises):** Remove `Raises:` entries for exceptions the function doesn't raise, OR verify the exception is raised indirectly and add a `noqa: DOC502` comment if the docstring is intentionally documenting propagated exceptions

## HOW

Google-style Raises format:

```python
def load_config(path: str) -> dict:
    """Load configuration from file.

    Args:
        path: Path to config file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If config file contains invalid syntax.
    """
```

### DOC502 Judgment Calls

DOC502 requires careful review. Three possible actions per violation:

1. **Remove the Raises entry** — if the exception is truly never raised (stale docs)
2. **Keep and add `noqa: DOC502`** — if the exception is raised by a called function and the docstring intentionally documents it for callers (rare, use sparingly)
3. **Fix the code** — if the docstring is correct but the raise statement was accidentally removed (unlikely but check)

Default to option 1 (remove stale docs) unless there's clear reason for option 2.

## ALGORITHM

```
1. Run ruff check to list all DOC501 and DOC502 violations
2. For DOC501: read function, identify raised exceptions, add Raises section
3. For DOC502: read function, verify exception is NOT raised, remove the entry
4. For ambiguous DOC502 cases: check if exception propagates from callees — decide keep or remove
5. Run ./tools/format_all.sh
6. Run ruff check, pylint, pytest, mypy to verify
7. Commit
```

## DATA

No data structures. Output: modified `.py` files with corrected Raises docstring sections.

## Verification

- `ruff check src --select DOC501,DOC502` — should report 0
- **Final full check:** `ruff check src` — should report 0 total violations
- `pylint ./src` — should pass with no C0114/C0115/C0116 violations
- `pytest` — all pass
- `mypy` — no regressions

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md for context.

Execute step 5: Fix Raises sections (final step).

1. Run `ruff check src --select DOC501,DOC502` to get the full violation list
2. For DOC501 (missing Raises):
   - Read the function to identify which exceptions it raises
   - Add a `Raises:` section in Google-style format
3. For DOC502 (extraneous Raises):
   - Read the function to confirm the exception is NOT raised
   - If confirmed stale: remove the Raises entry
   - If the exception propagates from a called function and is important for callers:
     add `# noqa: DOC502` (use sparingly)
4. Run ./tools/format_all.sh
5. Verify ALL checks pass:
   - `ruff check src tests` — 0 total violations (this is the final step)
   - pylint — 0 docstring violations
   - pytest — all pass
   - mypy — no regressions
6. Commit the changes
```
