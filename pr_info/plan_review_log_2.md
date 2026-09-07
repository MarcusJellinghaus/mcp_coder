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

## Round 2 — 2026-09-07

**Verification** (of round 1's changes and the two issue edits):
- Round-1 findings A–D confirmed present in the plan text, checked against HEAD
  (`app_core.py:73` accepts `permission_gateway=`, `gateway.py:107/128` rebinds `_config`,
  `app.py:85-89` computes `self._project_dir`).
- **No guard was lost in the `step_4.md` compression.** Each of the five guard families
  accumulated over run 1 maps to a surviving invariant plus a test row; the deleted `comma` rule
  is now pinned by the plain-`json.loads` assertion instead of by prose.
- No `#1154` residue: `summary.md` and `step_1.md` agree with the rescoped issue.
- The reworded full-args AC is reflected in `step_2.md` and `step_5.md`.

**Findings**:
- F1 — low — `step_1.md:76-88`: the list of prose sites to restate for the 4-key → 6-key change
  misses `resolver.py:142` (the `_resolve_config` docstring) and `resolver.py:180` (the R14 bound
  comment), so merged code would still describe a key that no longer exists. #1154's own
  "Consequential edits" list names the first of these.
- F2 — low — `step_4.md:152`: `test_no_temp_file_is_left_behind` asserts `.icoder/` holds no
  `*.tmp` file, but the specified `tempfile.mkstemp(dir=target.parent)` uses an empty suffix and a
  `tmp` *prefix*, so the glob can never match and the row passes whether or not a temp file leaks.
- F3 — low — `summary.md:33`: the heading "Resolver precedence: layer moves above policy rank"
  asserts exactly what `step_1.md:72-74` forbids stating, and is contradicted by `summary.md:44`.
- Follow-on (found while fixing) — `summary.md` and `step_1.md`'s WHERE row disagreed with
  `step_1.md`'s TDD table on the resolver test counts.

**Decisions**: F1, F2, F3 all accepted and applied — one-line edits, none changes the design; F2
in particular was an unfalsifiable assertion. The count mismatch was folded into the same round
rather than deferred. Five items were explicitly considered and skipped as speculative or
implementer detail (recorded in the review report).

**User decisions**: none outstanding. The two questions raised in round 1 were answered and
applied:
1. **#1154 rescoped on GitHub** to the narrow `local`/`runtime`-over-authored precedence fix
   (new title: "I2.5 — Cross-layer precedence: a local/runtime rule must win over an authored ask
   at equal specificity"), with a **Won't fix** section recording that a `user` `ask` still beats
   a `project` `allow` at equal specificity — a repo-committed `"allow"` must not silently
   override the user's global `"ask"`. `personal_bit` is the final semantic, not a stopgap, so
   step 1 delivers #1154 in full and closes it.
2. **#1046's full-args AC reworded** from the unsatisfiable "equals `_format_args(args)` in full"
   to "contains every argument value verbatim", since `_format_args` truncates single-line values
   over 120 chars.

**Changes**: `step_1.md` (F1, WHERE-row count), `step_4.md` (F2), `summary.md` (F3, count),
`Decisions.md` (decisions 8–11).

**Status**: committed.

## Round 3 — 2026-09-07

**Findings**: none.

Round-2's three corrections were verified against HEAD rather than against the log: `step_1.md`'s
five `resolver.py` prose sites all resolve to exact lines (`:9`, `:46`, `:142`, `:166`, `:180`)
plus the test module docstring, and its counts now agree across the WHERE row, the 7-row TDD
table, the notes section, Acceptance and the LLM prompt; `step_4.md`'s
`test_no_temp_file_is_left_behind` asserts `.icoder/` holds exactly `settings.local.json`;
`summary.md`'s heading and Files-modified rows match `step_1.md`.

Other anchors spot-checked and correct: `app.py:82-86`/`:222-233` (the `action_cancel_stream`
"pure move" claim holds — it touches only `_cancel_event` and `_core`), `loader.py:214/216`,
`test_app_pilot.py:1609/1766`, `test_approval_wiring.py:384`,
`test_permissions_loader_layers.py:459`. Every #1046 acceptance criterion maps to at least one
named test; no new dependencies are implied.

**Decisions**: nothing to apply.

**User decisions**: none outstanding.

**Changes**: none.

**Status**: no changes needed.

---

## Final Status

**Plan is ready for approval.** Three rounds; rounds 1 and 2 produced changes, round 3 produced
none, which is what ended the loop.

**Commits produced**
| SHA | Subject |
|---|---|
| `264e0c5` | `docs(pr_info): make persist tests falsifiable and trim step_4 pseudo-code` |
| `01acf1a` | `docs(pr_info): rescope #1154 into step 1 and pin the reworded full-args AC` |
| `5f08bdc` | `docs(pr_info): apply plan review round 2 corrections` |

**Why run 1 did not converge, and what changed.** Run 1's five rounds all found edge cases inside
`step_4.md`/`step_5.md` prose pseudo-code rather than planning defects. Prose pseudo-code is
reviewable but not runnable, so review had no termination condition, and each round's fix enlarged
the surface for the next. Run 2 round 1 compressed `step_4.md` from ~322 to 223 lines — the six
pseudo-code bodies became six numbered invariants, every accumulated guard preserved as a stated
requirement, with the 19-row test table left as the real specification. Review converged in two
further rounds.

Run 2 also applied four findings that run 1 had raised and dropped without applying (two of which
left named tests unfalsifiable), and settled the two questions run 1 escalated.

**Issue edits made during this run**
- **#1154** rescoped and retitled to *"I2.5 — Cross-layer precedence: a local/runtime rule must win
  over an authored ask at equal specificity"*, with its sort key, AC1 and test list aligned to the
  narrow `personal_bit`, and a new **Won't fix** section recording that a `user` `ask` still beats a
  `project` `allow` at equal specificity — a repo-committed `"allow"` must not silently override the
  user's global `"ask"`. `personal_bit` is final, not a stopgap; step 1 delivers #1154 in full and
  closes it.
- **#1046**'s full-args acceptance criterion reworded from the unsatisfiable "the args widget's
  text equals `_format_args(args)` in full" to "contains every argument value verbatim"
  (`_format_args` truncates single-line values over 120 chars via `_render_value_full`).

**Left for the human at merge time.** #1154's "Consequential edits elsewhere" also asks for a
precedence-bullet update in design ref #1037 §5 and a sub-issue-table row in epic #1038. These are
issue-text edits, not code, and are not among #1154's acceptance criteria, so the plan correctly
omits them — but step 1's commit closes #1154, so they want doing by hand.

**Unrelated:** CI on this branch is red from a pre-existing dependency mismatch on `main`
(`run_mypy_check() got an unexpected keyword argument 'strict'`, 4 failures in
`tests/test_mcp_tools_py_integration.py`). Nothing on this branch touches source code.

---

## Addendum — 2026-09-07 (after the run closed)

**The #1154 rescope recorded above was reverted.** The rounds above are left as written — they
record what was decided at the time — but two of their conclusions no longer hold:

- Round 2's "**#1154 rescoped on GitHub** … step 1 delivers #1154 in full and closes it" is
  **superseded**. #1154 has been restored to its original text (the wider `_LAYER_ORDER` hoist
  proposal) and **stays open**. Step 1 partially addresses it and its commit carries `Refs #1154`,
  never a closing keyword.
- The Final Status entry "Left for the human at merge time", which was premised on step 1 closing
  #1154, no longer applies in that form. #1154 remains open and carries its own consequential-edits
  list.

**Why.** The rescope settled a design question that is the maintainer's to make — whether a `user`
`ask` should keep beating a `project` `allow` at equal specificity, and whether layer order should
outrank policy rank in general. #1046 needs neither answered: step 1's narrow `personal_bit` is
sufficient for the persist scope on its own. The rescope also ran under the maintainer's GitHub
credentials, so the issue's edit history attributed reasoning to him that was not his.

**What the research found** (gathered after the run, from #1037/#1038 rather than from #1046's
restatements of them):

- #1037 §5 states the order as specificity → `deny`/`never` > `ask` > `allow` → layer order, i.e.
  **policy rank sits above layer order**. `tests/icoder/test_permissions_resolver.py:612` already
  pins the `user`↔`project` pair at HEAD. So the *original* wide hoist would have contradicted §5
  and silently flipped a passing test — but the "won't fix" rationale offered for the narrow fix
  (that a repo-committed config must not override a user-global setting) **is not in the design**.
  #1037 and #1038 describe no trust asymmetry between `user` and `project`; §8.2's committed/personal
  split governs *write targets* only, and §10.1 F2 prefers project scoping where it compares.
- **Both variants deviate from §5** — the narrow one still lifts a layer-derived bit above
  `Policy.rank` for `local`/`runtime`. Amending §5's precedence bullet is therefore required either
  way; it is tracked on #1154 and is *not* done by #1046. A comment on #1037 now records the
  deviation, which is the second of its kind (#1045's R14 already overrides §5 for `runtime`).

**Code impact: none.** Step 1 still implements
`(specificity, never_bit, personal_bit, policy.rank, layer, -index)`. Only the issue-tracking
framing changed. The plan remains ready to implement.
