# Implementation Review Log — Run 2

Branch: `264-coordinator-detect-unlinked-branches-by-issue-number-pattern`
Date: 2026-03-22

## Round 1 — 2026-03-22

**Findings:**
- C1: Missing guard on `repo_full_name` before `.split("/", 1)` in `_handle_intervention_mode()` — `_get_repo_full_name_from_url` can return `""`, causing ValueError
- C2: `_prepare_restart_branch` defaults `repo_owner=""` and `repo_name=""` — masks bugs, all callers provide values
- S1: Two separate features in one PR — process observation
- S2: `list()` materializes all refs before truncation — YAGNI (deferred in round 1)
- S3: Regex compiled on every call — negligible, YAGNI
- S4: `labels_schema.md` location — unrelated to #264

**Decisions:**
- C1: Accept — real bug, other call sites guard against this
- C2: Accept — Boy Scout fix, empty defaults mask bugs
- S1: Skip — process observation, already committed
- S2: Skip — already deferred as YAGNI in review round 1
- S3: Skip — called once per resolution, negligible
- S4: Skip — unrelated to issue #264

**Changes:**
- Added empty-string guard on `repo_full_name` in `_handle_intervention_mode()` (commands.py)
- Removed default empty-string values from `repo_owner`/`repo_name` params in `_prepare_restart_branch()` (session_restart.py)
- Updated 4 test call sites to pass now-required params (test_orchestrator_sessions.py)

**Status:** Committed
