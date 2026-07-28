# Implementation Review Log — Issue #1042 (I2.2)

Feature: Config `.icoder/` JSONC reader + layered discovery + schema.

Supervisor-driven code review of the implementation on branch
`1042-i2-2-config-icoder-jsonc-reader-layered-discovery-schema`.

---

## Round 1 — 2026-07-28

**Findings** (from `/implementation_review`; all gates green: pylint, mypy strict, ruff, lint-imports, pytest 781/781 in `tests/icoder/`):
- Real implementation diff confirmed (`loader.py` + tests + `pyproject.toml` + `.importlinter` + `__init__.py`).
- Fail-closed, JSONC stripper, `@ref`, provenance, schema emission, discovery, merge — all verified against ACs.
- **F1 (Accept):** `_load_layer` per-layer guard catches only `(OSError, json.JSONDecodeError)`; an unexpected raise from `jsonschema`/`parse_matcher` would propagate and abort startup — contrary to the fail-closed contract ("only hard-raise is inability to construct a config object").
- **F2 (Accept):** `@ref` detection uses `token.startswith("@")` on the raw token; a member like `" @git"` (leading whitespace) would miss the specific I4.1 diagnostic and get the generic "malformed matcher" message — violates the AC ("never a generic 'malformed matcher'").
- **F3 (Skip):** `summary.md` names one test file that was split into `_layers`/`_schema`. Doc-only; `pr_info/` is background and deleted later.

**Decisions**:
- F1 → Accept. Security startup path; broaden per-layer catch to degrade-on-any-exception.
- F2 → Accept. One-line `.strip()` upholds an explicit AC; trivial/low-risk.
- F3 → Skip. `pr_info/` doc-only, out of scope.

**Changes**:
- `loader.py`: added a broad `except Exception` fallback in `_load_layer` that converts any unexpected error into a per-layer degrade (empty `_LayerResult` + recorded error), with a scoped `# pylint: disable=broad-exception-caught` + WHY comment. Changed `@ref` check to `token.strip().startswith("@")`.
- `tests/icoder/test_permissions_loader_layers.py`: +3 tests (leading-whitespace `@ref` → specific I4.1 message at load and unit level; unexpected exception during layer load degrades not raises).
- Gates after fixes: pylint / mypy / ruff / pytest all PASS (full unit suite 4766 passed, 2 skipped).

**Status**: implemented; pending commit.

## Round 2 — 2026-07-28

**Findings**: Focused follow-up verifying the round-1 hardening fixes.
- Fix 1 (broad `except Exception` per-layer degrade) — correct: separate from the file-read `(OSError, json.JSONDecodeError)` block (no double-handling / message masking); returns empty `_LayerResult` with recorded error → `degraded=True`; `return`s live inside the `try` but don't raise so the good path is untouched; `except Exception` (not `BaseException`) so `KeyboardInterrupt`/`SystemExit` propagate.
- Fix 2 (`token.strip().startswith("@")`) — correct: `" @git"` routes to the specific I4.1 diagnostic; valid `mcp__…` tokens and the empty case unchanged (original token still passed to `parse_matcher`).
- 3 new tests are sound and minimally mocked.
- **No new issues** (zero Critical/Accept/Skip).

**Decisions**: Nothing to act on.

**Changes**: None (review-only round).

**Status**: No code changes — review loop complete. Gates: pylint / mypy / ruff / lint-imports / pytest all PASS (4766 passed, 2 skipped).

---

## Final Status — 2026-07-28

- **Rounds run:** 2. Round 1 accepted 2 hardening fixes (fail-closed broad per-layer degrade; whitespace-tolerant `@ref` diagnostic); round 2 confirmed them correct with zero new issues → loop complete.
- **Commits produced (code):** `20f6fb0` — *Harden loader fail-closed: broad per-layer degrade + whitespace-tolerant @ref detection*.
- **Supervisor final gates:**
  - vulture — clean (no output).
  - lint-imports — 21 contracts kept, 0 broken (incl. new `iCoder Permissions Core Purity`).
  - (via engineer) pylint / mypy strict / ruff / pytest — all PASS (4766 passed, 2 skipped).
- **Acceptance criteria:** all verified against the implementation across rounds 1–2.
- **Outcome:** Implementation review complete. No open issues; ready for PR/CI verification.
