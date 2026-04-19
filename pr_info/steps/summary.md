# Summary: Migrate .mcp.json to new KV format with repo URLs (#860)

## Overview

mcp-workspace now requires a new key-value format for `--reference-project` args. The old `name=path` format is deprecated. This is a **config-only change** — no source code or tests are modified.

## Architectural / Design Changes

**None.** This PR touches only configuration files. No code, no new modules, no architectural changes. The runtime behavior is identical — mcp-workspace receives the same reference project names and paths, plus an additional `url` field per project.

## Files Modified

| File | Change |
|------|--------|
| `.mcp.json` | Migrate 4 `--reference-project` values from old `name=path` format to new `name=...,path=...,url=...` KV format |
| `.claude/settings.local.json` | Add `mcp__workspace__search_reference_files` permission |

## No Files Created or Deleted

## Test-Driven Development

Not applicable — these are declarative config files with no testable logic.

## Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Migrate `.mcp.json` reference-project args to new KV format and add `search_reference_files` permission | `chore(config): migrate .mcp.json to KV format and add search_reference_files permission` |
