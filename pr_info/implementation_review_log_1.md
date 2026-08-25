# review-implementation review log 1

## Round 1 — 2026-08-25
**Findings**:
I'll start by gathering context.`src/mcp_coder/llm/providers/langchain/__init__.py:132` — medium — `hint = f"tried {dialed}" if dialed else base_url_hint` *replaces* the per-backend hint instead of adding to it, so connection errors lose `"base_url/OLLAMA_HOST if not localhost"` (ollama) and `"base_url if using a custom server"` (openai) exactly when a client was constructed; the rendered line also reads `2. base_url: tried <url>`, mixing label and action.

`docs/configuration/config.md:330` — medium — the `[llm.langchain]` field table still marks `api_key` (and `base_url`) as Required = "No", contradicting the new contract (missing `api_key` is an exit-1 error for openai/azure/gemini/anthropic; `base_url` is required in Azure mode) and the scenario→values table added four rows below at `:346`.

`src/mcp_coder/llm/providers/langchain/_config_diagnostics.py:46` — low — `"api_version": "optional"` in the `openai` contract row is unreachable: `mode_of()` promotes any truthy `api_version` under `openai` to the `azure` mode, so this entry can never be evaluated with a value set.

`src/mcp_coder/llm/providers/langchain/_config_diagnostics.py:271` — low — `_UNSET_TARGET` and `_NOT_CONFIGURED` (`:508`) are two constants holding the identical literal `"(not configured)"`; `_check_base_url_shape` keys its skip on the first while the echo renders the second, so changing one silently breaks the skip.

`src/mcp_coder/llm/providers/langchain/verification.py:231` — low — the shape-check guard skips only `"n/a"` and `_UNSET_TARGET`; `_UNKNOWN_TARGET` (`"(unknown)"`, produced by `_fallback_url` at `_config_diagnostics.py:435`) reaches the heuristic and renders as `"(unknown) — malformed URL; use e.g. https://host/v1"`. `"n/a"` is also re-typed here rather than imported as a shared sentinel.

`src/mcp_coder/llm/providers/langchain/__init__.py:257` — low — the trailing `raise ValueError("Unsupported langchain backend: ...")` is now dead code: `validate()` emits the same message for any backend outside `_SUPPORTED_BACKENDS` and lines 216-218 raise it first.

`src/mcp_coder/llm/providers/langchain/verification.py:21` — low — imports four underscore-private names (`_API_KEY_ENV`, `_KEYLESS_ENV`, `_UNSET_TARGET`, `_targets_match`) across the module boundary from `_config_diagnostics`; these are effectively that module's public surface and should be named accordingly.
**Decisions**:
Verdict(decision='tasks', tasks=["In src/mcp_coder/llm/providers/langchain/__init__.py around line 132, stop letting the dialed-URL hint replace the per-backend base_url hint: combine them so connection errors still surface the ollama ('base_url/OLLAMA_HOST if not localhost') and openai ('base_url if using a custom server') guidance when a client was constructed, and fix the rendered line so it no longer reads '2. base_url: tried <url>' (keep the label and the tried-URL detail distinct).", "In docs/configuration/config.md around line 330, update the [llm.langchain] field table to match the current contract and the scenario->values table at line 346: mark api_key as required for openai/azure/gemini/anthropic (missing api_key exits 1) and base_url as required in Azure mode, instead of Required = 'No'.", "In src/mcp_coder/llm/providers/langchain/verification.py around line 231, extend the shape-check skip guard to also skip _UNKNOWN_TARGET ('(unknown)', produced by _fallback_url in _config_diagnostics.py:435) so it no longer renders as '(unknown) - malformed URL; use e.g. https://host/v1'; import the sentinel rather than re-typing the literal, and do the same for the 'n/a' literal."], escalate_reason=None)
**Changes**:
rebase-needed
**Escalate reason**: rebase
