# Implementation Review Log — Issue #1041 (I2.1 Permission model + resolver)

Run 1 — started 2026-07-20. Supervised code review of the permission model +
resolver implementation against issue #1041 acceptance criteria, `summary.md`,
and `Decisions.md`.

## Round 1 — 2026-07-20

**Findings** (from `/implementation_review` engineer):
- Diff confirmed: real source implementation in `permissions/{__init__,model,matcher,resolver}.py` + tests + `.importlinter` + `vulture_whitelist.py`.
- Quality gates all green: pylint, mypy(strict), pytest 87/87 (full fast-unit 4342 pass / 2 skip), import-linter 20/20 (incl. `permissions_leaf_isolation`), vulture clean.
- No Critical findings.
- Accept-worthy (all confirmed correct-by-decision, not defects):
  - A1: degrade check precedes rule matching → `ASK` + `matched_rule=None`; `Degraded.layer` unset (intentional, S6).
  - A2: frame `allow` path runs a full config resolution to derive `lifted_never` (correct per Q3; acceptable at scale).
  - A3: value-set `{a,,b}` tolerantly yields `[a,b]` (parse-only in M2; arg eval is I5.4).
- Skip: sort-key negation `-ir[0]` readability; pylint-disable on `resolve` (per decision #9).
- Decisions.md adherence: all 8 checked points honored, no violations. Full AC coverage present and passing.

**Decisions**:
- A1/A2/A3 → Skip (correct by settled decision / out of M2 scope).
- Skip #2 (pylint-disable) → Skip (matches decision #9).
- Skip #1 (negated-index readability) → **Accept**: security-critical precedence code; add a one-line clarifying comment (bounded, zero-risk Boy Scout fix).

**Changes**:
- `resolver.py` `_resolve_config`: added a one-line comment explaining the `-ir[0]` negation (earlier declaration wins the final tie-break, so lower index must score higher under `max`). Comment-only; no behaviour change. pylint/mypy/pytest re-run green (4342 pass / 2 skip).

**Status**: committed (see commit agent).

## Round 2 — 2026-07-20

**Findings** (fresh `/implementation_review` engineer, post comment change `d353556`):
- Comment-only change verified clean, no regression; comment is accurate re: `max`/`-ir[0]` earliest-declaration tie-break.
- No new findings (no Critical / Accept-worthy / Skip). Precedence key, frame-first ordering, F4, Q3, and the `matched_rule` biconditional all re-confirmed; purity intact.
- pylint pass, mypy(strict) pass, pytest 87 permission tests pass (full fast-unit 4342 pass / 2 skip).

**Decisions**: nothing to accept — implementation confirmed ready.

**Changes**: none (loop exit condition met — zero code changes this round).

**Status**: no changes needed.

## Final Status

- **Rounds run**: 2 (round 1 → 1 accepted change; round 2 → zero changes, loop exit).
- **Code changes produced**: 1 commit — `d353556` "Document why declaration index is negated in permission tie-break" (comment-only clarification in `resolver.py`).
- **Supervisor gates (run directly)**: `run_vulture_check` → clean (no output); `run_lint_imports_check` → 20/20 contracts kept, incl. `iCoder Permissions Leaf Isolation`.
- **Quality gates**: pylint pass, mypy(strict) pass, pytest fast-unit 4342 pass / 2 skip, import-linter 20/20.
- **Acceptance criteria**: all AC rows covered by passing parametrized tests; all settled Decisions.md points honored (none violated).
- **Outcome**: implementation is clean, pure, well-tested, and matches the settled design. No blocking issues; ready to merge (pending CI/rebase check).
