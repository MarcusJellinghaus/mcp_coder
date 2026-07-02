# Implementation Review Log — Issue #988

Improve OpenAI-compatible endpoint diagnostics (verify + 404 hint).

Diagnostics/UX-only change across three steps:
- Step 1: always-on endpoint-shape heuristic in `verify`.
- Step 2: `--check-models` live-probe 404 messaging reword.
- Step 3: shared prompt-path 404 detection + hint helpers.

---

## Round 1 — 2026-07-03

**Findings** (from `/implementation_review`):
1. `_errors_404.py` created as a new module instead of putting helpers in `__init__.py` (as the plan said) — forced by the file-size gate; DRY intact; test import path preserved via re-export.
2. Test-coverage gap: the streaming path (`_ask_text_stream`) had no ollama (non-openai) 404 test, though the non-stream path did and step_3 asked for it.
3. `__init__.py` still 682 lines (over the 600 gate) — pre-existing/widespread condition.
4. Diff mojibake on `config.md` — only in diff rendering; the file is correct UTF-8.

**Decisions**:
- #1 **Skip** — sensible deviation justified by the file-size gate; no functional impact.
- #2 **Accept** — cheap, bounded, adds real regression safety on a separate code path.
- #3 **Skip** — pre-existing, out of scope per the pre-existing-issues rule.
- #4 **Skip** — non-issue (rendering artifact only).

**Changes**: Added `test_non_openai_backend_404_keeps_default_wording` to `TestAskTextStream404Hint` in `tests/llm/providers/langchain/test_langchain_404_hints.py`, asserting an ollama streaming 404 keeps the default "not found" + suggestions wording and omits the OpenAI base-URL hint. Full langchain subset: 408 passed. format_code clean.

**Status**: committed (test-only change).

## Round 2 — 2026-07-03 (convergence pass)

**Findings**: No new actionable findings. All design rules re-verified correct (shape check gated on `api_version` unset + `backend == "openai"`, excluded from `overall_ok`; `/completions`→warn, malformed→warn, missing `/v1`→info; base-URL 404 hint gated on `backend == "openai"`; DRY detection+message helpers). New streaming ollama test present, correct, and green.
**Decisions**: Nothing to accept — converged.
**Changes**: None.
**Status**: no changes needed.

---

## Final Status

- **Rounds run**: 2 (Round 1: one accepted change — added streaming ollama 404 test; Round 2: zero changes, converged).
- **Quality checks**: pylint PASS, mypy PASS, pytest fast subset PASS (4124 passed, 2 skipped), targeted langchain subset 70 passed.
- **vulture**: clean (no output).
- **lint-imports**: PASS — 19 contracts kept, 0 broken.
- **Commits produced this review**: `c55d663` (streaming ollama 404 test).
- **Assessment**: Implementation is a faithful, correct, DRY realization of all three diagnostic steps for issue #988. Ready to merge.
