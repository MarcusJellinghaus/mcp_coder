# Implementation Review Log — Run 1

**Issue**: #1112 — implement workflow: a blocked agent can only spin or fabricate
**Branch**: `1112-implement-workflow-a-blocked-agent-can-only-spin-or-fabricate`
**Started**: 2026-08-23

Supervised code review of the blocked-channel implementation (Steps 1–8).

---

## Round 1 — 2026-08-23

**Diff confirmed**: 8 source files, 10 test files, 3 docs files. Not plan-only.

**Invariant verification** — all six from `summary.md` hold, in source and pinned by tests:

| # | Invariant | Source | Test |
|---|-----------|--------|------|
| 1 | marker + changed files → blocked | three-way branch precedes the Step 6 `get_full_status` | `test_blocked_wins_over_changed_files` |
| 2 | empty marker → blocked, not `no_changes` | `read_and_clear_blocked` returns fallback, never `None` | `test_empty_marker_is_blocked_not_no_changes` |
| 3 | marker + `LLMTimeoutError` → `timeout` + detail | `llm_error` checked first; `append_detail` in `core.py` | `test_marker_plus_timeout_keeps_timeout_label` |
| 4 | stale marker cleared at task start | `task_processing.py` start-of-task cleanup | `test_stale_marker_removed_at_task_start` |
| 5 | blocked never retries | `process_task_with_retry` loops only on `no_changes` | `test_blocked_does_not_retry` |
| 6 | deleted before finalisation stages | `finally` scoped to the `prompt_llm` call only | `test_blocked_marker_removed_on_empty_response` |

All three in-scope commit paths carry cleanup. CI-fix loop correctly left alone per `summary.md` §5.

**Findings**:

1. *(Should-fix)* `read_and_clear_blocked` can raise `UnicodeDecodeError` — a `ValueError`, so not caught by its `except OSError`. Called from three `finally` blocks; escaping there replaces the in-flight LLM failure and loses the reason. Contradicts its own "Never raises" docstring.
2. *(Nice-to-have)* Blocked reason logged three times (helper WARNING, `task_processing` ERROR, `core` ERROR).
3. *(Nice-to-have)* `prompts.md:107` — `All sub-tasks must be [x] before finishing` is still unconditional, a few lines from the new blocked bullet.
4. *(Nice-to-have)* Marker text reaches the GitHub comment with internal newlines intact; a stray fence swallows the `### Uncommitted Changes` block.
5. *(Nice-to-have)* `get_diff_stat` uses `git diff HEAD --stat`, which excludes untracked files.
6. *(Nice-to-have)* `github_Issue_Workflow_Matrix.html` at 746 lines vs the 750-line gate, not allowlisted.
7. *(Nice-to-have)* `TaskOutcome` not exported from `implement/__init__.py` though `process_single_task` is.

**Decisions**:

