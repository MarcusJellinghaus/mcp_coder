# Plan Review Log — Issue #713

Coordinator template watchdog + `set-status --from-status` for silent-death recovery.

## Round 1 — 2026-04-07

**Findings**:
- Step 1 returns `(True, None)` on skip → caller would emit misleading "Updated" log (must fix)
- `--from-status` without positional `status_label` not rejected by argparse `nargs="?"` (must fix + test)
- "all three" → "all five" code-quality checks in both LLM prompts
- Stale "after Step 2" forward-reference in step_1 ALGORITHM
- Single-status-label invariant assumption not noted in ALGORITHM
- `--from-status` validation source ambiguous (project vs bundled labels.json)
- `--force` + skip-path interaction undocumented/untested
- Step 2 placeholder test passes all kwargs to all templates — should parameterize per-template
- Step 2 missing test for required inline recovery-matrix comment block
- Commit messages should use `feat(scope):` form to match repo convention

**Decisions**:
- Skip-log fix, argparse-error fix, "all five" prompt fix, ALGORITHM clarifications, single-status note, parameterized placeholder test, comment-block test, commit scope tags → **accept (straightforward)**
- Validation source + `--force`/skip interaction → **ask user**
- Windows "not hardened" test, `Decisions.md` file, param ordering note, `PRIORITY_ORDER` note → **skip (NIT)**

**User decisions**:
- Q: `--from-status` validation source → **Project labels.json** (consistent with positional)
- Q: `--force` + skip interaction → **Inline comment + dedicated test**

**Changes**:
- `step_1.md`: 3-tuple return surfaces skip state; argparse-style validation for `--from-status` w/o positional; `feat(set-status):` scope; "all five" prompt; clarified precondition placement; project-config validation made explicit; added inline-comment rationale for force/skip; 3 new tests added; success-path tests flagged for return-shape update
- `step_2.md`: parameterized per-template placeholder test; new `test_recovery_matrix_comment_present`; `feat(coordinator):` scope; "all five" prompt
- `summary.md`: unchanged (scope unchanged)

**Status**: changes applied to `step_1.md` and `step_2.md`; committed (946a5d1)

## Round 2 — 2026-04-07

**Findings**:
- BLOCKER: `parser.error(...)` pseudocode unreachable from `execute_set_status(args)` — no `parser` in scope
- Dirty-wd check runs before `_update_issue_labels` — invariant should be documented (callers need `--force`)
- Skip-message f-string implied but not inlined in ALGORITHM — LLM could render `None` instead of `<none>`
- Step 2: Windows has no `|| true` analog — safe because RC captured before watchdog, but worth a one-line note
- Step 2 test #10 wording "or equivalent" should be tightened to exact strings
- summary.md doesn't mention 3-tuple return shape change
- Round-1 changes all verified present and correct; acceptance criteria fully covered

**Decisions**: All findings accepted as straightforward; no user input needed.

**Changes**:
- `step_1.md`: replaced `parser.error` with `logger.error` + `return 2`; added INVARIANTS section for dirty-wd ordering; inlined skip-message f-string with `<none>` sentinel; tightened test #8 to assert exit code 2 via caplog
- `step_2.md`: Windows RC-safety note; tightened test #10 to exact strings; added KeyError rationale to test #9
- `summary.md`: noted return-shape change for `set_status.py`
- `Decisions.md`: created (engineer logged round-2 decisions)

**Status**: changes applied; committed (65c0419)

## Round 3 — 2026-04-07

**Findings**: No substantive issues. All round-2 fixes verified present and correct. One NIT (variable-name drift between DATA and ALGORITHM pseudocode in step_1 — cosmetic only, both render identically).

**Decisions**: NIT skipped — not load-bearing.

**Changes**: None.

**Status**: no plan changes — review loop terminates.

## Final Status

**Plan ready for implementation.** Three review rounds; rounds 1–2 produced commits 946a5d1 and 65c0419; round 3 was clean. Plan now covers all 14 issue decisions and acceptance criteria items, with explicit invariants, exact-string test assertions, and a 3-tuple return shape that surfaces the skip path to callers without misleading log output.
