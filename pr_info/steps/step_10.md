# Step 10: Remove Extraneous Raises (DOC502)

> **Context:** See [summary.md](summary.md). Raises fixes split from DOC501 to keep tasks small.

## Goal

Remove extraneous `Raises` entries from docstrings where the function doesn't actually raise that exception.

## Rules Addressed

| Rule | Description |
|------|-------------|
| DOC502 | Extraneous exception in docstring Raises section |

## Discovery

```bash
ruff check src --select DOC502
```

## HOW

For each DOC502 violation, read the function and choose:
1. **Remove the Raises entry** (default — stale docs)
2. **Keep and add `# noqa: DOC502`** (exception propagates from callee, intentionally documented — use sparingly)
3. **Fix the code** (raise statement accidentally removed — unlikely, but check)

See [decisions.md](decisions.md) decision #2 for policy.

## Verification

- `ruff check src --select DOC502` — 0 violations
- `pytest -n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"` — all pass

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_10.md for context.

Execute step 10: Remove extraneous Raises entries (DOC502).

1. Run `ruff check src --select DOC502` to get the full list
2. For each violation, read the function to confirm the exception is NOT raised
3. Default action: remove the Raises entry
4. If the exception propagates from a called function and is important for callers: add `# noqa: DOC502` (use sparingly)
5. Run `./tools/format_all.sh`
6. Verify `ruff check src --select DOC502` reports 0
7. Run pylint, pytest, mypy checks
8. Commit the changes
```
