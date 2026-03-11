# Decisions Log — Issue #508

Decisions made during plan review discussion.

## Decision 1: Defer `_get_status_symbols()` move to Step 2

**Context:** Step 1 originally moved `_get_status_symbols()` to `cli/utils.py`,
but the function isn't needed as a shared utility until Step 5, and Step 2
already touches `claude_cli_verification.py`.

**Decision:** Fold the move into Step 2. Step 1 becomes parser-only.

## Decision 2: Keep `verify.py` double-rewrite as planned

**Context:** `verify.py` gets rewritten in Step 2 (temporary shim) and again
in Step 5 (full orchestrator). An alternative was to keep `verify.py` untouched
until Step 5.

**Decision:** Keep as planned — rewrite in both Step 2 and Step 5.

## Decision 3: Keep `overall_ok` naming, add code comment

**Context:** `overall_ok=True` when MLflow is not installed feels counterintuitive.
Alternatives: rename to `severity`, or add a separate field.

**Decision:** Keep `overall_ok` as-is. Add a code comment explaining the semantic
(True = informational / no action needed, False = misconfigured and needs fixing).

## Decision 4: No timeout on MLflow SDK probe

**Context:** The plan used `threading.Timer` for a 10-second timeout on the
MLflow SDK call. Alternatives: `concurrent.futures`, or no timeout at all.

**Decision:** No timeout. This is a verify command, user can Ctrl+C if it hangs.
Removes complexity.

## Decision 5: Keep `_resolve_active_provider` separate from `resolve_llm_method`

**Context:** Both functions read `[llm] provider` from config, but they have
different semantics (different return types, different env vars, different purposes).

**Decision:** Keep them as separate, self-contained functions. The shared config
read is one line — not worth abstracting.

## Decision 6: Include `list_*_models()` in Step 3

**Context:** `--check-models` calls `list_*_models()` functions that don't exist
yet in the backend modules. Alternative: defer to a follow-up issue.

**Decision:** Include full implementation in Step 3. Each backend module
(`openai_backend.py`, `gemini_backend.py`, `anthropic_backend.py`) gets a
`list_*_models()` function.

## Decision 7: Clean break rename of `verify_claude_cli_installation`

**Context:** Step 2 renames `verify_claude_cli_installation()` to `verify_claude()`.
Alternative: keep old name as alias for one step.

**Decision:** Clean break — rename and update all test references in Step 2.
No alias or backwards-compatibility shim.

## Decision 8: `list_*_models()` already exist — keep test file only

**Context:** Step 3 originally included implementing `list_openai_models()`,
`list_gemini_models()`, and `list_anthropic_models()` as new work. These
functions already exist in `llm/providers/langchain/_models.py`.

**Decision:** Remove implementation tasks from Step 3. Keep the test file
`test_langchain_list_models.py` to add coverage for the existing functions.
No changes needed to the existing functions — they accept `api_key`, return
`list[str]`, and raise `ImportError` when the SDK is missing.

## Decision 9: Remove Step 6 reference from summary

**Context:** The summary listed "Step 6 — Integration tests for exit code
logic and end-to-end flow" but no `step_6.md` exists. The exit code and
orchestration tests are already covered in Step 5's `test_verify_orchestration.py`.

**Decision:** Remove the Step 6 reference from the summary. Step 5 covers
those tests sufficiently.

## Decision 10: Add formatting output test in Step 5

**Context:** Step 5 introduces `_format_section()` which produces user-visible
`[OK]`/`[NO]` output. No test specifically asserts the formatted output.

**Decision:** Add a formatting assertion test in `test_verify_orchestration.py`
that asserts specific formatted lines (e.g. `"Claude CLI Found:   [OK] YES"`).
Catches formatting regressions.
