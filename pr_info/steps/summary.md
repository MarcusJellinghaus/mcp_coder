# Issue #315: Suppress DEBUG logs from urllib3.connectionpool

## Summary

Add suppression for verbose DEBUG logs from `urllib3.connectionpool` in the centralized logging configuration. This reduces log noise when running with DEBUG level while preserving meaningful debug information from the project's own loggers.

## Architectural / Design Changes

**None.** This is a minimal configuration change within the existing logging infrastructure. No new modules, classes, or architectural patterns are introduced.

**Design Decisions (from issue):**
| Topic | Decision |
|-------|----------|
| Scope | Only `urllib3.connectionpool` (not entire urllib3 hierarchy) |
| Other loggers | Keep `github.Requester` visible |
| Log level | `INFO` (hides DEBUG, shows INFO and above) |
| Configurability | Hardcoded (no config needed) |
| Discoverability | Both code comment AND DEBUG log message |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/log_utils.py` | Add 4 lines to `setup_logging()` function |

## Files Created

None.

## Implementation Steps

| Step | Description |
|------|-------------|
| 1 | Add urllib3.connectionpool logger suppression to `setup_logging()` |

## Acceptance Criteria

- [x] DEBUG logs from `urllib3.connectionpool` no longer appear in output
- [x] INFO, WARNING, and ERROR logs from `urllib3.connectionpool` still appear
- [x] Project's own DEBUG logs (`mcp_coder.*`) work as expected
- [x] DEBUG log message indicates suppression at startup
- [x] Code comment explains the suppression
- [x] Tests pass
