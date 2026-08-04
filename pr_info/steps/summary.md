# Summary — #1107: TASK_TRACKER entry gate + CI-proven exit guard for `review-implementation`

## Goal

Close two holes in headless `review-implementation`:

1. **Entry gate (Gate 1)** — refuse to start when `## Tasks` in
   `pr_info/TASK_TRACKER.md` has unchecked items; point the human at
   `/implementation_finalise`.
2. **Exit guard (Gate 2)** — at the final dismiss gate, refuse the success label
   unless CI is *proven* green (`CIStatus.PASSED`), not merely "not obviously red".

`review-plan` is untouched. Both gates are implementation-lane only.

This is almost all wiring: the only genuinely new logic is `assess_ci` (~6 lines),
which *removes* a duplicated status→verdict predicate rather than adding one.

## Architectural / design changes

- **New policy layer `mcp_coder/checks/ci_policy.py`** holding one function,
  `assess_ci(status, *, require_proven)`. It becomes the **single implementation**
  of the CI-status→verdict policy, called by three sites:
  - the CLI `_exit_code` (`require_proven=False` → CLI behaviour byte-identical),
  - the CLI pre-`--fix` bail-out in `execute_check_branch_status` (also `False`),
  - Gate 2 (`require_proven=True`).
  It lives in `checks/` (a layer `workflows/` may import; the CLI module is not).
  It is **not** placed in `checks/branch_status.py` — that file is a declared pure
  re-export shim — nor in `workflow_steps/ci.py` (already ~606 lines, owns the LLM
  fix loop). No `tach.toml` change (`mcp_coder.checks`, `exact = false`, already
  covers it).

- **Allowlist, not denylist.** Gate 2 treats only `PASSED` as success and only
  `FAILED` as the existing `17f-ci`; **everything else** (`PENDING`,
  `NOT_CONFIGURED`, `UNKNOWN`, `UNAVAILABLE`) is `"ci_unknown"`. `_collect_ci_status`
  maps transient API errors and "no CI" to `NOT_CONFIGURED`, so the earlier
  `UNKNOWN`/`UNAVAILABLE` denylist would have missed almost every hole. An allowlist
  also degrades safely if upstream adds a new `CIStatus` member.

- **New gate module `mcp_coder/workflows/review/gates.py`** (following the
  `severity.py` / `handoff.py` precedent) holds both gate functions as pure logic
  returning `(reason, details)` tuples. `core.py` gets two thin call sites and
  nothing else, staying under its 600-line budget. Message-building (task-list
  capping, observed CI status) lives in the gates, not in `core.py`.

