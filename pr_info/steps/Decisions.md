# Decisions

## Decision 1: ~~Public `is_enabled` API on MLflowLogger~~ DROPPED

**Context:** Step 2's context manager needs to check if MLflow is enabled. `MLflowLogger` has `_is_enabled()` (private) which checks both `config.enabled` and `is_mlflow_available()`.

**Original decision:** Rename `_is_enabled()` to `is_enabled()` to make it a public method.

**Updated decision:** Dropped. The context manager will call `logger._is_enabled()` directly. Adding a public API is unnecessary scope creep for a single internal caller. Keeps the change minimal.

**Affected steps:** Step 2 (no rename needed, use `_is_enabled()` directly).

## Decision 2: Phase 1 / Phase 2 artifact strategy

**Context:** `log_conversation()` already logs `prompt.txt` internally. If Phase 1 also logs it, there's a duplicate. The motivation for Phase 1 is crash-survivability — the prompt artifact should be on disk before the LLM call starts.

**Decision:** Phase 1 logs `start_run()` + `log_artifact(prompt, "prompt.txt")` only (minimal survival data). Phase 2 calls `log_conversation()` which re-logs `prompt.txt` — this is a harmless overwrite of the same filename. No need to decompose `log_conversation()`.

**Rationale:** MLflow artifacts are written to disk immediately on `log_artifact()`. If the process is killed during the LLM call, the prompt artifact survives. The overwrite on success is a no-op in practice.

**Affected steps:** Step 2 (pseudocode updated).
