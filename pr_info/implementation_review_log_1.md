# Implementation Review Log #1 — Issue #916

**Branch:** `916-icoder-claude-code-streaming-broken-stdin-not-piped-to-cli`
**Date started:** 2026-04-27
**Scope:** Test-only additions for iCoder/Claude streaming (issue #916). Dependency pin to mcp-coder-utils git source. No production code changes.

## Round 1 — 2026-04-27

**Findings (from `/implementation_review` engineer):**
1. New streaming integration tests don't pass `logs_dir`; `get_stream_log_path()` falls back to `cwd/logs/claude-sessions/`, leaking NDJSON into the working tree on every run. Conflicts with issue #916 Decision #12.
2. `mcp-coder-utils` git URL has no commit-SHA pin — future installs may drift.
3. Defensive `str(...)` cast in test #2 around already-`str` `text_delta` payload — cosmetic.
4. Pre-existing `tests/cli/commands/test_prompt.py::test_continue_from_success` failing on `main`.
5. Pre-existing `src/mcp_coder/utils/tui_preparation.py:121` mypy `unreachable` warning.

**Decisions:**
- Finding 1: **ACCEPT** — matches issue Decision #12, real divergence from acceptance criteria.
- Finding 2: **SKIP** — user deliberately mirrored the unpinned form already used in `[tool.mcp-coder.install-from-github]`. Reproducibility tradeoff is accepted.
- Finding 3: **SKIP** — cosmetic only.
- Findings 4 & 5: **SKIP** — pre-existing on main, out of scope.

**Engineer escalation during fix:** `prompt_llm_stream` does not accept `logs_dir` and never threads one to `ask_claude_code_cli_stream` — the streaming path silently writes to `cwd/logs/claude-sessions/` regardless of caller intent. Latent bug that issue planning didn't anticipate. User chose **Option B**: have `prompt_llm_stream` derive `logs_dir` from `env_vars["MCP_CODER_PROJECT_DIR"]`, mirroring `prompt_llm`'s existing pattern.

**Changes implemented:**
- `src/mcp_coder/llm/interface.py` — `prompt_llm_stream` derives `logs_dir = Path(env_vars["MCP_CODER_PROJECT_DIR"]) / "logs"` for both Claude and Copilot streaming branches; passes through to `ask_claude_code_cli_stream` / `ask_copilot_cli_stream`. Public signature unchanged. Mirrors existing `prompt_llm` derivation.
- `tests/llm/providers/claude/test_claude_code_cli_streaming_integration.py` — wraps all 3 tests in `tempfile.TemporaryDirectory()`. Tests #1/#2 pass `logs_dir=tmp_logs_dir` directly to `ask_claude_code_cli_stream`. Test #3 passes `env_vars={"MCP_CODER_PROJECT_DIR": tmp_logs_dir}` to `prompt_llm_stream`.
- `tests/llm/test_interface.py` — mechanical mock-assertion update: added `logs_dir=None` to existing mocks of `ask_claude_code_cli_stream` / `ask_copilot_cli_stream` calls (consequence of new kwarg being passed by the production code).

**Quality checks:** format clean, pylint clean, pytest 3486 pass (only pre-existing `create_pr` collection error and the pre-existing `tui_preparation.py:121` mypy warning — both out of scope).

**Status:** committed as `842184a` (next round will run a fresh review).

## Round 2 — 2026-04-27

**Findings (from `/implementation_review` engineer):**
1. `_derive_logs_dir` helper would dedupe a 3-line snippet now repeated three times in `interface.py`. Engineer flagged as Skip-suggested.
2. `prompt_llm_stream`'s new `logs_dir` derivation has no parallel unit-test class. The existing `TestPromptLLMLogsDirDerivation` covers the non-streaming `prompt_llm` derivation (3 cases) but the new streaming derivation is only exercised by the live-CLI integration test, which is skipped in default CI.
3. Variable naming `tmp_logs_dir` for test #3 is mildly misleading (it's effectively `tmp_project_dir`); cosmetic.
4. Pre-existing issues unchanged (`tui_preparation.py:121` mypy unreachable, `tests/workflows/create_pr` collection error).

**Decisions:**
- Finding 1: **SKIP** — three lines, low refactor value, defer.
- Finding 2: **ACCEPT** — Round 1 added new production code and the existing convention in this file is a parallel unit-test class. Without unit tests the new derivation has no default-CI coverage.
- Findings 3 & 4: **SKIP**.

**Changes implemented:**
- `tests/llm/test_interface.py` — added `TestPromptLLMStreamLogsDirDerivation` class (3 tests mirroring `TestPromptLLMLogsDirDerivation`) covering env_vars with `MCP_CODER_PROJECT_DIR`, env_vars without it, and `env_vars=None`. Patches `ask_claude_code_cli_stream` and uses the file's established streaming-mock pattern (`iter([{"type": "done", "usage": {}}])` as `return_value`). ~78 lines added.

**Quality checks:** format clean (black auto-applied), pylint clean, pytest 93/93 in `test_interface.py`, mypy unchanged.

**Status:** committed as `4960fef` (next round will run a fresh review).

## Round 3 — 2026-04-27

**Findings (from `/implementation_review` engineer):**
1. `mcp-coder-utils` git URL has no commit-SHA pin — engineer flagged Skip (placeholder until upstream cuts a release).
2. `_derive_logs_dir` helper would dedupe a 3-line snippet — engineer flagged Skip (cosmetic, pattern was set in `prompt_llm` long before #916).
3. New `TestPromptLLMStreamLogsDirDerivation` covers only the Claude branch; Copilot streaming branch has no analogous test — engineer flagged Skip (issue is about Claude streaming).

**Decisions:**
- All findings: **SKIP** — engineer's own assessments are correct.

**Acceptance-criteria audit (all met):**
- mcp-coder-utils dependency pinned to git source containing the fix
- Renamed `test_claude_cli_stream_integration.py` → `..._logging_integration.py`
- 3 streaming integration tests, all using isolated `tempfile.TemporaryDirectory()` for `logs_dir`
- Continuity tests assert `session_id` equality + content reference (`"blue" in text.lower()`)
- iCoder smoke test asserts `text_delta` + `done` + `service.session_id` populated

**Quality checks:** pylint clean, pytest 3668 pass (only pre-existing `tui_preparation.py:121` mypy warning out of scope), mypy clean for #916 changes.

**Status:** zero changes — review loop terminates here.

## Final Status

**Rounds run:** 3 (1 review-only, 2 with changes accepted, 1 clean confirmation).

**Commits produced (newest first):**
- `4960fef` — Add unit tests for prompt_llm_stream logs_dir derivation (#916)
- `842184a` — Thread logs_dir through prompt_llm_stream from env_vars (#916)

**Final supervisor lint checks:**
- `run_vulture_check`: clean (no output)
- `run_lint_imports_check`: 22 contracts kept, 0 broken

**Net production-code change introduced by review:** ~12 lines in `src/mcp_coder/llm/interface.py` — `prompt_llm_stream` now derives `logs_dir` from `env_vars["MCP_CODER_PROJECT_DIR"]` for Claude and Copilot branches. Public signature unchanged. Mirrors the existing `prompt_llm` pattern. Fixes a latent bug (streaming path silently bypassed `MCP_CODER_PROJECT_DIR`).

**Verdict:** branch is ready for PR review.
