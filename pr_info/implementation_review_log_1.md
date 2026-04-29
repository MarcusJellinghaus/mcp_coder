# Implementation Review Log #1 — Issue 928

Branch: `928-verify-globalise-truststore-so-non-langchain-http-works-on-corporate-networks-surface-github-token-source`
Started: 2026-04-29

This log records each review round: findings from the review subagent, supervisor
triage decisions (accept/skip with reason), changes implemented, and commit status.


## Round 1 — 2026-04-29

**Findings (from review subagent):**
- Critical: none.
- Suggested:
  1. `pyproject.toml:62` — `[langchain-base]` comment lists "SSL" but `truststore` was promoted out of this extra into core deps.
  2. `tests/cli/test_main.py:304-313` — new test `test_main_calls_ensure_truststore` doesn't mock `setup_logging` / `create_parser` like its sibling tests in the same class.
  3. `tests/utils/test_ssl_setup.py:38-43` — `test_noop_when_truststore_not_installed` relies on CPython's `sys.modules[name] = None` import-blocking sentinel; could be more explicit.
- Cosmetic:
  4. `src/mcp_coder/utils/ssl_setup.py:21` — reviewer believed `# noqa: PLW0603` and `# pylint: disable=global-statement` were redundant.
  5. `.importlinter:259-262` — informational note about rationale comment.

**Decisions:**
- (1) **Accept** — Boy Scout fix; the comment is now factually wrong.
- (2) **Skip** — working test, cosmetic; "Don't change working code for cosmetic reasons when it's already readable."
- (3) **Skip** — speculative; "If a change only matters when someone makes a future mistake, it's speculative."
- (4) **Skip** — reviewer's analysis is wrong: `# noqa` only suppresses ruff, `# pylint: disable` only suppresses pylint. Both directives are needed for the project's two linters.
- (5) **Skip** — reviewer flagged informationally; no fix needed.

**Changes:**
- `pyproject.toml:62` — dropped `, SSL` from the `[langchain-base]` comment.

**Status:** committed (`48eb4c9`); pushed.


## Round 2 — 2026-04-29

**Findings (from review subagent):**
- Critical: none.
- Suggested: none.
- Cosmetic: none.

**Decisions:** N/A — no findings.

**Changes:** none from review.

**Status:** zero code changes from review → exit review loop.

---

## Vulture / lint-imports sweep — 2026-04-29

**lint-imports:** 23/23 contracts kept (including new `Truststore Isolation`).

**Vulture:** one false positive: `tests/utils/test_ssl_setup.py:16 unused function '_reset_injected' (60% confidence)`. The fixture is `autouse=True` and required by Decision 8 in the issue. Project convention for silencing such fixture false positives lives in `vulture_whitelist.py` (e.g. `_._isolate_crash_logging_state` is whitelisted there).

**Fix:**
- Updated `_reset_injected` to use `Generator[None, None, None]` with `yield` and symmetric pre/post reset, matching the `_isolate_crash_logging_state` pattern in `tests/utils/test_crash_logging.py`.
- Added `_._reset_injected` to `vulture_whitelist.py` alongside the analogous existing autouse-fixture entry.

Vulture re-run: clean.

**Status:** committed (`c811699`); pushed.

---

## Final Status

- Rounds run: 2 (round 2 produced zero findings → exited loop).
- Commits produced this review:
  - `48eb4c9` — Drop stale SSL note from langchain-base extra comment
  - `c811699` — Silence vulture false positive for _reset_injected fixture
- Quality checks at end of review:
  - `lint-imports`: 23/23 contracts kept.
  - `vulture`: clean.
  - `mypy`: 1 pre-existing unreachable warning at `src/mcp_coder/utils/tui_preparation.py:121`. Out of scope (file last modified by PRs predating this branch).
  - `pytest` (scoped to changed surfaces): all green; the `mcp__tools-py__run_pytest_check` wrapper has an unrelated "Internal pytest error" issue when invoked without an explicit path argument — verified by scoped runs.
  - `pylint`: not available in venv (tooling/wrapper issue, not a code regression).
- Outstanding issues: none for the implementation. All 11 acceptance criteria from issue #928 are met.
