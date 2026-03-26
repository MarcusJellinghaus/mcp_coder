# Implementation Review Log — Run 1

**Issue:** #595 — set-status: show available labels when called without args
**Date:** 2026-03-26

## Round 1 — 2026-03-26

**Findings:**
- (Critical) `format_status_labels` crashes on empty `workflow_labels` — `max()` raises ValueError on empty sequence
- (Critical) `get_status_labels_from_config` is dead code after refactoring — never called in production
- (Critical) `load_labels_config` failure not caught in no-args path — malformed config causes unhandled exception
- (Accept) Unrelated changes (logs_dir removal) in diff — separate PR concern
- (Accept) Inline set comprehension duplicates `get_status_labels_from_config` — tied to dead code finding
- (Accept) `validate_status_label` computes labels set twice — minor inefficiency

**Decisions:**
- Accept #1: Trivial fix, defensive guard. Boy Scout rule.
- Accept #2: Dead code should be reused or removed. Clean Code principle.
- Accept #3: Potential bug in no-args graceful path. Needs fix.
- Skip #4: Out of scope — pre-existing commits, not part of #595 implementation.
- Accept #5: Resolved together with #2 by reusing the existing function.
- Skip #6: Trivial overhead, not worth the change.

**Changes:**
- Added early-return guard in `format_status_labels()` for empty labels
- Replaced inline set comprehension with `get_status_labels_from_config()` call in `execute_set_status`
- Wrapped `load_labels_config` in no-args path with try/except fallback to bundled config
- Added tests: `test_format_status_labels_empty_workflow_labels`, `test_execute_set_status_no_args_malformed_config_fallback`

**Status:** Committed
