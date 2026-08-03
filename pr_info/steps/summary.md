# Summary — #1106: severity-aware triage + rounds-cap handoff for the review loop

## Problem

The headless review loop (`workflows/review/core.py`, one shared loop driven by a
`ReviewConfig` for both `review-plan` and `review-implementation`) has four
lane-independent defects:

1. **Severity is emitted but never consumed.** Reviewers mandate
   `file:line — SEVERITY — desc` (`critical|high|medium|low`), but triage treats
   `low` and `high` identically, so the loop burns its whole round budget polishing
   nitpicks — and each fix hands the next fresh reviewer new material to critique
   (a self-feeding loop).
2. **The supervisor has no round context.** `_get_verdict` sends only header + report,
   so the final round is indistinguishable from the first.
3. **The rounds cap fails instead of handing off.** At the cap `run_review_workflow`
   calls `_fail(..., "rounds")` (failure label, RC=1), even though `escalate_label_id`
   already routes to the human-recovery label (`status-04:plan-review` /
   `status-07:code-review`) the workflow is converging toward.
4. **No terminal path commits its own log.** `write_round_log` runs *after* the commit,
   so a round's log is committed by the *next* round. On every terminal path
   (dismiss, escalate, rebase, cap) the last round's log is written to the tree and lost.

## Goal (acceptance criteria, condensed)

- A round at/after the lane's `strict_from_round` whose findings are all `low`/`medium`
  → `dismiss`, deterministically (mocked-LLM testable).
- An unparseable report (no severities) → keep `tasks` (**fail open**).
- Severity cutoff is a per-lane `ReviewConfig` field; the value the prompt states is the
  value the backstop enforces (single source).
- Rounds cap with reason `rounds` → stays on the review label, committed log, issue
  comment, **no failure label, RC=0**.
- Cap with an open CI finding → still fails to `status-17f-ci` (CI stays terminal).
- A round with `pending_ci_note` set is never severity-downgraded.
- The last executed round always appears in the **committed** log on every terminal path.
- Existing dismiss/escalate/commit-failed/push-failed/rebase/CI paths keep their routing,
  labels and exit codes; new: every terminal path gains a log flush, every handoff path
  gains a comment.
- `status-14f-rounds` / `status-17f-rounds` gone from config, docs and tests.
- `core.py` under 600 lines.

## Architectural / design changes

**Two-layer severity enforcement (advisory prompt + deterministic backstop).**
The prompt rule alone is untestable with a mocked LLM, so a pure `max_severity(report)`
backstop deterministically downgrades a `tasks` verdict to `dismiss` at/after
`strict_from_round` when no `critical`/`high` remains. The two layers are complementary:
if the supervisor obeys the prompt, the cap is never reached; the backstop is the
guarantee for when it doesn't.

**Backstop realized as a verdict transform, not a new branch** (KISS simplification).
Immediately after `_get_verdict`, before dispatch, a `tasks` verdict may be rewritten to
`Verdict("dismiss")`; the existing dismiss branch then handles logging + labelling. No
duplicated terminal logic; the `pending_ci_note is None` guard gives the CI exemption for
free.

