# Step 2: Add stderr faulthandler safety net to CLI entry point

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #712).

## LLM Prompt

```
Implement step 2 of issue #712 (see pr_info/steps/summary.md for context).

Add an early stderr-based faulthandler.enable() at the top of src/mcp_coder/cli/main.py,
before heavy imports. This catches any crash during CLI startup. Add a test to verify
faulthandler is enabled. Run all three quality checks after implementation.
```

## WHERE

- **Modify**: `src/mcp_coder/cli/main.py`
- **Modify**: `tests/cli/test_main.py` (add one test)

## WHAT

Add at the very top of `main.py`, after the docstring but before other imports:

```python
import faulthandler
import sys

faulthandler.enable(file=sys.stderr, all_threads=True)
```

The existing `import sys` further down becomes a harmless duplicate (Python deduplicates).

## HOW

- Place the three lines immediately after the module docstring
- Keep all existing imports untouched below
- This runs at import time — zero cost, catches startup crashes

## Test

| Test | What it verifies |
|------|-----------------|
| `test_faulthandler_enabled_on_import` | After importing `mcp_coder.cli.main`, assert `faulthandler.is_enabled()` is `True` |

## DATA

No new functions, no return values. Pure side effect at import time.
