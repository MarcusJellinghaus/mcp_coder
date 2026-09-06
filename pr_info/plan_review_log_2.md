# review-plan review log 2

Issue #1046 — I3.3 Reactive approval modal + scopes + persist write-back.

Run 1 (`plan_review_log_1.md`) ran 5 rounds and hit the round limit without converging; each
round found new failure-mode gaps in the same detailed pseudo-code. This run starts from the
plan as left by run 1 round 5.

## Round 1 — 2026-09-07

**Findings**:
- A — medium — `step_4.md:235/248/268`: every test row routed through `_reload` asserts
  `Policy.ALWAYS` after reload, but `resolver.py:191` returns `ALWAYS` from `Default()` whenever
  no rule matches, so the rows pass identically if `write_rule` wrote nothing. (Raised in run 1
  round 5; never applied.)
- B — medium — `step_3.md:153`: `test_session_grant_is_honoured_by_resolve` hand-builds
  `PermissionConfig` from the spied `Rule`, so `gateway.add_runtime_rule` — the store #1045 owns —
  is never exercised. (Raised in run 1 rounds 1, 2 and 5; never applied.)
- C — low — `step_4.md:127`: the `comma` rule never says where the root object body ends; on the
  `"{\n}\n"` skeleton the closing `}` is itself a code character, so a literal reading writes a
  trailing comma into a brand-new file. No test catches it — both scaffold tests parse through
  `_strip_jsonc`, which strips trailing commas. (Raised in run 1 rounds 3 and 5; never applied.)
- D — low — `step_3.md:108`: `_persist_target` recomputes the project dir that `app.py:83-87`
  already holds as `ICoderApp._project_dir` — the exact drift objection the plan itself raises to
  justify moving `action_cancel_stream`. (Raised in run 1 round 2; never applied.)
- E — low — `step_2.md:87` vs the issue AC: the AC demands the args widget text *equal*
  `_format_args(args)` **and** carry no truncation; `_format_args` truncates single-line values
  over 120 chars via `_render_value_full`, so both cannot hold.
- F — low — `step_3.md:5-8`: after step 3 the modal advertises the persist write while choice `3`
  only writes the runtime rule — a one-commit intermediate state, disclosed by the plan.
- Structural — the plan is ~1333 lines of markdown for ~380 lines of production code;
  `step_4.md` alone was ~322 lines for a ~180-line module. All six "high" findings across run 1's
  five rounds were edge cases inside that pseudo-code, not planning defects. Prose pseudo-code is
  reviewable but not runnable, so review had no termination condition — this is why run 1 did not
  converge.

**Decisions**:
- A, B, C, D — accepted, applied via `/plan_update`. All four had already been raised in run 1 and
  dropped without being applied; none changes the intended implementation.
- Structural — accepted. `step_4.md`'s six pseudo-code bodies replaced by six numbered invariants,
  with every guard rounds 1–5 added preserved as a stated requirement; the 19-row test table is
  the specification. `step_5.md`'s three-paragraph `except OSError` justification cut to one
  sentence.
- F — skipped. Correctly disclosed single-commit intermediate state inside one PR.
- Modal test placement — left as the issue decided (`tests/icoder/test_app_pilot.py`, already on
  `.large-files-allowlist`). Splitting ~21 pilot tests into a new file would reverse a settled
  decision for no defect.
- E, and the #1154 scope questions — escalated to the user (see below).

**User decisions**: pending — two questions asked:
1. Should step 1's commit amend **#1154's body** (not just comment) so it stops describing a sort
   key that no longer matches HEAD; and is the narrow `personal_bit` the final answer or a stopgap?
2. Should #1046's full-args AC be amended to "contains every argument value verbatim, with no
   truncation or ellipsis", since the current wording is self-contradictory?

**Changes**: `step_3.md` (findings B, D), `step_4.md` (findings A, C + compression, ~322 → 223
lines), `step_5.md` (compression, `_persist_target` form), new `steps/Decisions.md`.

**Status**: committed.
