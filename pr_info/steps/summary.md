# Summary: validate task tracker structure, repair or fail loudly (#1093)

## Goal

An invalid `pr_info/TASK_TRACKER.md` (e.g. checkboxes in `## Tasks` that are not under a
`### Step N:` header, #1085 / #1146) must be caught at the start of implement. Prep then
repairs it or fails with a labelled, line-precise error. Today it runs for hours with
degraded observability.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Structure check | `validate_task_tracker`: file + `## Tasks` exist | `classify_task_tracker` → `TrackerState` MISSING / INVALID / EMPTY / POPULATED plus violation strings with file line numbers |
| "Populated?" | `has_implementation_tasks` (any checkbox) | the classifier; INVALID is never treated as populated |
| Prerequisites | fail on missing `## Tasks` | MISSING fails, INVALID logs a WARNING; no repair |
| Prep result | `bool` | returns `None`; raises `TrackerPrepError(reason, message)` with `.stage` |
| Prep LLM use | one call, no session | `_llm_rounds`: one session, guard + check after every call, feedback prompt on failure |
| Repair | none | no `[x]` → reset to template + populate; some `[x]` → LLM restructure checked by `check_restructure` |
| Failure safety | tracker could stay modified | `try/finally` writes the original bytes back on any failure, incl. `SystemExit` |
| Commit | `commit_all_changes` | `commit_paths([tracker])` |
| `## Tasks` end | any `##`+ header *containing* "pull request" | header whose whole text is "Pull Request" |
| Progress log | empty/exception at DEBUG | WARNING |
| Failure comment progress | run counter / tracker total | `get_task_counts()` done/total, omitted if unreadable |

### Key design decisions (KISS)

- **One scanner, two consumers.** `_scan_tracker(content)` turns the file into per-line
  records (line number, section, enclosing step, checkbox state, normalized name).
  `classify_tracker_content` and `check_restructure` both read it. HTML comments are skipped.
- **Violations are plain strings** that already contain `pr_info/TASK_TRACKER.md line N: ...`.
  The same text goes to the log, the failure message and the prompt placeholder.
- **One LLM loop** (`_llm_rounds`) for population (1 call + 3 feedback rounds) and restructure
  (3 attempts). Only the first prompt and the check function differ. Both share the
  "Task Tracker Feedback Prompt".
- **Typed exception, failure reason fixed by the starting state:** EMPTY →
  `task_tracker_prep_failed` / "Task tracker preparation"; INVALID → `general` /
  "Task tracker validation". `core.py` catches the exception and calls `fail(...)`.
- **The reset path reuses population.** It writes `TASK_TRACKER_TEMPLATE` with
  `write_lf_text`, then runs the EMPTY path.
- **Parsers stay lenient.** Only the classifier is strict (`### Step N: <title>`).
- `uv.lock` is in `DEFAULT_IGNORED_BUILD_ARTIFACTS`, which `check_git_clean` ignores, so
  committing only the tracker cannot block the next run.

## Files

### Created
- `src/mcp_coder/workflow_utils/task_tracker_classify.py`: `TrackerState`, `_scan_tracker`,
  `classify_tracker_content`, `classify_task_tracker`, `describe_violations`,
  `EXPECTED_FORMAT`, `has_completed_tasks`, `check_restructure`
- `tests/workflow_utils/test_task_tracker_classify.py`
- `tests/workflow_utils/test_task_tracker_restructure_check.py`
- `tests/workflow_utils/test_data/populated_tracker.md` (real tracker, `git show f9fce18:pr_info/TASK_TRACKER.md`)
- `tests/workflows/implement/test_task_tracker_repair.py`

### Modified
- `src/mcp_coder/workflow_utils/task_tracker.py`: section-end fix; remove `validate_task_tracker`
- `src/mcp_coder/workflows/implement/prerequisites.py`: classifier; remove `has_implementation_tasks`
- `src/mcp_coder/workflows/implement/__init__.py`: drop the `has_implementation_tasks` export
- `src/mcp_coder/workflows/implement/task_tracker_prep.py`: `TrackerPrepError`, guard, restore,
  `_llm_rounds`, population, repair, log levels
- `src/mcp_coder/workflows/implement/constants.py`: `MAX_TRACKER_FEEDBACK_ROUNDS`, `MAX_TRACKER_REPAIR_ATTEMPTS`
- `src/mcp_coder/workflows/implement/core.py`: catch `TrackerPrepError`; drop `progress=` from the `fail` partial
- `src/mcp_coder/workflows/implement/failure_reporting.py`: progress from `get_task_counts()`
- `src/mcp_coder/prompts/prompts.md`: Restructure + Feedback prompts; planner "Do not edit" line
- `tools/jenkins_issue_patterns.toml`: `MC-IMPL-TRACKER-INVALID`
- Tests: `tests/workflow_utils/test_task_tracker_parsing.py` (or `_incomplete_tasks.py`),
  `test_task_tracker_validation.py`, `tests/workflows/implement/test_prerequisites.py`,
  `test_task_tracker_prep.py`, `test_core*.py`, `test_core_workflow.py`, `test_failure_reporting.py`,
  `tests/prompts/test_prompt_loader.py`, `tests/tools/test_jenkins_classify_logs.py`

## Steps

1. Section boundary fix
2. Classifier + prerequisites, remove `validate_task_tracker`
3. Restructure check (pure functions)
4. Prompts
5. Prep rewrite: exception, guard, restore, LLM rounds, population, core wiring, Jenkins signature
6. Repair: reset and restructure
7. Louder progress logging
8. Failure-comment progress from the tracker