- **One new `ReviewConfig` field, `enforce_implementation_gates`**, gates *both*
  gates (`True` on `REVIEW_IMPLEMENTATION`, `False` on `REVIEW_PLAN`). It is a
  dedicated per-concern boolean, consistent with the existing
  `inject_base_branch` / `run_after_steps` / `thread_pr_feedback` fields. Gate 2
  deliberately does **not** reuse `run_after_steps` (that flag means "run rebase +
  CI", adjacent but not the same authorization question).

- **`_fail` gains an optional `details: str | None`**, inserted immediately after
  the `❌ …` header line and before Round / Verdict / Elapsed, so the cause is the
  first thing read. Used by both gates (open-task list / malformed-tracker cause /
  observed `ci_status`).

- **Two new failure labels** in `config/labels.json`, each with distinct recovery:
  - `code_review_open_tasks` → `status-17f-tasks:code-review-open-tasks`,
    recovery `/implementation_finalise`.
  - `code_review_ci_unknown` → `status-17f-ci-unknown:code-review-ci-undeterminable`,
    recovery `/check_branch_status`. Distinct from `17f-ci` on purpose: "couldn't
    tell" has a different fix (check the token / whether CI exists) than "fix the
    code".

## Design decisions carried from the issue (and the KISS review)

- Gate 1 **fails (RC=1)** rather than handing off — a handoff routes to
  `07:code-review` whose recovery refuses for the same reason (a loop).
- Gate 1 error handling is collapsed to **two branches**:
  `TaskTrackerFileNotFoundError` → **skip** (mirrors `create_pr`); any other
  exception (including `TaskTrackerSectionNotFoundError`) → **block** with `"tasks"`,
  the `details` message naming the actual cause.
- Gate 2 makes **exactly one** fresh `collect_branch_status` call — no retry loop.
  "How long to wait for CI" is owned by `CI_MAX_POLL_ATTEMPTS`.
- `_exit_code` keeps its two `fail_on_reviews` branches at their current precedence;
  only the CI comparisons move behind `assess_ci`. **CLI exit codes unchanged for
  every input, including `--fail-on-reviews` combinations.**

## Behaviour matrix (Gate 2)

| `ci_status` | verdict (`require_proven=True`) | outcome |
|---|---|---|
| `PASSED` | `ok` | success → `status-08:ready-pr` |
| `FAILED` | `failed` | `"ci"` → `status-17f-ci` (unchanged) |
| `PENDING` / `NOT_CONFIGURED` / `UNKNOWN` / `UNAVAILABLE` | `undeterminable` | `"ci_unknown"` → `status-17f-ci-unknown`, RC=1 |

## Folders / modules / files created or modified

**Created**
- `src/mcp_coder/checks/ci_policy.py` — `assess_ci`
- `src/mcp_coder/workflows/review/gates.py` — `check_open_tasks_gate`, `check_ci_proven_gate`
- `tests/checks/test_ci_policy.py`
- `tests/workflows/review/test_gates.py`

**Modified — source**
- `src/mcp_coder/cli/commands/check_branch_status.py` — `_exit_code` + pre-`--fix` bail-out delegate to `assess_ci`
- `src/mcp_coder/workflows/review/config.py` — new `enforce_implementation_gates` field + `"tasks"` / `"ci_unknown"` in `REVIEW_IMPLEMENTATION.failure_labels`
- `src/mcp_coder/workflows/review/handoff.py` — `details` param on `_fail`
- `src/mcp_coder/workflows/review/core.py` — two call sites (gate 1 top of `body()`, gate 2 in dismiss cascade)
- `src/mcp_coder/config/labels.json` — two new labels

**Modified — tests**
- `tests/cli/commands/test_check_branch_status_exit_code.py` — regression + delegation
- `tests/config/test_label_config.py` — `REVIEW_LABELS` (13 → 15), `REVIEW_FAILURE_IDS`, docstring
- `tests/cli/commands/test_define_labels.py` — expected label-name sequence
- `tests/workflows/review/test_config.py` — new field + failure_labels
- `tests/workflows/review/test_handoff.py` — `details` insertion

**Modified — docs**
- `docs/processes-prompts/development-process.md` — `17f-tasks` / `17f-ci-unknown` rows
- `docs/processes-prompts/github_Issue_Workflow_Matrix.html` — new statuses
- `docs/cli-reference.md` — new statuses

## Step map (one commit each)

1. `assess_ci` policy helper + CLI delegation (behaviour byte-identical)
2. Two new labels in `labels.json` + label tests
3. `ReviewConfig.enforce_implementation_gates` + `failure_labels` entries
4. `_fail` gains `details` param
5. Gate 1 (entry gate) — `check_open_tasks_gate` + wire into `core.body()`
6. Gate 2 (exit guard) — `check_ci_proven_gate` + wire into dismiss cascade
7. Docs

Steps 5 and 6 depend on 1–4 being committed first.

## Acceptance criteria (from the issue)

- `review-implementation` refuses to start on unchecked `## Tasks`: RC=1,
  `status-17f-tasks`, comment naming open tasks (capped at 10) → `/implementation_finalise`.
- Missing `TASK_TRACKER.md` does **not** block (skipped).
- No `## Tasks` section **does** block, comment naming that cause.
- Final dismiss gate: only `PASSED` → `ready-pr`; `PENDING`/`NOT_CONFIGURED`/`UNKNOWN`/`UNAVAILABLE` → RC=1 + `17f-ci-unknown`; red-but-determinable still `17f-ci`.
- Gate 2 makes exactly one `collect_branch_status` call.
- `assess_ci` is the single implementation, called by Gate 2, `_exit_code`, and the pre-`--fix` bail-out.
- `mcp-coder check-branch-status` exit codes unchanged for every input (regression-tested).
- Both labels exist with the correct recovery commands, covered by tests.
- `review-plan` behaviour unchanged.
- `core.py` stays under 600 lines.
