# Implementation Review Log — Issue #727 (Add Ollama backend to LangChain provider)

Run 1 — supervisor: technical lead orchestrating subagents.
Started: 2026-05-12
Branch: 727-add-ollama-backend-to-langchain-provider

## Round 1 — 2026-05-12

**Findings**:
1. `_preflight.py` extracted as new module instead of inline in `__init__.py` (deviates from Decisions P6).
2. `list_ollama_models()` silently discards `api_key`, while `_check_ollama_daemon()` and `check_ollama_tool_capability()` pass it via `headers` kwarg — inconsistent for proxy-auth Ollama.
3. `pyproject.toml` mypy overrides added but `summary.md` claims "no change".
4. `_ollama_preflight` does an HTTP round-trip per agent call, no caching (documented decision Q3).
5. Tests assert `"llama" not in result["value"].lower()` with brittle `"some-model"` fixture.
6. Pre-existing `endpoint\base_url` typo in `_exceptions.py:101` (`\b` → backspace).
7. `_check_ollama_daemon` (single-underscore) called from sibling module `verification.py`.

**Decisions**:
- 1: SKIP — split driven by 750-line CI threshold (commit `26ad1a9`); `pr_info/` is throwaway scratch.
- 2: ACCEPT — real proxy-auth consistency gap; the PR explicitly supports proxy-auth elsewhere, listing must match.
- 3: SKIP — same as 1.
- 4: SKIP — explicit decision Q3.
- 5: SKIP — speculative ("if a future contributor mistakenly...").
- 6: SKIP — pre-existing, affects all backends; file separately if anyone cares.
- 7: SKIP — single underscore = package-private by convention; not a real defect.

**Quality checks reported**: pylint PASS, mypy PASS, Ollama tests PASS. Two pre-existing Windows-specific flakes (`test_verify_shows_custom_prompt_paths`, `test_commit_auto_no_mcp_config_arg`) unrelated to this PR.

**Changes**: in progress — engineer to wire `headers` kwarg into `list_ollama_models()` with the same `TypeError` fallback used by the other two probes.

**Changes** (committed `1f267d0`, pushed):
- `src/mcp_coder/llm/providers/langchain/_models.py` — `list_ollama_models` now forwards `api_key` as `Authorization: Bearer …` header with the same `TypeError` fallback used by the two sibling probes.
- `tests/llm/providers/langchain/test_langchain_models_ollama.py` — added `test_passes_auth_header_when_api_key_set`.

**Status**: committed.

## Round 2 — 2026-05-12

**Findings**: none. Round 2 reviewer verified the Round 1 fix (`headers` kwarg forwarding in `list_ollama_models`) is symmetric with the two sibling Ollama probes and that the new test covers both `api_key` set and unset paths. Three minor observations were flagged as out-of-scope:
- No explicit `TypeError`-fallback test for `list_ollama_models` (speculative; matches sibling coverage shape).
- `_ollama_preflight` raises `ValueError` for a missing `ollama` SDK while `_create_chat_model` would raise `ImportError` for the same condition — UX nit, not a regression.
- `__init__.py` is 729 lines (under the file-size threshold, allowlist-suppressed). Not blocking.

**Quality checks reported**: pylint clean, mypy clean, ~3966 fast unit tests green. The combined-marker pytest runner trips on stderr from pre-existing intentional-argparse-rejection tests, but subdirectory runs are all green.

**Changes**: none.

**Status**: no changes needed — loop terminates.

## Final Status

- **Rounds run**: 2.
- **Commits produced this review**: 1 (`1f267d0` — Forward `api_key` as Bearer header in `list_ollama_models`).
- **Supervisor checks**: `run_vulture_check` produced no output (clean). `run_lint_imports_check` reports 23 contracts kept, 0 broken.
- **Outstanding issues**: none that block merge. Out-of-scope follow-ups (do NOT block this PR):
  - `_exceptions.py:101` `endpoint\base_url` escape typo (`\b` interpreted as backspace) — affects all four backends; file separately.
  - `_ollama_preflight` raises `ValueError` for a missing `ollama` SDK whereas `_create_chat_model` would raise `ImportError`. UX consistency nit.
  - The combined-marker pytest runner returns "Internal Error" when stderr is non-empty during intentional argparse-rejection tests. Pre-existing runner quirk, unrelated to #727.
- **Verdict**: implementation review complete. The Ollama-backend diff is consistent with the plan, symmetric with the three sibling backends, and clean on all supervisor checks.
