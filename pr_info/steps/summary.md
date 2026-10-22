# Summary — #1268 Shared structured failure / hand-off comment builder

## Goal

Every failure, hand-off and crash comment any workflow posts is produced by **one
builder** in `workflow_utils/failure_handling.py`, with a `❌` heading, a fixed
field order, `**Branch:** <name> @ <sha7>` and `**Build:**` (when `BUILD_URL` is
set). The review rebase hand-off stops being a bare
`❌ Branch could not be rebased cleanly — handing off.` and instead names *why*
(dirty tree, no base, base missing, conflict, rebase failed, push failed), the
base commit, the files involved and the next step.

## Architectural / design changes

1. **Shared comment builder (`workflow_utils/failure_handling.py`).**
   - `build_failure_comment(project_dir, *, title, kind, fields, elapsed, extra_section)`
     renders `## ❌ <title> <kind>`, then fields sorted by one constant
     `FIELD_ORDER`, then an optional extra section. Fields with `None` value are
     skipped; unknown labels sort just before `Next step`.
   - The builder adds its own `Branch`, `Elapsed`, `Build` fields. `BUILD_URL` is
     read from the environment here only — the `build_url` plumbing in
     `implement` is removed.
   - All git lookups sit behind one patchable helper `_branch_head(project_dir)`
     which never raises.
   - Callers pass plain `(label, value)` tuples (`CommentField`); no new
     dataclass. `kind` is a plain string: `"Failed"`, `"Handed Off"`, `"Crashed"`.

2. **`run_guarded` owns the crash heading.** `comment_header` is replaced by
   `workflow_title`; the net always renders `## ❌ <title> Crashed`.
   `build_comment` now returns `(extra_fields, extra_section)` only, so it can no
   longer silently override the heading (the dead `"## Implementation Failed"`
   header disappears).

3. **Per-workflow formatters are deleted, not rewritten.** implement,
   create_plan, create_pr and fix_ci call the builder directly. implement keeps one
   small `_comment_parts` helper shared by its deliberate `_fail` and its net.
   Output is unified across workflows (not byte-identical to earlier releases).

4. **`RebaseOutcome` instead of `bool` (`workflow_steps/rebase.py`).**
   `_attempt_rebase_and_push` returns a frozen dataclass
   `RebaseOutcome(reason, base_branch, base_sha, files)` with an `.ok` property.
   A failed `rebase_onto_branch` is classified with a read-only
   `git merge-tree --write-tree --name-only --no-messages` probe (conflict vs
   other failure, plus likely conflicting files). The base SHA is read once,
   right after the rebase attempt. `_after_steps` returns
   `(reason, outcome)`. No mcp-workspace change.

5. **Structured review terminals (`workflows/review/handoff.py`).**
   - `ReviewConfig.display_name` ("Implementation Review" / "Plan Review").
   - `_fail` → `## ❌ <Lane> Failed` with Category / Stage / Error / Verdict.
   - `_route_to_human` builds its own comment *after* the round-log flush,
     `## ❌ <Lane> Handed Off`, logs a `REVIEW HANDED OFF` warning banner, and
     drops its old `"❌ "` prefix. Rebase sites pass only `rebase=outcome`; a
     `reason -> (category, reason_text, next_step)` table in `handoff.py` drives
     Category, Reason and Next step. Rounds-cap / escalate sites pass `category=` / `reason=`.
   - Review net → `## ❌ <Lane> Crashed`.

### Canonical field order (`FIELD_ORDER`)

```
Category, Stage, Error, Reason, Branch, Base, PR, Likely conflicting files,
Uncommitted files, Progress, Verdict, Next step, Elapsed, Build
```

### Workflow titles

implement → "Implementation", create_plan → "Planning", create_pr →
"PR Creation", fix_ci → "CI Fix", fix_conflict → "Fix Conflict", review →
`config.display_name`.

## Files created / modified

### Created
- `tests/workflow_utils/test_failure_comment.py` — builder tests (step 1)

### Modified — source
- `src/mcp_coder/workflow_utils/failure_handling.py` — builder, `_branch_head`, `run_guarded` (steps 1, 2)
- `src/mcp_coder/workflows/implement/failure_reporting.py` — `_comment_parts`, `_fail` (step 2)
- `src/mcp_coder/workflows/implement/core.py` — net, drop `build_url` / `os` (steps 2, 6)
- `src/mcp_coder/workflows/create_plan/core.py`, `create_plan/__init__.py` (steps 2, 3)
- `src/mcp_coder/workflows/create_pr/helpers.py`, `create_pr/core.py` (steps 2, 4)
- `src/mcp_coder/workflows/fix_ci/core.py` (steps 2, 5)
- `src/mcp_coder/workflows/fix_conflict/core.py` (steps 2, 6)
- `src/mcp_coder/workflow_steps/rebase.py` — `RebaseOutcome`, probes (step 6)
- `src/mcp_coder/workflows/review/config.py` — `display_name` (step 2)
- `src/mcp_coder/workflows/review/steps.py` — tuple return, comment fix (steps 6, 8)
- `src/mcp_coder/workflows/review/core.py` — net title, call sites (steps 2, 6, 8)
- `src/mcp_coder/workflows/review/handoff.py` — `_fail`, `_route_to_human` (steps 7, 8)

### Modified — tests
- `tests/workflow_utils/test_run_guarded.py`
- `tests/workflows/implement/test_failure_reporting.py`, `test_core_workflow.py`, `test_core_failure_routing.py`
- `tests/workflows/create_plan/test_failure_handling.py`
- `tests/workflows/create_pr/test_failure_handling.py`
- `tests/workflows/fix_ci/test_core.py`
- `tests/workflows/fix_conflict/test_core.py`
- `tests/workflow_steps/test_rebase.py`
- `tests/workflows/review/conftest.py`, `test_core.py`, `test_core_after_steps.py`, `test_core_gates.py`, `test_handoff_route.py`, `test_config.py`

### Modified — docs
- `docs/processes-prompts/development-process.md` (escalations now post a structured comment) (step 8)

## Steps

1. Shared builder `build_failure_comment` + `_branch_head`
2. `run_guarded(workflow_title=…)` + all six nets + implement migration + `ReviewConfig.display_name`
3. create_plan deliberate failure → builder
4. create_pr deliberate failure → builder
5. fix_ci deliberate failure → builder
6. `RebaseOutcome` + merge-tree classification; callers compile against it
7. Review `_fail` → structured "Failed" comment
8. Review `_route_to_human` → structured "Handed Off" comments + rebase table + docs

## Test conventions for every step

- Tests that check a comment patch
  `mcp_coder.workflow_utils.failure_handling._branch_head` (e.g. to return
  `("feat", "abc1234")`) so no real git is touched.
- Tests asserting **no** `**Build:**` line clear `BUILD_URL`
  (`patch.dict(os.environ, {}, clear=True)` or `monkeypatch.delenv("BUILD_URL", raising=False)`).
- Only `test_failure_comment.py` asserts the full field order; workflow tests
  assert their own lines (heading, Category, PR, sections).
- Every rebase mock returns a `RebaseOutcome`, never a bool; no caller uses
  `if outcome:` — always `.ok`.
