# Decisions Log

This document records decisions made during the project plan review discussion.

## Context Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Coordinator run frequency | Every 1 minute | Continuous monitoring loop - caching is valuable |
| Typical number of open issues | 20-100 (medium) | Incremental fetching provides meaningful API savings |
| Cache staleness window acceptable | Yes | System will self-correct on next fetch |

## Implementation Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Implementation approach | Both features together (duplicate protection + incremental fetching) | Deliver complete solution |
| `list_issues_since()` vs extend `list_issues()` | Extend existing `list_issues()` with optional `since` parameter | Less code, one method to maintain |
| Merging steps | Merge Steps 3 (Configuration) and 4 (Integration) | Keep cache logic separate, but config + integration are tightly coupled |
| Integration testing step | Merge into each step using TDD approach | Tests written with implementation |

## Configuration Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cache directory structure | `~/.mcp_coder/coordinator_cache/` | Simple, purpose-specific |
| Default `cache_refresh_minutes` | 1440 minutes (24 hours) | Trust incremental fetching |

## Logging & Quality Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Staleness logging during full refresh | Detailed - log each stale issue with what changed | Helps validate caching strategy is working |
| Atomic file writes guidance | Add explicit temp-file-then-rename pattern in documentation | Common pattern but worth specifying |

## Test Organization Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Test file organization | Keep separate files for unit vs integration tests | As originally planned |
| Cache logic test location | Dedicated `tests/utils/test_coordinator_cache.py` | Cleaner separation, cache logic is conceptually distinct from CLI handling |

## Caching Implementation Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Staleness logging level | Detailed at INFO level | Helps validate caching strategy is working correctly |
| Duplicate protection mechanism | JSON field `last_checked` | Self-contained, explicit, portable |
| Duplicate protection return value | Return empty list `[]` | Clean "too soon, do nothing" behavior |
| Cache file naming | Full repo identifier (`owner_repo.issues.json`) | Ensures uniqueness across different owners with same repo name |
| Error handling granularity | Specific handlers per error type | More informative for troubleshooting |
| Step 2 algorithm detail | Prescriptive helper function structure | Clear expectations for consistent implementation |
| Atomic writes documentation | Document in step file with example | Ensures implementer doesn't miss this important pattern |
