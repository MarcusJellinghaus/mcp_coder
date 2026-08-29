# review-plan review log 2

Issue #1132 — Remove `--execution-dir`: collapse Claude's working directory onto `project_dir`.

Run 1 (`plan_review_log_1.md`) reached the 5-round automated limit without converging and was
handed off for human review. This run resumes from that state.

Two findings were raised repeatedly in run 1 and never applied:

- `summary.md` — "each one still supplies the value that is now passed as `project_dir` — so no
  parameter goes unused" is false after 4a for seven signatures (rounds 3, 4, 5).
- `step_3.md` — the command docstring `Args:` entries for the removed flag appear in no step's
  WHERE (rounds 4, 5).

Base: branch is one commit behind `origin/main` (`47e72e0`, vscodeclaude — disjoint files);
no rebase required.

## Round 1 — 2026-08-29

**Findings**:
- `step_4.md` — high — the mechanical test rules only rewrite `execution_dir=<x>`, missing ~90
  `prompt_llm` calls that pass no directory at all (`tests/llm/test_interface.py`,
  `test_llm_sessions.py`, `test_claude_integration.py`, `test_input_validation.py`,
  `test_prototype_session_interleave.py`). Each raises `TypeError` after 4a, and several sit
  behind `claude_api_integration` / `claude_cli_integration` so the fast gate hides them.
- `step_4.md` — high — six tests pin the removed `None` semantics; applying rule 1 to them
  yields `project_dir=None` into a required `str | Path`.
- `step_1.md:18` — high — the WHERE row cites `test_interface.py:302-385` and `:723-773`, which
  patch `ask_claude_code_cli`. They are Claude tests the step itself says to leave alone;
  following the row edits working tests and leaves step 1 red.
- `summary.md:150` — medium — the "no parameter goes unused" greenness rationale is false
  (raised in rounds 3, 4 and 5 of run 1, never applied).
- `step_3.md:20` — medium — the command docstring `Args:` entries for the removed flag appear in
  no step's WHERE (raised in rounds 4 and 5 of run 1, never applied).
- `step_3.md:105` — medium — `test_none_returns_cwd` and `test_default_does_not_warn` are
  unassigned in the `TestResolveExecutionDir` split; the first becomes a `TypeError`.
- `summary.md:177` — low — 4a and 4b are two commits in one step file; `prepare_task_tracker`
  writes one row per file, so the tracker would show five rows for six commits.
- low — stray `execution_dir=None` in `test_mcp_config_integration.py:122`; the `commit.py`
  resolve side effect on `validate_git_repository` is unframed.

**Decisions**: All accepted — every finding is a step-greenness or plan-precision defect, none
touches scope or architecture, so nothing was escalated. Skipped only the minor line drift in
step 4 E1 (`rebase.py:319` → `:326`, `task_tracker_prep.py:78` → `:84`); the knowledge base says
precise line numbers are not worth fixing.

**User decisions**: None required.

**Changes**: `step_4.md` split into `step_4a.md` / `step_4b.md`. 4a gained rule 3 (every
remaining `prompt_llm` call in `tests/` must pass `project_dir=`) plus a grep covering
marker-excluded files, and a delete-or-rewrite table above the mechanical rules. `step_1.md`
retargeted onto the langchain assertions it actually breaks. `step_3.md` gained the command
docstring WHERE row, the two missing deletions, and the `commit.py` resolve note. `summary.md`
greenness clause replaced with the seven-signature list and the `W0613` reason. `Decisions.md`
created.

The reviewer also re-verified run 1's corrections against source and confirmed they landed
correctly: the 4a/4b split, the E1 exception rows, the `RealLLMService` keyword-only mechanism
and the `claude_cli_integration` marker runs.

**Status**: committed
