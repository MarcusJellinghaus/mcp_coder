# Step 4: Triage logger.info() calls — promote progress messages to NOTICE

**References:** [summary.md](summary.md) — Part 2 (continued)

## Goal

Audit existing `logger.info()` calls across the codebase. Promote user-facing progress messages to NOTICE level. Keep operational chatter as INFO.

## WHERE

All source files under `src/mcp_coder/` that use `logger.info()`. Primary candidates:

- `src/mcp_coder/cli/commands/*.py` — CLI command modules
- `src/mcp_coder/workflows/*.py` — workflow modules
- `src/mcp_coder/checks/*.py` — check modules

## WHAT

### Classification Rules

**Promote to `logger.log(NOTICE, ...)` or `logger.notice(...)`:**
- User-facing progress/status messages: "CI passed", "Fix attempt 1/3", "Updated issue #N to status-X", "PR created", "Plan generated"
- Completion messages: "Command X completed successfully"
- Action confirmations: "Labels synced", "Branch rebased"

**Keep as `logger.info()`:**
- Operational startup/routing: "Starting X detection", "No command provided, showing help", "Executing help command"
- Internal state: "Loading config from...", "Found N issues", "Checking branch..."
- Debug-adjacent: "Skipping...", "Using default..."

### Import pattern

In each file that gets NOTICE calls, add:
```python
from mcp_coder.utils.log_utils import NOTICE
```

Then use either:
```python
logger.log(NOTICE, "User-facing message")
# or (if .notice() method is preferred):
logger.notice("User-facing message")  # type: ignore[attr-defined]
```

Prefer `logger.log(NOTICE, ...)` to avoid the `type: ignore` comment.

## HOW

1. Search for all `logger.info(` calls in `src/mcp_coder/`
2. For each, classify as progress (→ NOTICE) or chatter (→ stays INFO)
3. Update the call
4. Add `NOTICE` import where needed

## ALGORITHM

```
for each file in src/mcp_coder/:
    for each logger.info() call:
        if message is user-facing progress/completion:
            change to logger.log(NOTICE, ...)
            add NOTICE import if not present
        else:
            leave as logger.info()
```

## DATA

No data structure changes.

## Tests

No new tests needed. Existing tests don't assert on specific log levels for most info messages. If any test asserts `mock_logger.info.assert_called_with(...)` for a message that's being promoted, update the assertion to `mock_logger.log.assert_called_with(NOTICE, ...)`.

## LLM Prompt

```
Please read pr_info/steps/summary.md and pr_info/steps/step_4.md.
Implement step 4: Triage logger.info() calls — promote progress messages to NOTICE.

Search all files under src/mcp_coder/ for logger.info() calls.
Classify each as:
- User-facing progress → change to logger.log(NOTICE, ...)
- Operational chatter → keep as logger.info()

Use `from mcp_coder.utils.log_utils import NOTICE` and `logger.log(NOTICE, ...)` pattern.
Do NOT change WARNING/ERROR/DEBUG calls.
Update any test assertions that break due to the level change.

Run all quality checks after changes. One commit for this step.
```
