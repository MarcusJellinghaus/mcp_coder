# Step 6: Changed-files guard, byte restore, LLM feedback rounds

See `pr_info/steps/summary.md` (§2 row 3, §3 guard/restore/LLM errors of issue #1093).
Builds on step 5's `TrackerPrepError`. An INVALID tracker still fails directly (repair: step 7).

## WHERE
- `src/mcp_coder/workflows/implement/task_tracker_prep.py`
- `src/mcp_coder/workflows/implement/constants.py`
- Tests: `tests/workflows/implement/test_task_tracker_prep.py`; new
  `tests/workflows/implement/test_task_tracker_repair.py` (restore / guard / SystemExit cases)

## WHAT
```python
# constants.py
MAX_TRACKER_FEEDBACK_ROUNDS = 3   # after the initial population call
MAX_TRACKER_REPAIR_ATTEMPTS = 3   # restructure calls (used in step 7)

# task_tracker_prep.py
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
  Step 5's inline `len(all_changed) != 1` check and the empty-response check are removed.
- `_population_errors`: classify; POPULATED → `[]`; EMPTY → `["pr_info/TASK_TRACKER.md: no '### Step N:' sections were added"]`; INVALID → violations.
- `_populate`: `_llm_rounds(ask, project_dir, get_prompt(..., "Task Tracker Update Prompt"), _population_errors, 1 + MAX_TRACKER_FEEDBACK_ROUNDS, reason)`.
  Replaces step 5's single population call.
- Commit: `commit_paths("TASK_TRACKER.md with implementation steps and PR tasks updated", [tracker], project_dir)`
  replaces `commit_all_changes`; failure → `TrackerPrepError(reason, ...)`.
- Restore: wrap everything after classification in `try/finally` that writes the original bytes back unless done.

## ALGORITHM
```
(after step 5's steps-dir check and classification)
reason = "general" if INVALID else "task_tracker_prep_failed"; original = tracker.read_bytes(); done = False
try: INVALID -> raise TrackerPrepError(reason, describe_violations(v))  # step 7 replaces with repair
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
Unchanged from step 5.

## Tests (write first)
- EMPTY + LLM populates correctly → `commit_paths` called with only the tracker.
- EMPTY + LLM leaves it EMPTY/INVALID 4 times → `TrackerPrepError("task_tracker_prep_failed")`,
  `prompt_llm` called 4 times, calls 2–4 use the returned `session_id` and the feedback prompt;
  tracker bytes identical to the start (use CRLF content to prove byte-exactness).
- LLM fixes the tracker on the second call → success after 2 calls.
- LLM changes nothing → counted as a failed round, not a guard trip.
- LLM changes `src/x.py` → fails after that call, message names `src/x.py`, no further round, tracker restored.
- `LLMTimeoutError` from `prompt_llm` → `TrackerPrepError` with the starting reason, one call only, tracker restored.
- `prompt_llm` raising `SystemExit` after the tracker was modified → `SystemExit` propagates, tracker bytes restored.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement step 6 only:
> write the tests first, then add `_ask_llm` (session wiring), the `_other_changed_files`
> guard, `_llm_rounds` with feedback prompts, `_populate`, the `try/finally` byte restore and
> `commit_paths`. INVALID trackers still fail directly (repair comes in step 7). Run pylint,
> pytest (`-n auto`, unit markers) and mypy.
