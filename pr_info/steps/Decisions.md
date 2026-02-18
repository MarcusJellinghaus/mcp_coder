# Implementation Decisions

Decisions made during plan review discussion for issue #458.

---

## Decision 1: Step ordering reordered to 1 → 3 → 2 → 4 → 5

**Original order:** 1 → 2 → 3 → 4 → 5

**New order:** 1 → 3 → 2 → 4 → 5

**Rationale:** Moving `_get_configured_repos` to `config.py` (original Step 3) before creating `session_restart.py` (original Step 2) eliminates the need for a temporary import of `_get_configured_repos` from `.orchestrator` in `session_restart.py`. The new module can import from `.config` directly from the start.

---

## Decision 2: `BranchPrepResult` removed from `session_restart.py.__all__`

**Rationale:** `BranchPrepResult` is only used internally within `session_restart.py` by `_prepare_restart_branch` and `restart_closed_sessions`. It was never listed in `orchestrator.py.__all__`, so adding it would silently expand the public API surface. Keeping it private matches the existing convention.

---

## Decision 3: Verification for `get_stage_display_name` / `truncate_title` added to Step 4

**Rationale:** Step 4 changes the re-export source of these two functions from `.orchestrator` to `.helpers`. Before making that change, the implementing LLM should verify no code imports them directly from `orchestrator` (bypassing `__init__.py`). Verification uses `mcp__filesystem__read_file` on relevant files — no grep.

---

## Decision 4: No bash `grep` commands anywhere in plan LLM prompts

**Rationale:** `grep` is not in the project's allowlist (`.claude/settings.local.json`). All verification steps in LLM prompts must use `mcp__filesystem__read_file` or other allowed MCP tools instead of bash grep commands.