**`_flush_round_log` = commit + push only** (KISS simplification of the issue's
"write + commit + push"). The round body always *writes* its log (the continuing `tasks`
path relies on the next round's commit); terminal paths *additionally* commit+push. The
cap reaches `_route_to_human` right after the last `tasks` round already wrote its entry,
so the flush must not re-write it — otherwise a duplicate `## Round N` block appears. Uses
`commit_all_changes(message, project_dir)` directly (no LLM message call), best-effort on
`commit-failed`/`push-failed` (warn, never recurse).

**Failure-reason convention** (inherited by #1107): a reason meaning *"a human must act on
the work"* routes through `_route_to_human` → `escalate_label_id`, RC=0; a reason meaning
*"the run broke"* routes through `_fail` → `failure_labels`, RC=1. Round exhaustion is the
former; `ci`, `timeout`, `mcp_unavailable`, `commit-failed`, `push-failed` are the latter.

**Module layout (`core.py` 729 → < 600).** Two new modules plus two cohesive relocations:

- `severity.py` *(new, pure)* — `max_severity`.
- `handoff.py` *(new)* — terminal routing: `_set_label`, `_fail` (**relocated from
  core**), `_flush_round_log`, `_route_to_human`.
- `reviewer.py` — the PR-feedback prompt-framing helpers `_quote_pr_feedback` /
  `_pr_feedback_note` / `_QUOTE_FENCE` are **relocated here from core** (prompt-input
  framing is cohesive with the reviewer/supervisor turn helpers).
- `core.py` keeps the loop, `_resolve_context`, `_after_steps`, and constants.

Relocating `_set_label`/`_fail` is more aligned with the issue's intent ("core keeps only
the loop") than moving `_after_steps` (which a test reads via `inspect.getsource`), and is
what reliably clears the 600-line budget. Relocations are behaviour-preserving; test
fixtures repoint their `monkeypatch` targets from `core` to `handoff`.

**Round context by substitution only.** `{round_number}` / `{max_rounds}` are threaded
into `_run_reviewer` (fresh reviewer prompt) and `_get_verdict` (supervisor header),
reusing the existing `{issue_number}` / `{base_branch}` substitution plumbing.
`{strict_from_round}` and `{tie_break}` come from the single `ReviewConfig` fields, so the
number the prompt states cannot drift from the number the backstop enforces.

## New `ReviewConfig` fields

| Field | Plan | Implementation |
|-------|------|----------------|
| `strict_from_round: int` | 3 | 3 |
| `tie_break: str` | "default to simpler plans" | "default to better code quality" |

Both added at the end of the dataclass with defaults (`= 3`, `= ""`) so existing
instantiations remain valid; explicit values are set on both real instances. The
now-unreachable `"rounds"` key is removed from both `failure_labels` maps.

## Folders / modules / files

**Created**
- `src/mcp_coder/workflows/review/severity.py`
- `src/mcp_coder/workflows/review/handoff.py`
- `tests/workflows/review/test_severity.py`
- `tests/workflows/review/test_handoff.py`

**Modified**
- `src/mcp_coder/workflows/review/core.py` — backstop wiring, cap→handoff, terminal-path
  flush, round-context threading; `_set_label`/`_fail` and note helpers relocated out.
- `src/mcp_coder/workflows/review/config.py` — new fields; drop `"rounds"` key.
- `src/mcp_coder/workflows/review/reviewer.py` — round-context substitution; note helpers
  relocated in.
- `src/mcp_coder/workflows/review/__init__.py` — export `max_severity` (optional).
- `src/mcp_coder/prompts/prompts.md` — §Review Supervisor + both reviewer sections.
- `src/mcp_coder/config/labels.json` — remove the two `*-rounds` labels.
- `docs/processes-prompts/development-process.md` — remove rounds rows.
- `docs/processes-prompts/github_Issue_Workflow_Matrix.html` — remove rounds cards.
- `tests/workflows/review/test_config.py`, `test_core.py`, `test_core_after_steps.py`,
  `test_reviewer.py` — new fields, fixture repoints, new behaviour.
- `tests/config/test_label_config.py`, `tests/cli/commands/test_define_labels.py` —
  remove rounds labels.

## Implementation steps

1. `severity.py` — pure `max_severity`.
2. Relocate PR-feedback note helpers → `reviewer.py` (behaviour-preserving).
3. `ReviewConfig` — add `strict_from_round` + `tie_break`.
4. Create `handoff.py` — relocate `_set_label` + `_fail` (behaviour-preserving).
5. Severity backstop — verdict transform in `core.body()`.
6. Handoff wiring — add `_flush_round_log` + `_route_to_human`; rewire terminal paths.
7. Round context + prompt rules — `reviewer.py` substitution + `prompts.md` + `_CI_NOTE`.
8. Remove dead `*-rounds` labels from config/docs/tests; verify `core.py` < 600.

Each step is one commit: tests first, then implementation, with pylint + pytest + mypy
green before moving on. A pre-merge sweep for open issues carrying `status-14f-rounds` /
`status-17f-rounds` (e.g. mcp-tools-sql#44) must run before Step 8 lands, because
`define-labels` deletes `status-*` labels absent from config.
