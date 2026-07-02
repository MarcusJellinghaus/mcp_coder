# Plan Review Log — Issue #988 (Improve OpenAI-compatible endpoint diagnostics)

Supervisor-driven plan review. Base branch: `main`. Branch up to date (no rebase needed).
Plan: 3 steps (Part A1 verify heuristic, Part A2 --check-models messaging, Part B 404 hint helper).

## Round 1 — 2026-07-02
**Findings** (from `/plan_review`):
- F1 (design/req): Plan + issue claim `--check-models` is the only check that can fail `verify` on a bad endpoint. False in current code — `available_models` is excluded from `overall_ok`/exit code; the unified "Reply with OK" test prompt is what fails `verify`.
- F2 (DRY): Step 3 factors the 404 hint *message* into `_format_404_hint`, but the 404 *detection* predicate stays copy-pasted in `_ask_text`/`_ask_text_stream`.
- F3 (docs): No step updates `docs/configuration/config.md`; `endpoint` isn't documented as base-URL-only, the exact cause of the reported 404.
- F4 (granularity): Steps 1 & 2 could merge (both Part A, same file, Step 2 tiny).
- F5 (nit): integration test must patch `...verification._load_langchain_config` (bound via `from . import`).
- Verified accurate: renderer contract, duplicated 404 block, `try/except…pass` swallow, `api_version` Azure gating, target function names, test files exist.

**Decisions**:
- F1 → ask user (design/scope question).
- F2 → accept (straightforward DRY, serves issue's anti-drift goal).
- F3 → accept, minimal (note + one relay example; directly addresses root cause).
- F4 → skip (keep small, order-independent commits).
- F5 → skip (existing tests already handle it).

**User decisions**:
- F1: "Fix rationale text only (diagnostics-only)." Correct wording in summary.md/step_2.md; Step 2 stays a pure reword of the /models 404 message; no behavior change; `overall_ok`/exit code unchanged.

**Changes** (via `/plan_update`):
- `summary.md`: corrected F1 rationale; updated file table (added config.md, Step 1) and Step 3 row (named `_is_404_error` + `_format_404_hint`); updated step-overview bullets.
- `step_1.md`: added `docs/configuration/config.md` docs edit (base-URL-only note + relay example).
- `step_2.md`: added "pure reword" clarification (available_models excluded from overall_ok; message-only change).
- `step_3.md`: added `_is_404_error(exc)` detection helper replacing inline predicates at both call sites; added algorithm + test note.
- `Decisions.md`: created; logs F1/F2/F3 decisions and not-changing items.

**Status**: plan changed → committed (`2b5a6d6`) → run Round 2.

## Round 2 — 2026-07-02
**Findings** (from `/plan_review` on the revised plan):
- Verified all three Round-1 corrections are correctly applied and internally consistent (F1 rationale, `_is_404_error` extraction, `config.md` edit); Step 3 matches source; `config.md` targets accurate.
- Finding A (correctness/consistency): Step 3's `_format_404_hint` custom-endpoint branch fires on `endpoint set + api_version unset`, but the `ollama` backend also matches that → an Ollama 404 would get OpenAI-specific base-URL wording and lose Ollama model suggestions (a regression).
- Minor (non-blocking): summary.md prose conflates "hint" with the `install_hint` key; planning-principles compliant. No changes required.

**Decisions**:
- Finding A → accept autonomously (gate the branch on `backend == "openai"`, matching Step 1's shape check; narrows firing, prevents regression, no scope/architecture change).
- Minor notes → skip (no change required).

**User decisions**: none (no design/scope question this round).

**Changes** (via `/plan_update`):
- `step_3.md`: gated `_format_404_hint` base-URL branch on `backend == "openai"`; updated pseudocode/docstring/tests (added ollama fall-through test) and LLM prompt.
- `summary.md`: made design point 3, Step 3 row, and step-overview consistent with the openai gate + ollama fall-through.
- `Decisions.md`: logged the openai-gate decision + Ollama-regression rationale.

**Status**: plan changed → will commit and run Round 3.

