# Decisions Log for Issue #417

## Discussed Decisions

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Staging directory path | Use shared path `safe_delete_staging` (same as CLI tool) | Both tools share cleanup; files from either get cleaned by either |
| 2 | Error path extraction | Use `error.filename` only, no regex fallback | KISS - simpler implementation |
| 3 | Code reuse | Accept duplication between library and CLI tool | Keeps library self-contained; add comments in CLI tool pointing to library functions |
