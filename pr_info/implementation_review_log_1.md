# Implementation Review Log — Run 1

**Issue:** #1040 — I1.2 Self-invocation guard (`disable-model-invocation`)
**Branch:** `1040-i1-2-self-invocation-guard-disable-model-invocation`
**Nature:** verify + lock-in + document (no new production behaviour)

Review rounds are appended below.

## Round 1 — 2026-07-17

**Findings** (from `/implementation_review`):
- #1 AC3 primary single-dispatch-call-site test is sound; regex `\.dispatch\(` excludes the `def dispatch` definition and unrelated `dispatch_workflow`. (positive)
- #2 Source-search regexes are line-based/literal-token — a future second dispatch via alias/`getattr`/line-split would evade them (false-negative surface). Optional hardening.
- #3 AC4 `InputSubmitted(` test loose but docstring honest; assertion correct. (positive)
- #4 AC2 pilot test drives real `_handle_stream_event`, spies `registry.dispatch`, asserts not-called + rendered once. (positive)
- #5 AC1 behavioural test proves human path dispatches and expands `$ARGUMENTS`. (positive)
- #6 AC5 test asserts observable outcome (command absent from registry). (positive)
- #7 AC6 doc-notes accurate; warn against a naive runtime reader. (positive)
- #8 AC7 marker comments present and precise. (positive)
- Minor: git diff showed mojibake em-dashes (`â€”`) in committed docstrings/comments.
- Full fast suite green: 4255 passed, 2 skipped.

**Decisions**:
- #2 — **Accept** (optional hardening). A security-invariant test should be explicit about its limits to avoid false confidence. Bounded, zero-risk docstring caveat.
- Mojibake — **Accept as investigate-and-fix**. Garbled bytes in production comments would be a real defect; required confirmation.
- #1, #3–#8 — positive confirmations, no action.

**Changes**:
- Investigated mojibake: raw-byte inspection showed all em-dashes are proper UTF-8 `e2 80 94`; zero `â€”` sequences. Diff-rendering artifact only — **no source change**.
- Added scope caveat to the module docstring of `tests/icoder/test_self_invocation_guard.py` noting the guards match direct call syntax only and that alias/`getattr`/line-split indirection is out of scope (realistic direct-call threat is caught).
- Quality checks: pylint clean, mypy clean, pytest 4255 passed / 2 skipped. format_code no-op.

**Status**: committed (see commit for the caveat).

## Round 2 — 2026-07-17 (confirmation pass)

**Findings**: Confirmation pass after the Round 1 caveat commit. All AC1–AC7 re-verified against the live tree: single `.dispatch(` call site in `app_core.py` (marker comment does not create a false hit); `InputSubmitted(` only in `input_area.py`; human-path/model-path behavioural tests pass; `user-invocable: false` absent from registry; doc-notes/markers accurate. The Round 1 scope-caveat addition is truthful and well-bounded (no overclaim). One informational note: the pilot test carries `textual_integration` so it's excluded from the fast set, but passes when run explicitly and the load-bearing guarantee lives in the non-marked source-search test — coverage intact.

**Decisions**: No actionable findings. No Critical issues.

**Changes**: None.

**Status**: no changes needed — review loop complete.

## Final Status

- **Rounds run**: 2 (Round 1 accepted one bounded doc-caveat change; Round 2 confirmation pass produced zero code changes → loop complete).
- **Code changes this run**: 1 commit — `5c262d1` docstring scope caveat in `tests/icoder/test_self_invocation_guard.py`.
- **Quality gates**: pylint clean, mypy clean, pytest 4255 passed / 2 skipped, format_code no-op.
- **Supervisor checks**: `run_vulture_check` — no output (clean). `run_lint_imports_check` — PASSED, 19 contracts kept / 0 broken.
- **Outcome**: All acceptance criteria AC1–AC7 verified against the live tree. Implementation is a documentation-only "verify + lock-in + document" change; the security boundary is now explicit, tested, and documented. No open review issues.
