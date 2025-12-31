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
