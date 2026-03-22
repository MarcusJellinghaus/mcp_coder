# Step 11: Add Missing Raises (DOC501)

> **Context:** See [summary.md](summary.md). Final step — after this, `ruff check src tests` should report 0 violations.

## Goal

Add missing `Raises` sections to docstrings where the function raises exceptions but doesn't document them.

## Rules Addressed

| Rule | Description |
|------|-------------|
| DOC501 | Missing `Raises` section in docstring |

## Discovery

```bash
ruff check src --select DOC501
```

## HOW

For each DOC501 violation, read the function, identify which exceptions it raises, and add a `Raises:` section in Google-style format.

```python
def example():
    """Do something.

    Raises:
        ValueError: If input is invalid.
    """
```

## Verification

- `ruff check src --select DOC501` — 0 violations
- **Final full check:** `ruff check src tests` — 0 total violations
- `pytest -n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"` — all pass

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_11.md for context.

Execute step 11: Add missing Raises sections (DOC501). This is the final step.

1. Run `ruff check src --select DOC501` to get the full list
2. For each function, read it and identify which exceptions it raises
3. Add a `Raises:` section in Google-style format
4. Run `./tools/format_all.sh`
5. Verify `ruff check src --select DOC501` reports 0
6. Run full check: `ruff check src tests` — must be 0 total violations
7. Run pylint, pytest, mypy checks
8. Commit the changes
```
