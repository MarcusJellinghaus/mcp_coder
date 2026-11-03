# Step 7: Repair — reset to template or LLM restructure

See `pr_info/steps/summary.md` (§3 Repair of issue #1093).

## WHERE
- `src/mcp_coder/workflows/implement/task_tracker_prep.py`
- Tests: `tests/workflows/implement/test_task_tracker_repair.py`

## WHAT
```python
def _repair(ask, project_dir: Path, original: str, violations: list[str]) -> None: ...
```
Replaces the direct INVALID `raise` inside step 6's `try/finally` in `prepare_task_tracker`.
`original` = the original bytes decoded as UTF-8.

## HOW
- Uses `has_completed_tasks`, `check_restructure`, `describe_violations`, `EXPECTED_FORMAT`
  (steps 2/3), `TASK_TRACKER_TEMPLATE`, `write_lf_text` (`mcp_coder.utils.text_io`), `_populate`
  and `_llm_rounds` (step 6), and "Task Tracker Restructure Prompt" (step 4).
- `reason` is always `"general"` here.
- No restore between restructure attempts; the step 6 `finally` restores once at the end.
- The final restructure failure message always carries the original line-numbered violations:
  the `TrackerPrepError` from `_llm_rounds` is re-raised with
  `describe_violations(violations)` appended.

## ALGORITHM
```
if not has_completed_tasks(original):
    if not any((project_dir / PR_INFO_DIR / "steps").glob("step_*.md")): raise TrackerPrepError("general", "cannot reset ...: no pr_info/steps/step_*.md\n" + describe_violations(violations))
    write_lf_text(tracker, TASK_TRACKER_TEMPLATE); _populate(ask, project_dir, "general")
else:
    prompt = restructure template with [violations] / [expected_format] filled
    try: _llm_rounds(ask, project_dir, prompt, lambda c: check_restructure(original, c), MAX_TRACKER_REPAIR_ATTEMPTS, "general")
    except TrackerPrepError as exc:
        raise TrackerPrepError("general", f"{exc}\nOriginal violations:\n{describe_violations(violations)}") from exc
```
Every restructure check compares with `original`, never with the previous attempt.

## DATA
None returned; failures raise `TrackerPrepError("general", ...)`, success falls through to the commit.

## Tests (write first)
- Flat #1146-shaped tracker (no `[x]`), steps dir with `step_1.md`: the tracker is reset to
  the template before the first LLM call (assert file content in the `prompt_llm` side effect);
  LLM populates → commit; success.
- Same, but only `summary.md` in `pr_info/steps/` → `TrackerPrepError("general")`, no LLM call, tracker restored.
- Reset + population still invalid after 4 calls → reason `general`, tracker bytes restored.
- `## Step N` tracker with an `[x]` → restructure path (no reset); LLM writes a valid
  restructure → POPULATED, the `[x]` line is present, commit.
- Restructure that toggles / deletes / rewords a checkbox, or adds `[ ]` under a step with
  `[x]` → failed attempt; 3 failed attempts → `TrackerPrepError("general")`, `prompt_llm`
  called 3 times with one session, tracker restored, and the message contains the original
  violations' line numbers (assert e.g. `"pr_info/TASK_TRACKER.md line 26"` for the fixture).
- Restructure in which the LLM changes nothing → failed attempt.
- Guard trip during restructure → immediate failure naming the other file.
- `SystemExit` during restructure → tracker bytes restored.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`. Implement step 7 only:
> write the tests first, then add `_repair` (reset when the file has no `[x]` outside
> `## Instructions for LLM`, else LLM restructure checked by `check_restructure`, with the
> original violations appended to the final failure message) and call it for INVALID
> trackers in `prepare_task_tracker`. Run pylint, pytest (`-n auto`, unit markers) and mypy.
