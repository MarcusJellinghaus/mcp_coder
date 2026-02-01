# Implementation Decisions

## Decision 1: Stream-JSON Output Format

**Context:** Need better debugging and real-time monitoring of Claude CLI interactions.

**Decision:** Use `--output-format stream-json` instead of `--output-format json`.

**Rationale:**
- Enables real-time monitoring via `tail -f`
- Captures full message history for debugging
- Includes cost and usage statistics
- NDJSON format is easy to parse line-by-line

## Decision 2: Log File Naming Convention

**Context:** Need to correlate log files with git branches/issues for debugging.

**Decision:** Use format `session_{timestamp}_{branch_id}.ndjson` where:
- `timestamp`: `YYYYMMDD_HHMMSS_ffffff`
- `branch_id`: First 10 chars of sanitized branch identifier

**Rationale:**
- Timestamp ensures uniqueness
- Branch ID provides context without excessive length
- `.ndjson` extension indicates newline-delimited JSON format

## Decision 3: Branch Identifier Extraction

**Context:** Need short, meaningful identifier from branch names.

**Decision:** Extract identifier as follows:
- For `123-feature-name` → `123` (prefer numeric issue IDs)
- For `fix/improve-logging` → `fix` (use prefix before slash)
- Sanitize to alphanumeric only, max 10 chars

**Rationale:**
- Issue IDs are most useful for correlation
- Branch type prefixes (fix, feat) provide context
- Short length keeps filenames manageable

## Decision 4: Fallback for Missing Branch

**Context:** Some call sites may not have branch info but have issue_id.

**Decision:** If branch name unavailable but issue_id known, use `{issue_id}-issue` format.

**Rationale:**
- Maintains correlation capability
- Clear indication it's derived from issue, not actual branch
- Consistent with branch naming conventions

## Decision 5: Test File Organization

**Context:** `test_claude_code_cli.py` exceeds 750-line limit (826 lines).

**Decision:** Split into three files:
1. `test_claude_cli_stream_parsing.py` - Stream parsing tests (~230 lines)
2. `test_claude_code_cli.py` - Core CLI tests (~380 lines)
3. `test_claude_cli_wrappers.py` - IO wrappers and logging tests (~220 lines)

**Rationale:**
- Logical grouping by functionality
- Each file well under 750-line limit
- Clear separation of concerns
