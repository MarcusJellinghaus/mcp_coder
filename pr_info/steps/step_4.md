# Step 4 — Create `handoff.py`; relocate `_set_label` + `_fail`

See `pr_info/steps/summary.md` (§"Module layout"). A behaviour-preserving refactor that
creates the terminal-routing module and moves the two existing terminal helpers into it.
This is the primary reduction toward `core.py` < 600 and the home for Step 6's new helpers.

## WHERE
- New: `src/mcp_coder/workflows/review/handoff.py`
- From: `src/mcp_coder/workflows/review/core.py` (move `_set_label`, `_fail`)
- Tests: `tests/workflows/review/test_core.py` and `test_core_after_steps.py` fixtures.

## WHAT
Move verbatim into `handoff.py` (unchanged signatures):
```python
def _set_label(config, project_dir, to_label_id, update_issue_labels) -> None: ...
def _fail(config, project_dir, reason, *, update_issue_labels, post_issue_comments,
          round_number=None, verdict=None, elapsed=None) -> int: ...
```

## HOW
- Move the imports these functions need into `handoff.py`: `IssueManager`,
  `update_workflow_label`, `WorkflowFailure`, `handle_workflow_failure`,
  `format_elapsed_time`, and `Verdict` (type hint). Remove now-unused imports from
  `core.py`.
- In `core.py`, import the two helpers: `from .handoff import _fail, _set_label` and keep
  all call sites unchanged.
- **Test fixture repoint** — the `env` fixtures currently patch these on the `core` module.
  Because the functions now live in `handoff`, repoint:
  - `monkeypatch.setattr(core, "handle_workflow_failure", ...)` → `handoff`
  - `monkeypatch.setattr(core, "IssueManager", ...)` → `handoff`
  - `monkeypatch.setattr(core, "update_workflow_label", ...)` → `handoff`
  The mock objects (`env.handle_workflow_failure`, `env.update_workflow_label`) keep the
  same identity, so the existing `assert_*` calls are unchanged.
- Leave `core`'s patched `run_formatters`, `commit_changes`, `push_changes`,
  `get_latest_commit_sha`, `is_working_directory_clean`, `get_current_branch_name`,
  `collect_branch_status` where they are — those stay in `core`.

## ALGORITHM
_None — relocation only._

## DATA
No behavioural or data change; `_fail` still returns `1`, `_set_label` still returns `None`.

## TDD
- No new behaviour to test. The full `test_core.py` / `test_core_after_steps.py` suites
  must pass after the fixture repoint.
- Confirm `core.py` shrank (`mcp-coder check file-size --max-lines 600`); it may still be
  slightly over until Step 6's dedup — that is expected and finalised in Step 8.

## LLM PROMPT
> Implement Step 4 from `pr_info/steps/step_4.md` (see `pr_info/steps/summary.md`). Create
> `workflows/review/handoff.py` and move `_set_label` and `_fail` verbatim from `core.py`
> into it, moving their required imports and removing now-unused imports from `core.py`.
> Import them back into `core.py` so all call sites are unchanged. Repoint the `env`
> fixtures in `test_core.py` and `test_core_after_steps.py` so `handle_workflow_failure`,
> `IssueManager`, and `update_workflow_label` are patched on the `handoff` module instead of
> `core` (keep the same mock identities). This is behaviour-preserving: all existing review
> tests must pass. Run pylint, pytest (`-n auto` with integration exclusions), and mypy. One
> commit.