- **1 — Accept.** Genuine correctness bug defeating the issue's core guarantee. One-word fix (`errors="replace"`).
- **2 — Accept.** The `task_processing` log is the redundant one; the other two are each load-bearing (helper covers the cleanup call sites, `core`'s unconditional ERROR is required by issue §1).
- **3 — Accept.** Not cosmetic. The issue's thesis is that an unconditional imperative next to the blocked exit drives fabrication, and §3 requires conditioning rules in place rather than leaving a contradiction standing. Same shape as the `:115` bullet the issue already fixed.
- **4 — Accept.** Bounded, and it protects the readability of the failure comment that is the whole deliverable. Collapsing whitespace also stretches the 500-char budget.
- **5 — Skip.** Pre-existing in `workflow_utils/failure_handling.py`; changing it alters every workflow's failure comment. Out of scope per the knowledge base's pre-existing-issues rule.
- **6 — Skip.** Passes the gate today. Weakening a size gate against hypothetical future growth is speculative.
- **7 — Skip.** The issue explicitly scoped `implement/__init__.py` as "export names only, no change". YAGNI without a real consumer.

**Changes**: findings 1–4 implemented (see next round for verification).
**Status**: pending commit.

Committed as `495e1d6` — "Harden blocked-marker read and drop residual fabricate pressure" (3 files, +70/-7). Pushed fast-forward.

Branch status after commit: CI=PASSED, Rebase=UP_TO_DATE, Tasks=COMPLETE.

---

## Round 2 — 2026-08-23

Reviewed commit `495e1d6` for correctness, plus a holistic re-check of the whole change.

**Critical**: none. **Should-fix**: none.

All six invariants re-verified in source and still pinned by their named tests. The four points flagged for scrutiny all came back clean:

- Whitespace-only → fallback still works: `" ".join("   ".split())` → `""`, which is falsy, so `reason` keeps its `BLOCKED_REASON_FALLBACK` initialisation.
- `errors="replace"` does not disturb the character budget — U+FFFD is a single code point and the slice is taken on the decoded `str`, not on bytes.
- The log removal left no orphan; `blocked` is still consumed by the `return` below.
- The markdown-fence risk is genuinely closed, and for the right reason: `format_failure_comment` renders the reason as `f"**Error:** {message}"`, so a collapsed reason sits mid-line and cannot open a fence.

**Findings** (both nice-to-have):

1. `test_collapse_happens_before_truncation` does not test what its name claims. Its 60 chunks are separated by a *single* `\n`, so collapsing is a 1:1 substitution that commutes with a prefix slice — both orderings produce byte-identical output and the assertions (`"\n" not in result`, `len(result) == 503`) pass under either.
2. The `ValueError` arm of the `except` in `read_and_clear_blocked` is unreachable now that `errors="replace"` is in place.

**Decisions**:

- **1 — Accept.** A test that claims to pin an ordering but cannot fail against the wrong one is worse than no test: it gives false confidence in exactly the property the change exists to guarantee.
- **2 — Accept, comment only.** Keep the guard — the docstring promises the function never raises and three `finally` blocks depend on it. Add one line so the next reader does not conclude the `except` is what handles bad bytes. Do not drop `ValueError`.

**Process note**: a Bash `python -c` the reviewer used to confirm finding 1 was declined by the user. Asked afterwards, it confirmed the finding rested on a deterministic argument (1:1 substitution commutes with a prefix slice), not on the declined command, but qualified its confidence as analytical rather than executed and flagged that its suggested `455` count was unverified arithmetic. The implementing engineer was therefore instructed to confirm the counts against the source rather than trust them — it did, empirically, via a temporary test it then deleted.

**Changes**: both findings implemented. `test_collapse_happens_before_truncation` now uses a 5-newline separator and asserts `result.count("x") == 455` (the rejected ordering yields 335 — confirmed by execution before landing); two-line comment added above the `except` arm.

**Status**: pending commit.

Committed as `0cb25ff` — "Make the collapse-before-truncate test actually pin the ordering" (2 files, +10/-4). Pushed fast-forward.

---

## Round 4 — 2026-08-23

Reviewed `0cb25ff` plus a final holistic pass.

**Critical**: none. **Should-fix**: none. **Nice-to-have**: none.

The reviewer independently re-derived the arithmetic rather than accepting it: raw input 895 chars; collapse-first yields 659 chars in 11-char units, sliced to 500 → 455 x's; truncate-first cuts 15-char units → 335 x's. 455 ≠ 335, so the rejected ordering genuinely fails the assertion. It also confirmed the count is platform-independent (`str.split()` treats `\r` as whitespace, so Windows newline translation round-trips cleanly) and that the new comment is factually correct — `UnicodeDecodeError` is the only `ValueError` reachable in that `try`, since a directory or permission failure raises `OSError`.

All six invariants re-verified; the commit touched no control flow.

**Verdict**: ready to merge.

**Changes**: none. Loop terminates.

---

## Final Status

**Rounds**: 4 (two produced changes, two were verification-only).

**Commits produced**:

| SHA | Summary |
|-----|---------|
| `495e1d6` | Harden blocked-marker read and drop residual fabricate pressure |
| `0cb25ff` | Make the collapse-before-truncate test actually pin the ordering |

**Findings**: 9 raised across rounds 1–2, 6 accepted and fixed, 3 rejected as out of scope. No critical issues at any point.

The one genuine correctness bug was round 1 finding 1: `read_and_clear_blocked` decoded with strict UTF-8, so a non-UTF-8 marker raised `UnicodeDecodeError` — a `ValueError`, not the `OSError` its guard caught — out of a function whose docstring promises it never raises and which three `finally` blocks depend on. It would have replaced the in-flight LLM failure with a generic label, losing exactly the reason the marker exists to deliver.

**Rejected findings** (recorded so they are not re-raised): `get_diff_stat` untracked-file handling (pre-existing, affects every workflow); allowlisting `github_Issue_Workflow_Matrix.html` for file size (passes today); exporting `TaskOutcome` from `implement/__init__.py` (issue scoped that file as "no change").

**Architecture checks** (run by the supervisor):

- `vulture` — no output.
- `lint-imports` — 21 contracts kept, 0 broken, across 693 files and 3552 dependencies.

**Final branch state**: CI=PASSED, Rebase=UP_TO_DATE, Tasks=COMPLETE (24/24), working tree clean.
