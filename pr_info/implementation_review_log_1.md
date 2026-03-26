# Implementation Review Log — Run 1

**Issue:** #593 — Fix MLflow parameter conflict when logging multiple prompts in same run
**Date:** 2026-03-26

## Round 1 — 2026-03-26

**Findings:**
- C1 (Critical): Duplicate `step_N_prompt.txt` artifact — Phase 1 and `log_conversation()` both write it
- C2 (Critical): `mlflow_logger.py` exceeds 750-line limit (821 lines)
- C3 (Medium-Critical): `log_error_metrics()` doesn't use step-aware metrics
- S1: `tool_trace.json` artifact not step-prefixed — overwrites in multi-prompt sessions
- S2: ~30 lines duplicated between `log_conversation()` and `log_conversation_artifacts()`
- S3: `_run_step_count` grows unboundedly — no cleanup on LRU eviction
- S4: Mixed `Dict` vs `dict` typing style

**Decisions:**
- C1: **Skip** — intentional crash insurance design; MLflow silently overwrites; no bug
- C2: **Skip** — verify functions are pre-existing code not modified by this PR; out of scope
- C3: **Accept** — real consistency bug; error metrics in resumed sessions lack step index
- S1: **Accept** — real data loss; tool traces overwrite each other in multi-prompt sessions
- S2: **Accept** — DRY fix; extracted `_log_step_params_and_artifacts()` private method
- S3: **Accept** — memory leak fix; clean up step count on LRU eviction
- S4: **Skip** — cosmetic; "Don't change working code for cosmetic reasons"

**Changes:**
- `log_error_metrics()` now passes `step=self.current_step()` and calls `_advance_step()`
- Tool trace artifact changed to `f"step_{step}_tool_trace.json"`
- Extracted `_log_step_params_and_artifacts()` to deduplicate shared logic
- LRU eviction in `end_run()` now also removes `_run_step_count` entry
- Updated test assertion for step-prefixed tool trace

**Status:** Committed
