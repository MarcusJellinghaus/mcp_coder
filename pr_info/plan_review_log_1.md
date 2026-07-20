# Plan Review Log — Issue #1041 (I2.1 Permission model + resolver)

Run 1 — supervised plan review. Base branch: main. Started 2026-07-20.

Plan state at start: 4 steps in `pr_info/steps/`, TASK_TRACKER empty (nothing implemented yet).

---

## Round 1 — 2026-07-20

**Findings** (from `/plan_review` engineer):
- C1 (Critical): Step 2 lacks a test that `matches()` does NOT evaluate the arg predicate (parse-only M2 invariant) — a `Matcher` with an arg predicate must still match the bare tool name.
- C2 (Critical): `matched_rule is None` biconditional not explicitly asserted for **frame-sourced** decisions (Step 4).
- S1: No explicit test for exact-tool vs server-wildcard ordering (§8.3 manager primary-key case).
- S2: Model docstring encodes resolver semantics (`default_policy None -> ALWAYS`); move note to resolver to keep `model.py` pure-data.
- S3: Step pytest marker-exclusion list is incomplete vs. CLAUDE.md canonical set.
- S4: `__init__` export of matcher helpers marked "(optional)" — make deterministic (export `parse_matcher`, keep `specificity`/`matches` internal).
- S5: Step 3 leaves `frame` param unread; verify `run_vulture_check` green at the Step-3 commit.
- S6: `Degraded.layer` is structurally unfillable in I2.1 — document it stays `None` in M2 (populated by I2.2).
- S7: New import-linter contract re-lists third-party modules already globally forbidden (redundant but harmless).
- Q1: `lifted_never` typed `Policy | None` — matches design ("base policy that was lifted").
- Q2: Frame ask->always elevation records no signal (only never-lift) — matches decision #4.
- Q3: Under degraded config a frame `allow` reports `lifted_never=None` (degrade masks base) — subtle; wants a test + comment.
- Q4: No new dependencies / `pyproject.toml` / mypy changes — confirmed correct.
- Coverage: all acceptance criteria otherwise mapped to steps; sizing appropriate (Step 4 largest but cohesive — keep).

**Decisions**:
- ACCEPT & apply (straightforward, within settled design): C1, C2, S1, S2, S3, S4, S5, S6, Q3.
- SKIP: S7 (harmless redundancy; keep explicit leaf contract for clarity). Q1 (settled by design — `lifted_never` = base `Policy`). Q2 (recording ask->always is I4.3 scope; decision #4 keeps `lifted_never` = never-only). Q4 (confirmation only).
- No user escalation: no finding affects scope or architecture; all resolved by settled decisions in #1037/#1041 or are test/doc improvements.

**User decisions**: none required this round.

**Changes applied** (via `/plan_update`): all 9 accepted items landed, plus a new `pr_info/steps/Decisions.md` decision log.
- C1 (step_2): test — `Matcher` with arg predicate still matches bare tool name.
- C2 (step_4): explicit `matched_rule is None` on all frame-sourced tests.
- S1 (step_2): test — exact-tool `(0,1,1)` outranks server-wildcard `(0,0,1)`.
- S2 (step_1+3): moved `default_policy None -> ALWAYS` note to resolver; `model.py` stays pure-data.
- S3 (steps 1-4): CHECKS cite full canonical 10-marker fast-unit set with `-n auto`.
- S4 (step_2): `parse_matcher` exported from `__init__`; `specificity`/`matches` internal; "(optional)" removed.
- S5 (step_3): Step-3 commit must be vulture-green; whitelist unread `frame` if flagged.
- S6 (step_1): documented `Degraded.layer` stays `None` in I2.1.
- Q3 (step_4): test row + `_resolve_frame` comment — frame `allow` under degraded config reports `lifted_never is None`.
Files changed: `step_1.md`, `step_2.md`, `step_3.md`, `step_4.md`, `Decisions.md` (new).

**Status**: plan changed this round -> committing, then looping to a fresh review round (Round 2).

---

## Round 2 — 2026-07-20

Committed round 1 as `d304b75` (pushed). Fresh review engineer ran `/plan_review` again.

**Findings**:
- Verification: all 9 round-1 edits present, internally consistent, no contradictions introduced. Marker lists (all 10) typo-free; specificity tuples consistent; `matched_rule` biconditional coherent; every AC row maps to a test; step sizing sound. No Critical issues.
- #1 (optional): Step 1 could also assert the `matched_rule is None` biconditional at pure-model level — but it's behaviorally covered in Steps 3-4 and the model has no logic enforcing it.
- #2 (straightforward): Step 1 TESTS include a blanket "instances are hashable" bullet, but `PermissionConfig` carries `dict`-valued `groups`/`scenarios` fields — a frozen dataclass with `dict` fields raises at `hash()`. If the assertion is read as covering `PermissionConfig`, `/implement` would write a self-contradictory test.
- #3 (settled): frame-path has no `Rule`, so `matched_rule=None` needs no origin test — consistent with §10.3 DC2. No change.

**Decisions**:
- ACCEPT & apply: #2 — scope the Step 1 hashability assertion to the genuinely-hashable value types; explicitly note `PermissionConfig` (dict-valued fields) is not required to be hashable.
- SKIP: #1 (optional, already behaviorally covered), #3 (settled).
- No user escalation: fix is a plan-text clarification within settled design.

**User decisions**: none required.

**Changes applied** (via `/plan_update`): #2 — scoped Step 1's hashability test to genuinely-hashable value types (`Policy`, `Matcher`, `Rule`, `Decision`, `Source` members); explicitly excluded `PermissionConfig` (dict-valued `groups`/`scenarios` -> `hash()` raises); corrected the "Frozen, hashable dataclasses" blanket wording; logged as R2-H1 in `Decisions.md`. Files changed: `step_1.md`, `Decisions.md`.

**Status**: plan changed this round -> committing, then looping to Round 3.
