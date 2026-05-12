# Step 6 — Single at-capacity diagnostic log (Item #6)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_6.md`) in
> full. This step uses a simplified design vs. the issue (single log line
> replacing the existing tail message, not two emissions). Follow TDD.
> One commit at the end.

## Goal

When `vscodeclaude launch` is at capacity, log a single line that names the
folders consuming the slots. No log archaeology required to figure out which
sessions are blocking new launches.

## Design choice (KISS deviation from issue)

The issue prescribes adding a new "At max sessions ..." log *and* keeping the
existing "No new sessions started (active: N/M)" tail. Single emission is
simpler — **extend the existing tail message** rather than replace it with a
parallel emission. At capacity, the tail gets the new detailed folder-list
line; below capacity, the tail preserves today's wording verbatim. One log
site, one emission, branched on `current_count >= max_sessions`.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/commands.py`
  (replace the existing "No new sessions started" tail message around line 631)
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
  (drop or downgrade the per-repo "Already at max sessions" log)
- `tests/cli/commands/coordinator/test_commands.py`

## WHAT — function signatures

No signature changes. Replace one log call; drop/downgrade another.

## HOW — integration points

In `execute_coordinator_vscodeclaude`, after the per-repo loop computes
`total_started` and `current_count`, replace the existing else-branch tail
message with:

```python
if total_started:
    # existing branch unchanged: list started sessions
    ...
else:
    if current_count >= max_sessions:
        active_folders = [Path(f).name for f, alive in active_set.items() if alive]
        restarted_folders = [Path(s["folder"]).name for s in restarted]
        logger.log(
            OUTPUT,
            "No new sessions started — at capacity (%d/%d). "
            "Counted: active=%s restarted=%s",
            current_count, max_sessions,
            active_folders, restarted_folders,
        )
    else:
        logger.log(
            OUTPUT,
            "No new sessions started (active: %d/%d)",
            current_count, max_sessions,
        )
```

In `session_launch.py:process_eligible_issues`, downgrade the existing
`"Already at max sessions (%d/%d), skipping"` log from INFO to DEBUG (it's
now redundant with the orchestrator-level line and noisy at INFO when
multiple repos are configured).

## ALGORITHM

```
if total_started:
    log per session   # unchanged
elif current_count >= max_sessions:
    log: "at capacity ... active=[...] restarted=[...]"
else:
    log: "No new sessions started (active: N/M)"   # unchanged
```

## DATA

- `active_folders: list[str]` — basenames of folders flagged active in
  `active_set`.
- `restarted_folders: list[str]` — basenames of restarted sessions' folders.

## Tests (write first)

In `tests/cli/commands/coordinator/test_commands.py`:

1. **At-capacity log includes folder basenames**: set up `active_set` with
   two `True` folders and `max_sessions=2`. Patch
   `process_eligible_issues` to return `[]`. Capture log output. Assert the
   captured line contains the two folder basenames.
2. **Below-capacity message unchanged**: `active_set` has zero active
   folders, no sessions started → log line matches the existing
   `"No new sessions started (active: 0/3)"` format.
3. **Per-repo log downgraded**: assert
   `"Already at max sessions"` no longer appears at INFO when multiple repos
   are processed at capacity (DEBUG only). If existing tests asserted this
   message N times, update them.

## Done when

- All tests pass (including any existing tests that relied on the dropped
  per-repo INFO log — adjust them to assert the new single line).
- mypy, pylint clean.
- One commit: tests + implementation.
