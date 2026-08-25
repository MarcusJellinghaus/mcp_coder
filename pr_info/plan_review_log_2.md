# Plan review log 2 — issue #1117

Supervised run. Run 1 (`plan_review_log_1.md`) ran 5 automated rounds and
escalated with four unresolved high findings; this run picks those up first,
then re-reviews to convergence.

Branch: `1117-langchain-backend-config-verify-diagnosability-base-url-rename-per-backend-contract-verify-overhaul`
Base: `main` (branch 2 commits behind; both unrelated to the touched files)
Task tracker: empty — nothing implemented yet, so the whole plan is in scope.

---

## Round 1 — 2026-08-25

**Findings**: carried over from run 1's escalation (four unresolved high findings, no new review this round):
- `step_5.md` — `_API_KEY_ENV`'s `azure` row mapped only `OPENAI_API_KEY`; a working Azure setup keyed off `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_AD_TOKEN` would hit a false required-error and exit 1.
- `step_5.md` — same for `gemini`: only `GEMINI_API_KEY` mapped, ignoring `GOOGLE_API_KEY` and the keyless Vertex path.
- `step_7.md` — `describe_effective_config(config, target, api_key_source)` had neither the resolved key nor `overridden`, so its ALGORITHM/DATA were unimplementable without fabricating provenance.
- `step_9.md` — HOW/ALGORITHM contradiction on the `api_key` row (outstanding since run 1 round 3); the HOW reading hides the contract message the acceptance criterion requires.

**Decisions**: all four accepted and delegated — each is a correctness fix to the plan, none changes scope or architecture. Step 9 resolved in favour of the ALGORITHM (finding supplies both `ok` and `value`) because the AC demands the contract message reach the user. Gemini carve-out delegated to the engineer with the rule "simplest that cannot break a working setup".

**User decisions**: none required.

**Changes**:
- `step_5.md` — `_API_KEY_ENV` becomes `dict[str, tuple[str, ...]]`; azure row `("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_AD_TOKEN")`; new `_KEYLESS_ENV = {"gemini": "GOOGLE_GENAI_USE_VERTEXAI"}` satisfied by presence (deliberately over-permissive; a truthiness parse could recreate the false required-error). Required-messages enumerate the whole row. TDD cases 4c/4d/5b added. All rows measured against the installed SDK in the project venv.
- `step_7.md` — `describe_effective_config(config, target, *, api_key_masked, api_key_source, api_key_overridden)`; masked value passed in to keep the builder pure and avoid importing `_mask_api_key` back from `verification.py`. Undefined `masked` replaced by a defined `key_row`. TDD 3b pins that a losing config `api_key` never appears.
- `step_9.md` — contradicting HOW sentence deleted; finding present → both `ok` and `value` from the finding, else masked key. TDD cases 2/2b/3 assert rendered value text.
- `summary.md` — contract-table footnote ¹ widened to match step 5.
- `Decisions.md` — created by `/plan_update` (entries A–D, lettered so they cannot collide with the issue's "Decision N").

**Status**: committed
