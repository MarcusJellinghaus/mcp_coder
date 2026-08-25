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

---

## Round 2 — 2026-08-25

**Findings** (fresh review; the round-1 fixes were re-measured and confirmed consistent):
- `step_7.md:148` / `step_9.md:94` — medium — `_resolve_api_key` still keys off `verification._BACKEND_ENV_VARS` (one var per *backend*) while step 5's contract is mode-keyed. An Azure setup keyed off `AZURE_OPENAI_API_KEY`, or gemini off `GOOGLE_API_KEY`, would render `API key [OK] not set (optional)` — false provenance inside the block whose purpose is truthful provenance.
- `step_6.md:110` — medium — the most common ollama setup (no `base_url`, no `OLLAMA_HOST`) prints `base_url (unknown)` when the truthful `http://localhost:11434` is knowable. Raised in run 1 round 4 but never delegated.
- `step_8.md:94` — low — the DATA example shows `[WARN]` for a URL the step's own ALGORITHM classifies `[OK]`; risk of an implementer flipping the heuristic to match. `(source: …)` also missing from two ALGORITHM branches.
- `step_7.md:102` — low — `_matches_config_base_url` used but declared nowhere.
- `step_5.md:139` / `summary.md:44` — low, process — the plan deliberately overrides issue Decision 5 and its acceptance criterion.

**Decisions**: first four accepted and delegated — all correctness or consistency fixes, no scope change. The fifth escalated to the user: it needs an edit to the issue, not the plan.

**User decisions**: asked whether to amend issue #1117's Decision 5 and the matching AC to say hard error rather than exit-neutral warning, given two SDK measurements showing a keyless openai config cannot construct a client. **Answer: yes, update the issue.** Applied via the issue-updater agent — Decision 5 (marked *Revised:*), the acceptance criterion, and footnote ¹ under the contract table. Body only; no label or status change.

**Changes**:
- `step_6.md` — `_OLLAMA_DEFAULT_URL` fallback replaces the `(unknown)` sentinel; `_targets_match` promoted into the declared module surface.
- `step_7.md` / `step_9.md` — `_BACKEND_ENV_VARS` deleted in favour of the mode-keyed `_API_KEY_ENV`; gemini's keyless Vertex carve-out renders `satisfied via …` rather than `not set (optional)`; `_matches_config_base_url` expressed via `_targets_match`.
- `step_8.md` — DATA example corrected to `[OK]` plus a genuinely-warning `/completions` row; `(source: …)` spelled out in all four branches.
- `summary.md` — §7 and the files-modified table updated.
- `Decisions.md` — entries E–H.
- Issue #1117 — Decision 5, one AC, footnote ¹.

**Status**: committed

---

## Round 3 — 2026-08-25

**Findings**:
- `step_7.md:181` / `step_9.md:100` / `Decisions.md:62` — high — round 2's mode-keyed `_API_KEY_ENV` was reused for *provenance* as well as presence, but only `_API_KEY_ENV[mode][0]` is read by our own code (`create_openai_model:36` etc.); the rest are SDK fallbacks reached only when no key is passed. Azure with a config `api_key` plus `AZURE_OPENAI_API_KEY` exported would render the wrong masked value, a false "overrides config.toml" label and a spurious `API key override [WARN]`.
- `step_8.md:94` / `:3` — low — TDD case 2 pins a case that cannot occur: `create_openai_model` always passes `base_url=<config value>`, and both the SDK and `_resolve_gateway_config` give an explicit `base_url` precedence, so env redirection only happens when config is unset.
- `step_6.md:16` — low — `_REDIRECT_ENV["openai"]` in inverted precedence order; `OPENAI_API_BASE` is consumed by langchain before the SDK ever reads `OPENAI_BASE_URL`.
- `step_6.md:130` — low — two false sentinel provenance strings: "backend has no configurable target" for unset/typo'd backends, and a `config.toml (unverified …)` label on a value config never supplied — the common path when the contract is violated.

**Decisions**: all four accepted and delegated. The high finding is a genuine consequence of round 2's fix overshooting — widening the env-var list was right for presence checking, wrong to reuse for provenance. No scope or design change, so nothing escalated.

**User decisions**: none this round. (Marcus asked to run the loop to convergence without check-ins unless something needs a scope or design call.)

**Changes**:
- `step_6.md` — `_NO_BACKEND_TARGET` sentinel gated on `mode_of(config) is None`; `_REDIRECT_ENV["openai"]` reordered to `OPENAI_API_BASE, OPENAI_BASE_URL, AZURE_OPENAI_ENDPOINT` with a note that tuple order is the same-value tie-break and must reflect real precedence; unverified source names `config.toml` only when config supplied the value; TDD 2c/4b/5b added.
- `step_7.md` — resolution order fixed to primary var > config > remaining vars > `_KEYLESS_ENV`, `overridden=True` only when the primary beats config; explicit note that step 5's `validate()` presence check is order-independent and unaffected; TDD 3d added; TDD 6b reworded.
- `step_8.md` — opening trimmed to the one real inaccuracy; TDD case 2 reframed to "config unset, `OPENAI_API_BASE` redirecting, source named".
- `step_9.md`, `summary.md` §2/§7, `Decisions.md` (E corrected, I–L added) — aligned.

**Status**: committed

---

## Round 4 — 2026-08-25

**Findings** (the reviewer re-verified all round-3 changes against the installed SDK and found them correct; only three items remained):
- `step_7.md:176` — low — the `api_key_override` row's f-string reuses `env_var`, bound 24 lines earlier to a *base-URL* redirect variable (often `None`), so it would print `OPENAI_API_BASE env var overrides … api_key` or `None env var overrides …`. TDD case 7 asserted only the row's presence, so it would not catch it.
- `step_7.md:189` — low — the echo's `mode` row had no guard for an unset or typo'd `backend`, rendering `plain None (api_version not set)`; the `backend` and `base_url` rows both guard this case already.
- Non-blocking type note — `resolve_target(config: Mapping[...])` calls `_create_chat_model(config: dict[...])`; strict mypy rejects that, and mypy-green is a per-step exit criterion, so step 6 would not go green as written.

**Decisions**: all three accepted and delegated. Nothing escalated — no scope or design content.

**Changes**:
- `step_7.md` — override row built from `key_source` and gated on `key_overridden`; TDD 7 now runs the same config with and without `OPENAI_BASE_URL` exported and requires identical text naming no redirect variable. `mode` row renders `(not applicable — backend not configured)` when `mode_of(config) is None`; TDD 1 extended to unset and typo'd backends.
- `step_6.md` — `_create_chat_model`'s parameter widened to `Mapping[str, str | None]` (body is read-only, all four call sites pass a `dict`, so widening the callee churns nothing); `__init__.py` added to WHERE.
- `summary.md` — files-modified row for `__init__.py` now lists step 6.
- `Decisions.md` — entries M–O.

**Status**: committed
