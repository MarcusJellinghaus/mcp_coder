# Plan Review Log — Issue #1004

Unify Claude blocking/streaming onto one streaming core (blocking = drain+assemble).

- Base branch: `main` (branch up to date, no rebase needed)
- Plan state at start: 6 steps, no steps implemented yet (fresh plan review)
- Supervisor: technical-lead session delegating to engineer subagents

---

## Round 1 — 2026-07-02

**Findings** (from `/plan_review` engineer):
- S1: Timeout sweep (Step 3) incomplete vs Requirement 1 / Decision 2 — missing commit-msg (`LLM_COMMIT_TIMEOUT_SECONDS=120`), create-plan's `PROMPT_3_TIMEOUT=900` (only two 600s covered), create-pr actual value is `300` not `600`.
- S2: Step 2 drain-wrapper pseudocode references an undefined command variable for `TimeoutExpired`/`CalledProcessError`.
- S3: Step 5 wrongly claims the Step-7 `check_and_fix_mypy` call is covered by the new handler (it's outside the try; moot under `RUN_MYPY_AFTER_EACH_TASK=False`).
- S4: Step 2 "delete now-dead imports" risks stripping re-exports still imported elsewhere (`McpServersUnavailableError`, `parse_stream_json_*`, etc.).
- S5: Unused `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` imports in two modules + stale `constants.py:36` comment.
- E1 (escalated): unified `text` derives from assembler `text_delta` concat vs blocking's `result`-field — could shift `prompt --json` top-level `text` (AC3).
- E2 (escalated): `~300s` inactivity budget vs "kept below external CI cap"; `PROMPT_3_TIMEOUT=900` the outlier.

**Decisions**:
- E1 — Verified in code: both paths already concat assistant text; only real diffs are `.strip()` and the zero-assistant-text fallback. **Decision: move to streaming**; extend `ResponseAssembler` to `.strip()` + fall back to result-message `result` when no assistant text → `text` stays identical (AC3 literally true). Folded into Step 1.
- E2 — Verified: watchdog is pure per-line silence; a long silent MCP tool call counts as inactivity; icoder runs 300s in prod. **Owner decision: two categories.** Tool-using autonomous sites → new `LLM_INACTIVITY_TIMEOUT_SECONDS = 600` (headroom for silent MCP tool calls, below external CI cap); pure-LLM sites keep CI-analysis 300 / commit-msg 120; finalisation/task-tracker-prep stay 600; create-plan `PROMPT_3_TIMEOUT` 900→600. All constants documented with *why* comments (inactivity, not wall-clock).
- S1–S5 — all accepted, applied as mechanical plan fixes.

**User decisions**:
- Q (text value): "We want to move to streaming." + confirmed the assembler parity approach.
- Q (timeouts): approved the two-category model with `LLM_INACTIVITY_TIMEOUT_SECONDS = 600`; "different constants should be well explained with comments."

**Changes**: Edited `summary.md`, `step_1.md`, `step_2.md`, `step_3.md`, `step_4.md`, `step_5.md` (step_6 untouched). Text-parity added to Step 1; two-category timeout sweep + full caller enumeration + commented constants in Step 3; drain-wrapper pseudocode made self-consistent (`CMD_LABEL` placeholder) + lazy-import + re-export caution in Step 2; import-linter check note in Step 4; corrected mypy-coverage wording in Step 5.

**Status**: committed (plan changed → re-review triggered)
