# Step 5: Prep rewrite — typed failure, guard, restore, LLM rounds, population

See `pr_info/steps/summary.md` (§2, §3 guard/restore/LLM errors, Constraints of issue #1093).
Repair (reset / restructure) follows in step 6; here an INVALID tracker fails directly.

## WHERE
- `src/mcp_coder/workflows/implement/task_tracker_prep.py`
- `src/mcp_coder/workflows/implement/constants.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/prerequisites.py`, `__init__.py`: remove `has_implementation_tasks`
- `tools/jenkins_issue_patterns.toml`
- Tests: rewrite `tests/workflows/implement/test_task_tracker_prep.py`; new
  `tests/workflows/implement/test_task_tracker_repair.py` (restore / guard / SystemExit cases);
  update `test_core*.py`, `test_core_workflow.py`, `test_prerequisites.py`,
  `tests/tools/test_jenkins_classify_logs.py`

## WHAT
```python
# constants.py
MAX_TRACKER_FEEDBACK_ROUNDS = 3   # after the initial population call
MAX_TRACKER_REPAIR_ATTEMPTS = 3   # restructure calls (used in step 6)

# task_tracker_prep.py
TRACKER_FILE = f"{PR_INFO_DIR}/TASK_TRACKER.md"
PREP_STAGES = {"task_tracker_prep_failed": "Task tracker preparation",
               "general": "Task tracker validation"}

class TrackerPrepError(Exception):
    def __init__(self, reason: str, message: str) -> None:  # sets .reason, .stage = PREP_STAGES[reason]

def prepare_task_tracker(project_dir, provider, mcp_config=None, settings_file=None) -> None: ...
def _ask_llm(prompt: str, session_id: str | None, *, project_dir, provider, mcp_config, settings_file) -> str | None
def _other_changed_files(project_dir: Path) -> list[str]
def _llm_rounds(ask, project_dir: Path, first_prompt: str,
                check: Callable[[str], list[str]], max_calls: int, reason: str) -> None
def _populate(ask, project_dir: Path, reason: str) -> None
def _population_errors(content: str) -> list[str]
```

## HOW
- `_ask_llm`: `prompt_llm(..., session_id=session_id, timeout=LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
  env_vars=prepare_llm_environment(project_dir), branch_name=...)`, then `store_session` as today
  (warning on failure). Returns `response["session_id"]`. Bind it with `functools.partial` → `ask`.
- `_other_changed_files`: staged + modified + untracked minus `DEFAULT_IGNORED_BUILD_ARTIFACTS`,
  minus `TRACKER_FILE` (casefold compare). Empty list = OK, including "nothing changed".
  Today's `len(all_changed) != 1` check and the empty-response check are removed.
- `_population_errors`: classify; POPULATED → `[]`; EMPTY → `["pr_info/TASK_TRACKER.md: no '### Step N:' sections were added"]`; INVALID → violations.
- `_populate`: `_llm_rounds(ask, project_dir, get_prompt(..., "Task Tracker Update Prompt"), _population_errors, 1 + MAX_TRACKER_FEEDBACK_ROUNDS, reason)`.
- Commit: `commit_paths("TASK_TRACKER.md with implementation steps and PR tasks updated", [tracker], project_dir)`;
  failure → `TrackerPrepError(reason, ...)`.
- `core.py`: replace the `if not prepare_task_tracker(...)` block with
  `try: prepare_task_tracker(...)` / `except TrackerPrepError as exc: return fail(exc.reason, stage=exc.stage, message=str(exc))`.
- Remove `has_implementation_tasks` from `prerequisites.py` (`__all__` too) and `__init__.py`;
  drop the now-unused parser imports there.
- Jenkins: add after `MC-IMPL-BLOCKED`:
  `[[signature]]` / `id = "MC-IMPL-TRACKER-INVALID"` / `regex = 'Stage: Task tracker validation'`
  (`handle_workflow_failure` logs `Stage: %s`; the prerequisites WARNING doesn't contain it).

## ALGORITHM
```
prepare_task_tracker: steps dir missing -> raise TrackerPrepError("task_tracker_prep_failed", ...)
state, v = classify_task_tracker(pr_info); POPULATED -> return; MISSING -> raise prep_failed
reason = "general" if INVALID else "task_tracker_prep_failed"; original = tracker.read_bytes(); done = False
try: INVALID -> raise TrackerPrepError(reason, describe_violations(v))  # step 6 replaces with repair
     else _populate(...); commit; done = True
except TrackerPrepError: raise;  except Exception as e: raise TrackerPrepError(reason, f"... {e}") from e
finally: if not done: tracker.write_bytes(original)

_llm_rounds: session=None; prompt=first
  for _ in range(max_calls): session = ask(prompt, session)
      others = _other_changed_files(); if others: raise TrackerPrepError(reason, f"LLM modified files other than {TRACKER_FILE}: {others}")
      errors = check(tracker.read_text()); if not errors: return
      prompt = feedback template with [violations] = describe_violations(errors), [expected_format] = EXPECTED_FORMAT
  raise TrackerPrepError(reason, f"Task tracker still invalid after {max_calls} LLM calls:\n{describe_violations(errors)}")
```
`LLMTimeoutError` / `McpServersUnavailableError` reach the broad `except` → starting-state
reason, message names the error, not retried. `SystemExit` is not caught, but `finally` restores.

## DATA
`prepare_task_tracker` returns `None`; failures are `TrackerPrepError` with `.reason`, `.stage`, `str()` = message.

## Tests (write first)
- POPULATED → no LLM call, no commit. INVALID → `TrackerPrepError` reason `general`, stage
  "Task tracker validation", message names the line; tracker unchanged.
- EMPTY + LLM populates correctly → `commit_paths` called with only the tracker.
- EMPTY + LLM leaves it EMPTY/INVALID 4 times → `TrackerPrepError("task_tracker_prep_failed")`,
  `prompt_llm` called 4 times, calls 2–4 use the returned `session_id` and the feedback prompt;
  tracker bytes identical to the start (use CRLF content to prove byte-exactness).
- LLM changes nothing → counted as a failed round, not a guard trip.
- LLM changes `src/x.py` → fails after that call, message names `src/x.py`, no further round, tracker restored.
- `LLMTimeoutError` from `prompt_llm` → `TrackerPrepError` with the starting reason, one call only, tracker restored.
- `prompt_llm` raising `SystemExit` after the tracker was modified → `SystemExit` propagates, tracker bytes restored.
- `core`: `TrackerPrepError("general", ...)` → `fail("general", stage="Task tracker validation", ...)`.
  Existing tests patching `prepare_task_tracker` with `return_value=False` switch to
  `side_effect=TrackerPrepError("task_tracker_prep_failed", ...)`; `return_value=True` may stay.
- Jenkins: `classify("Stage: Task tracker validation\n", patterns)` contains `MC-IMPL-TRACKER-INVALID`.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5 only:
> write the tests first, then rewrite `prepare_task_tracker` around `TrackerPrepError`,
> `_llm_rounds`, the changed-files guard and the `try/finally` byte restore; wire `core.py`;
> remove `has_implementation_tasks`; add the Jenkins signature. INVALID trackers fail
> directly in this step (repair comes in step 6). Run pylint, pytest (`-n auto`, unit markers) and mypy.
